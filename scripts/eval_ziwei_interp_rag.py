#!/usr/bin/env python3
"""P2.4.3-F retrieval validation against the existing in-memory RAG stack.

Read-only with respect to the project: imports the production retriever and the
frozen corpus, indexes EXTERNAL interpretation chunks in memory only, and never
writes into the corpus, the retriever defaults or any knowledge artifact.

Two indexing variants are measured:
  raw   -- one chunk per topic, verbatim (median 6.4 KB) : naive mapping
  sect  -- one chunk per 【section】 / 1200-char window     : realistic chunking
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from openmetaphysics.rag.corpus import load_all_chunks  # noqa: E402
from openmetaphysics.rag.retriever import InMemoryRetriever, KnowledgeChunk  # noqa: E402

CORE_TOPICS = ("overview", "personality")
COND_MARKERS = ("庙", "陷", "四化", "三方四正", "若", "宜", "忌", "旺")
POS = ("吉", "旺", "贵", "福", "利", "成", "荣", "富")
NEG = ("凶", "破", "忌", "灾", "不利", "煞", "刑", "克", "败")
WINDOW = 1200
OVERLAP = 100

QUERIES = [
    {"id": "S1", "q": "巨门 口舌 是非 暗曜", "kind": "star", "star": "巨门"},
    {"id": "S2", "q": "紫微 帝座 尊贵 中天", "kind": "star", "star": "紫微"},
    {"id": "S3", "q": "太阳 光明 贵显 中天", "kind": "star", "star": "太阳"},
    {"id": "S4", "q": "武曲 财星 刚毅 北斗", "kind": "star", "star": "武曲"},
    {"id": "S5", "q": "天机 变动 智谋 南斗", "kind": "star", "star": "天机"},
    {"id": "P1", "q": "命宫 主星 格局 定盘", "kind": "kw", "must": ["命宫"]},
    {"id": "P2", "q": "兄弟宫 手足 相处", "kind": "kw", "must": ["兄弟"]},
    {"id": "P3", "q": "夫妻宫 婚姻 感情", "kind": "kw", "must": ["夫妻", "感情"]},
    {"id": "P4", "q": "财帛宫 求财 收入", "kind": "kw", "must": ["财"]},
    {"id": "P5", "q": "官禄宫 事业 工作", "kind": "kw", "must": ["事业", "工作"]},
    {"id": "H1", "q": "化禄 财源 得利", "kind": "kw", "must": ["化禄"]},
    {"id": "H2", "q": "化权 权力 掌权", "kind": "kw", "must": ["化权"]},
    {"id": "H3", "q": "化科 科名 名声", "kind": "kw", "must": ["化科"]},
    {"id": "H4", "q": "化忌 阻碍 纠结", "kind": "kw", "must": ["化忌"]},
    {"id": "H5", "q": "四化 飞星 生年", "kind": "kw", "must": ["四化"]},
    {"id": "G1", "q": "三方四正 会照", "kind": "kw", "must": ["三方四正"]},
    {"id": "G2", "q": "庙旺 落陷 星力强弱", "kind": "kw", "must": ["庙"]},
    {
        "id": "G3",
        "q": "擎羊 陀罗 火铃 煞星",
        "kind": "kw",
        "must": ["擎羊", "陀罗", "火星", "铃星", "煞"],
    },
    {"id": "G4", "q": "天罗地网 辰戌", "kind": "kw", "must": ["辰", "戌"]},
    {
        "id": "G5",
        "q": "机月同梁 格局",
        "kind": "kw",
        "must": ["机月同梁", "天机", "太阴", "天同", "天梁"],
    },
]


def split_sections(text: str) -> list[str]:
    parts = re.split(r"(?=\*\*【)", text)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) <= WINDOW * 1.25:
            out.append(p)
            continue
        step = WINDOW - OVERLAP
        for i in range(0, len(p), step):
            piece = p[i : i + WINDOW]
            if len(piece) >= 120:
                out.append(piece)
            if i + WINDOW >= len(p):
                break
    return out or [text[:WINDOW]]


def build(records, variant: str) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for meta, rec in records:
        source = "ziwei-interp-v4.0-13d · " + meta["member"] + "#L" + str(meta["line"])
        base_tags = ["external_interpretation", "ziwei", "main_star:" + str(meta.get("ms"))]
        for topic, text in (rec.get("c") or {}).items():
            text = str(text)
            if variant == "raw":
                pieces = [(text, "")]
            else:
                pieces = [(s, f":s{i}") for i, s in enumerate(split_sections(text))]
            for body, suffix in pieces:
                chunks.append(
                    KnowledgeChunk(
                        id="ext:ziwei_interp:" + str(meta["k"]) + ":" + topic + suffix,
                        text=body,
                        source=source,
                        tags=base_tags + ["topic:" + topic],
                    )
                )
    return chunks


def polarity(text: str) -> int:
    return sum(text.count(w) for w in POS) - sum(text.count(w) for w in NEG)


def relevant(chunk: KnowledgeChunk, query: dict) -> bool:
    if not chunk.id.startswith("ext:"):
        return False
    if query["kind"] == "star":
        star = [t for t in chunk.tags if t.startswith("main_star:")][0].split(":", 1)[1]
        topic = [t for t in chunk.tags if t.startswith("topic:")][0].split(":", 1)[1]
        return star == query["star"] and topic in CORE_TOPICS
    return any(m in chunk.text for m in query["must"])


def evaluate(retriever, queries, k, tag) -> dict:
    rows = []
    for q in queries:
        hits = retriever.retrieve(q["q"], k=k)
        ext = [h for h in hits if h.id.startswith("ext:")]
        rows.append(
            {
                "id": q["id"],
                "kind": q["kind"],
                "recall": any(relevant(h, q) for h in ext),
                "top1": bool(ext) and relevant(ext[0], q),
                "top1Id": ext[0].id if ext else None,
                "traceable": ext[0].source.startswith("ziwei-interp-v4.0-13d · ") if ext else None,
                "condMarkers": sum(1 for m in COND_MARKERS if ext and m in ext[0].text)
                if ext
                else 0,
                "kbTop1": bool(hits) and hits[0].id.startswith("kb:"),
                "top1CharLen": len(ext[0].text) if ext else 0,
                "top1Snippet": (ext[0].text[:80] if ext else ""),
            }
        )

    def rate(sub, key):
        vals = [r[key] for r in sub if r[key] is not None]
        return round(sum(1 for v in vals if v) / len(vals), 3) if vals else None

    return {
        "variant": tag,
        "recallAtK": rate(rows, "recall"),
        "top1Relevance": rate(rows, "top1"),
        "traceability": rate(rows, "traceable"),
        "condMarkersAvg": round(sum(r["condMarkers"] for r in rows) / len(rows), 2),
        "top1CharLenAvg": round(sum(r["top1CharLen"] for r in rows) / len(rows), 1),
        "starRecall": rate([r for r in rows if r["kind"] == "star"], "recall"),
        "starTop1": rate([r for r in rows if r["kind"] == "star"], "top1"),
        "kwRecall": rate([r for r in rows if r["kind"] == "kw"], "recall"),
        "kwTop1": rate([r for r in rows if r["kind"] == "kw"], "top1"),
        "kbTop1Rate": round(sum(1 for r in rows if r["kbTop1"]) / len(rows), 3),
        "rows": rows,
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--records", type=int, default=150)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args(argv)

    base = Path(args.data)
    provs = [
        json.loads(line)
        for line in (base / "samples/provenance.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    recs = [
        json.loads(line)
        for line in (base / "samples/samples.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    pairs = list(zip(provs, recs, strict=False))[: args.records]

    kb = load_all_chunks(REPO / "knowledge" / "ziwei_corpus.json", include_evidence=True)

    out: dict = {"recordsIndexed": len(pairs), "kbChunks": len(kb), "k": args.k, "variants": {}}
    variants = {}
    for variant in ("raw", "sect"):
        ext = build(pairs, variant)
        variants[variant] = ext
        res = evaluate(InMemoryRetriever(ext), QUERIES, args.k, variant)
        res["chunks"] = len(ext)
        res["avgChunkChars"] = round(sum(len(c.text) for c in ext) / len(ext), 1)
        out["variants"][variant] = res

    mixed = InMemoryRetriever(kb + variants["sect"])
    mix = evaluate(mixed, QUERIES, args.k, "mixed")
    out["mixed"] = {k2: v for k2, v in mix.items() if k2 != "rows"}
    out["mixed"]["kbChunks"] = len(kb)

    # conflict detection on the star queries
    conflicts = []
    for r in out["variants"]["sect"]["rows"]:
        if r["kind"] != "star":
            continue
        star = next(q["star"] for q in QUERIES if q["id"] == r["id"])
        kbchunk = next((c for c in kb if star in c.text and c.id.startswith("kn:")), None)
        if kbchunk is None:
            continue
        kp = polarity(kbchunk.text)
        ep = polarity(r["top1Snippet"])
        conflicts.append(
            {
                "query": r["id"],
                "star": star,
                "kbPolarity": kp,
                "extPolarity": ep,
                "signConflict": (kp * ep < 0),
                "kbSource": kbchunk.source,
            }
        )
    out["conflicts"] = conflicts

    # 10 explain cases: one per distinct main star
    cases, seen = [], set()
    for meta, _rec in pairs:
        ms = meta.get("ms")
        if not ms or ms in seen:
            continue
        seen.add(ms)
        hits = mixed.retrieve(ms + " 命宫 主星", k=args.k)
        kb_hits = [h for h in hits if h.id.startswith("kb:")]
        ext_hits = [h for h in hits if h.id.startswith("ext:")]
        cases.append(
            {
                "k": meta["k"],
                "mainStar": ms,
                "contextTop1": hits[0].id if hits else None,
                "kbInContext": len(kb_hits),
                "extInContext": len(ext_hits),
                "extTraceable": [h.source for h in ext_hits],
                "kbSource": kb_hits[0].source if kb_hits else None,
                "polarityConflict": bool(
                    kb_hits
                    and ext_hits
                    and polarity(kb_hits[0].text) * polarity(ext_hits[0].text) < 0
                ),
                "condMarkers": sum(1 for m in COND_MARKERS if ext_hits and m in ext_hits[0].text),
            }
        )
        if len(cases) >= 10:
            break
    out["explainCases"] = cases
    out["queryDetail"] = [
        {k2: v for k2, v in r.items() if k2 != "top1Snippet"}
        for r in out["variants"]["sect"]["rows"]
    ]
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
