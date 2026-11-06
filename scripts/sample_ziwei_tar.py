#!/usr/bin/env python3
"""P2.4.3-D deterministic bounded sampler for the Ziwei interpretation archive.

Guarantees:
  * the archive is opened read-only; nothing is extracted to disk;
  * at most --per-year records per year member, hard-capped by --max-records;
  * samples.jsonl keeps every record byte-identical to the archive line;
  * provenance (member, 1-based line, sha256 of the raw line) lands beside it;
  * CC BY 4.0 attribution + the Ni Haixia exclusion travel with the sample.

Usage:
  python scripts/sample_ziwei_tar.py E:/download/ziwei-interp-v4-all.tar \
      --out E:/OpenMetaphysics-Data/external/ziwei-doushu --per-year 12
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import tarfile

import zstandard

ATTRIBUTION = (
    "本项目使用了 紫微斗数开源解读数据集 v4.0（674,976 张命盘 × 13 维）\n"
    "来源：https://github.com/Renhuai123/ziwei-doushu\n"
    "作者：王多鱼AI"
)


def tar_index(path: str) -> tuple[dict, list[dict]]:
    with tarfile.open(path, "r:") as tf:
        manifest = {}
        handle = tf.extractfile("MANIFEST.json")
        if handle is not None:
            manifest = json.loads(handle.read().decode("utf-8"))
        members = [
            {"name": m.name, "offset": m.offset_data, "size": m.size}
            for m in tf.getmembers()
            if m.name.endswith(".jsonl.zst")
        ]
    return manifest, members


def pick_indices(total: int, k: int) -> list[int]:
    """Odd-stride walk so parity-linked fields (gender) are not aliased away."""
    if total <= k:
        return list(range(total))
    step = total // k
    if step % 2 == 0:
        step += 1
    return sorted({(i * step) % total for i in range(k)})


def decompress_member(path: str, offset: int, size: int) -> bytes:
    with open(path, "rb") as fh:
        fh.seek(offset)
        blob = fh.read(size)
    dctx = zstandard.ZstdDecompressor()
    with dctx.stream_reader(io.BytesIO(blob)) as reader:
        return reader.read()


def line_offsets(data: bytes) -> list[tuple[int, int]]:
    """Byte range of every newline-terminated record, in file order."""
    out: list[tuple[int, int]] = []
    start = 0
    n = len(data)
    while start < n:
        nl = data.find(b"\n", start)
        if nl == -1:
            break
        out.append((start, nl))
        start = nl + 1
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-year", type=int, default=12)
    ap.add_argument("--max-records", type=int, default=1000)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    for sub in ("metadata", "samples", "reports"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)
    samples_path = os.path.join(args.out, "samples", "samples.jsonl")
    prov_path = os.path.join(args.out, "samples", "provenance.jsonl")
    if os.path.exists(samples_path) and not args.force:
        print("REFUSED: samples.jsonl already exists (use --force to overwrite)", file=sys.stderr)
        return 2

    manifest, members = tar_index(args.archive)
    charts = {str(f["year"]): f["charts"] for f in manifest.get("files", [])}

    lines_out: list[bytes] = []
    prov: list[dict] = []
    anomalies: list[str] = []
    per_year_counts: dict[str, int] = {}

    for m in members:
        year = m["name"].split("-")[1].split(".")[0]
        expected = charts.get(year)
        data = decompress_member(args.archive, m["offset"], m["size"])
        spans = line_offsets(data)
        observed = len(spans)
        if expected is not None and observed != expected:
            anomalies.append(f"{m['name']}: manifest charts={expected} observed={observed}")
        indices = pick_indices(observed, args.per_year)
        per_year_counts[year] = len(indices)
        for idx in indices:
            start, stop = spans[idx]
            raw = data[start:stop]
            if len(lines_out) >= args.max_records:
                break
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                anomalies.append(f"{m['name']}#L{idx + 1}: unparsable line skipped")
                continue
            lines_out.append(raw)
            prov.append(
                {
                    "index": len(lines_out),
                    "member": m["name"],
                    "line": idx + 1,
                    "lineCount": observed,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "bytes": len(raw),
                    "k": rec.get("k"),
                    "y": rec.get("y"),
                    "m": rec.get("m"),
                    "d": rec.get("d"),
                    "h": rec.get("h"),
                    "g": rec.get("g"),
                    "ms": rec.get("ms"),
                    "topics": sorted((rec.get("c") or {}).keys()),
                }
            )
        del data

    payload = b"\n".join(lines_out) + b"\n"
    with open(samples_path, "wb") as fh:
        fh.write(payload)
    with open(prov_path, "w", encoding="utf-8") as fh:
        for p in prov:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")

    archive_sha = hashlib.sha256()
    with open(args.archive, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            archive_sha.update(block)

    out_manifest = {
        "schemaVersion": "p2.4.3-sample-1",
        "generatedBy": "scripts/sample_ziwei_tar.py",
        "dataset": {
            "name": manifest.get("dataset"),
            "releaseTag": manifest.get("releaseTag"),
            "contentVersion": manifest.get("contentVersion"),
            "generatedAt": manifest.get("generatedAt"),
            "years": manifest.get("years"),
            "totalCharts": manifest.get("totalCharts"),
            "totalReadings": manifest.get("totalReadings"),
            "topics": manifest.get("topics"),
        },
        "archive": {
            "path": args.archive,
            "sizeBytes": os.path.getsize(args.archive),
            "sha256": archive_sha.hexdigest(),
            "members": len(members),
        },
        "license": {
            "spdx": "CC-BY-4.0",
            "attribution": ATTRIBUTION,
            "attributionSource": "upstream DATASET-LICENSE, verbatim copy in open-metaphysics/reports/P2.4_DATASET-LICENSE.verbatim.md",
            "exclusions": (
                "倪海厦《天纪》原话著作权归原权利人，不在数据集授权范围内；"
                "如单独成批使用须按 docs/tianji-ziwei/LICENSE.md（CC BY-NC-SA 4.0）处理。"
            ),
            "constraints": [
                "attribution must ship with any redistribution or derived artifact",
                "never extract the Ni Haixia quotations into a separate batch or quote-only index",
                "quotations may not be re-licensed to third parties",
            ],
        },
        "sampling": {
            "method": "deterministic even-stride over each year member's record sequence",
            "perYear": args.per_year,
            "maxRecords": args.max_records,
            "recordCount": len(lines_out),
            "recordsPerYear": per_year_counts,
            "rule": "per year file: step = total // perYear, forced odd, then indices = sorted({(i * step) % total}) -- odd stride avoids aliasing on parity-linked fields such as gender",
            "byteFaithful": True,
        },
        "files": {
            "samples": {
                "path": "samples/samples.jsonl",
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "lines": len(lines_out),
            },
            "provenance": {"path": "samples/provenance.jsonl", "lines": len(prov)},
        },
        "quality": {
            "nullMainStar": sum(1 for p in prov if not p["ms"]),
            "distinctMainStar": len({p["ms"] for p in prov if p["ms"]}),
            "recordsWithEmptyTopics": sum(1 for p in prov if not p["topics"]),
            "genders": {
                g: sum(1 for p in prov if p["g"] == g)
                for g in sorted({p["g"] for p in prov if p["g"]})
            },
            "hoursCovered": len({p["h"] for p in prov if p["h"] is not None}),
        },
        "anomalies": anomalies[:50],
        "notes": [
            "samples.jsonl is NOT ground truth and NOT a rule base; it is external interpretation text kept for evaluation only.",
            "each samples.jsonl line N corresponds to provenance.jsonl line N (1-based).",
            "the readings are machine-generated from the v4.0 phrase library; recorded non-falsifiable prose is not evidence.",
        ],
    }
    with open(os.path.join(args.out, "metadata", "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(out_manifest, fh, ensure_ascii=False, indent=1)

    print(
        json.dumps(
            {
                "records": len(lines_out),
                "bytes": len(payload),
                "samplesSha256": out_manifest["files"]["samples"]["sha256"],
                "archiveSha256": out_manifest["archive"]["sha256"],
                "anomalies": anomalies[:5],
                "years": len(per_year_counts),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
