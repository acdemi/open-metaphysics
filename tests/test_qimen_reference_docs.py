"""Qimen Reference Domain 文档测试 (Phase 5.7 + 5.9B 自主 Sprint 更新).

验证 reference/qimen/ 域:
- 目录结构完整 (README / runtime_vs_reference / concepts/*)
- 文档链接可解析 (link check) / 外部引用存在
- 流派差异记录完整 (S1-S8)
- 实现层: domain.py 存在 (5.9B 起, 依契约实现; 验收见 test_reference_qimen.py)
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QIMEN_REF = ROOT / "reference" / "qimen"
CONCEPTS = QIMEN_REF / "concepts"

EXPECTED_CONCEPTS = [
    "board.md",
    "dundun_ju.md",
    "plates.md",
    "schools.md",
    "stars_doors_gods.md",
    "void_central.md",
    "zhifu_zhishi.md",
]

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _all_markdown_files() -> list[Path]:
    return sorted(QIMEN_REF.rglob("*.md"))


def test_domain_structure_exists():
    assert QIMEN_REF.is_dir(), f"missing: {QIMEN_REF}"
    assert (QIMEN_REF / "README.md").is_file()
    assert (QIMEN_REF / "runtime_vs_reference.md").is_file()
    assert CONCEPTS.is_dir()
    actual = sorted(p.name for p in CONCEPTS.glob("*.md"))
    assert actual == EXPECTED_CONCEPTS, f"concepts mismatch: {actual}"


def test_implementation_layer_present():
    """5.9B 起: 契约实现存在于 reference/qimen/domain.py (依契约 v1.0.0)."""
    domain = QIMEN_REF / "domain.py"
    assert domain.is_file(), "reference/qimen/domain.py missing (contract implementation)"
    text = domain.read_text(encoding="utf-8")
    assert "QIMEN_BEHAVIOR_CONTRACT.md" in text, "domain.py must reference the frozen contract"
    assert "def compute(" in text, "domain.py must expose compute() entry"


def test_markdown_links_resolve():
    """Link check: 所有相对 Markdown 链接目标存在 (文件或目录)。"""
    broken: list[str] = []
    for doc in _all_markdown_files():
        text = doc.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#")[0].strip()
            if not target:
                continue
            resolved = (doc.parent / target).resolve()
            if not resolved.exists():
                broken.append(f"{doc.relative_to(ROOT)} -> {target}")
    assert not broken, "broken links:\n" + "\n".join(broken)


def test_external_references_exist():
    """文档引用的关键外部产物存在 (契约 / 规范向量 / 相关文档)。"""
    for doc in _all_markdown_files():
        text = doc.read_text(encoding="utf-8")
        for m in re.finditer(r"`(\.\./\.\./[^`]+)`|`(docs/[^`]+)`|`(src/[^`]+)`", text):
            ref = next(g for g in m.groups() if g)
            if ref.endswith((".md", ".json")) and not (ROOT / ref).exists():
                raise AssertionError(f"{doc.relative_to(ROOT)}: missing reference {ref}")


def test_readme_defines_boundary():
    readme = (QIMEN_REF / "README.md").read_text(encoding="utf-8")
    for keyword in ("边界", "契约", "normative", "domain.py", "*.py"):
        assert keyword in readme, f"README missing boundary keyword: {keyword}"


def test_school_differences_recorded():
    """流派差异 S1-S8 全部显式记录 (强制约束 5)。"""
    schools = (CONCEPTS / "schools.md").read_text(encoding="utf-8")
    for sid in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"):
        assert f"| {sid} " in schools, f"school difference {sid} not recorded"
    assert "规范选择" in schools and "替代流派" in schools


def test_contract_and_vectors_referenced():
    """README 必须引用冻结契约与规范向量 (对齐基线)。"""
    readme = (QIMEN_REF / "README.md").read_text(encoding="utf-8")
    assert "QIMEN_BEHAVIOR_CONTRACT.md" in readme
    assert "golden_vectors.json" in readme
