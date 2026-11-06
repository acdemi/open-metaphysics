#!/usr/bin/env python3
"""P2.4.3-A/B read-only inspector for the Ziwei interpretation archive (TAR).

Contract (see reports/P2.4_DATA_ARCHIVE_AUDIT.md):
  * the archive is opened read-only and never modified;
  * nothing is extracted to disk -- members are read by offset;
  * sampling stops after --limit records, so a 742 MB member is never
    decompressed end to end;
  * the JSON report goes to stdout, so the caller decides whether it lands.

Usage:
  python scripts/inspect_ziwei_tar.py E:/download/ziwei-interp-v4-all.tar --limit 50
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import tarfile

CHUNK = 1 << 22


def sha256_stream(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def enumerate_members(tf: tarfile.TarFile) -> list[dict]:
    out = []
    for m in tf.getmembers():
        out.append(
            {
                "name": m.name,
                "type": m.type.decode("latin1") if isinstance(m.type, bytes) else str(m.type),
                "size": m.size,
                "offset": m.offset_data,
                "mode": oct(m.mode & 0o7777),
                "mtime": m.mtime,
            }
        )
    return out


def raw_member_bytes(path: str, offset: int, size: int) -> bytes:
    with open(path, "rb") as fh:
        fh.seek(offset)
        return fh.read(size)


def verify_sums(path: str, tf: tarfile.TarFile, members: list[dict]) -> dict:
    by_name = {m["name"]: m for m in members}
    handle = tf.extractfile("SHA256SUMS.txt")
    if handle is None:
        return {"available": False}
    declared = {}
    for line in handle.read().decode("utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            declared[parts[1]] = parts[0]
    ok, bad = 0, []
    for name, digest in declared.items():
        m = by_name.get(name)
        if m is None:
            bad.append("missing:" + name)
            continue
        actual = hashlib.sha256(raw_member_bytes(path, m["offset"], m["size"])).hexdigest()
        if actual == digest:
            ok += 1
        else:
            bad.append("mismatch:" + name)
    return {"available": True, "declared": len(declared), "ok": ok, "bad": bad[:10]}


def sample_records(path: str, member: dict, limit: int) -> dict:
    """Decompress only until limit JSONL records have been parsed."""
    try:
        import zstandard
    except ImportError:
        return {"ok": False, "reason": "zstandard module unavailable"}
    blob = raw_member_bytes(path, member["offset"], member["size"])
    dctx = zstandard.ZstdDecompressor()
    records, bad = [], 0
    fields: dict[str, str] = {}
    with dctx.stream_reader(io.BytesIO(blob)) as reader:
        text = io.TextIOWrapper(reader, encoding="utf-8")
        for line in text:
            if len(records) >= limit:
                break
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            for key, value in rec.items():
                fields.setdefault(key, type(value).__name__)
            records.append(rec)
    return {
        "ok": True,
        "member": member["name"],
        "records": len(records),
        "badLines": bad,
        "fieldTypes": fields,
        "firstKey": records[0].get("k") if records else None,
        "lastKey": records[-1].get("k") if records else None,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--member", default=None)
    ap.add_argument("--skip-verify", action="store_true")
    args = ap.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    report: dict = {"archive": {"path": args.archive}}
    report["archive"]["sizeBytes"] = os.path.getsize(args.archive)
    report["archive"]["sha256"] = sha256_stream(args.archive)

    with tarfile.open(args.archive, "r:") as tf:
        members = enumerate_members(tf)
        names = [m["name"] for m in members]
        report["archive"]["members"] = len(members)
        report["archive"]["typeflags"] = sorted({m["type"] for m in members})
        report["archive"]["extensions"] = sorted({os.path.splitext(m["name"])[1] for m in members})
        report["archive"]["pathTraversal"] = [
            n for n in names if n.startswith("/") or ".." in n.split("/")
        ]
        report["archive"]["duplicates"] = len(names) - len(set(names))
        if not args.skip_verify:
            report["integrity"] = verify_sums(args.archive, tf, members)

        target = args.member
        if target is None:
            candidates = [m for m in members if m["name"].endswith(".jsonl.zst")]
            target = candidates[0]["name"] if candidates else None
        if target:
            member = next(m for m in members if m["name"] == target)
            report["sample"] = sample_records(args.archive, member, args.limit)

        if "MANIFEST.json" in names:
            mh = tf.extractfile("MANIFEST.json")
            if mh is not None:
                manifest = json.loads(mh.read().decode("utf-8"))
                report["datasetManifest"] = {
                    k: manifest.get(k)
                    for k in (
                        "dataset",
                        "releaseTag",
                        "generatedAt",
                        "contentVersion",
                        "engineCommit",
                        "years",
                        "totalCharts",
                        "totalReadings",
                        "rawBytes",
                        "zstBytes",
                        "license",
                        "decompress",
                    )
                }
                report["datasetManifest"]["filesListed"] = len(manifest.get("files", []))

    json.dump(report, sys.stdout, ensure_ascii=False, indent=1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
