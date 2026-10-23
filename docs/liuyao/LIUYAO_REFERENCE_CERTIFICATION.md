# Liuyao Reference Certification

> **Status**: **CERTIFIED**（2026-10-23，ACP-LIUYAO-001 D3 批准）
> **Date**: 2026-10-23
> **Contract**: `liuyao:behavior:v1.0.0`（Frozen）
> **Reference**: `liuyao:reference:v0.1.0`（`reference/liuyao/`）
> **Production**: `src/openmetaphysics/agents/liuyao.py`（engine 0.1.0）
> **Vectors**: `docs/liuyao/golden_vectors.json`（25，Frozen）

---

## 1. 认证结论

**PASS**：Reference 在契约冻结范围内与生产实现行为一致，且保持源码独立。
认证覆盖 **21 条合法 golden vectors + 40 条生成输入 + 4 个显式 seed +
5 个换日边界 + 4 条拒绝路径**；未发现未解释的行为差异。

本认证已于 **2026-10-23** 随 `ACP-LIUYAO-001` 批准生效。契约与向量均已标记
**Frozen**；对外状态为 **Certified / Integration Ready**。

---

## 2. 认证范围

| 项 | 内容 |
|----|------|
| 契约条款 | LC-001~LC-052 范围内实际 30 条 |
| 规则 | LY-01~LY-11 |
| 输入域 | 显式 6 个 cast；显式 seed 起卦；时区感知 `born_at` |
| 输出域 | `LiuyaoChart` chart body（14 字段） |
| 排除 | 自动 seed（无 casts/seed）；Agent 输出信封；解释文本；知识/RAG |
| 比较方式 | `json.dumps(..., sort_keys=True)` 后逐字节比较 |
| 随机性 | 固定输入/固定 seed；无 `random()` 未播种路径 |

---

## 3. 证据

### 3.1 Golden Vectors

- 文件：`docs/liuyao/golden_vectors.json`
- 总数：25（normal 10 / edge 6 / boundary 5 / invalid 4）
- 合法可执行：21
- 拒绝路径：4
- 生产回归：`tests/test_liuyao_golden_vectors.py`（6 例）
- 判定：21/21 合法向量逐字节一致；4/4 拒绝行为一致。

### 3.2 生成输入

- 测试：`reference/tests/test_liuyao_equivalence.py::test_generated_inputs_are_equivalent`
- 参数：`SEED=20260916`，`GENERATED=40`
- 输入：随机 cast、2023~2025 年、0~23 时、UTC / Asia/Shanghai、六类问题
- 结果：**40/40 byte-identical**

### 3.3 显式 seed

- 测试：`test_seeded_casting_path_is_equivalent`
- seeds：`0, 1, 12345, 2**31 - 1`
- 结果：4/4 一致

### 3.4 换日边界

- 测试：`test_day_rollover_boundary_is_equivalent`
- 输入：`22:59 / 23:00 / 23:30 / 00:00 / 跨年 23:30`
- 结果：5/5 一致

### 3.5 拒绝路径

| 输入 | 生产 | Reference | 判定 |
|------|------|-----------|------|
| 5 个 cast | `ValueError` | `ValueError` | PASS |
| cast=5 | `ValueError` | `ValueError` | PASS |
| cast=10 | `ValueError` | `ValueError` | PASS |
| tz-naive `born_at` | `ValueError` | `ValueError`（冻结前修正） | PASS |
| 无 casts/seed | 自动 seed（契约外） | `ValueError`（契约外） | PASS（边界已声明） |

### 3.6 表一致性

`test_reference_tables_match_production_tables` 守卫：

- `HEXAGRAMS`、`TRIGRAMS`
- `HEAVENLY_STEMS`、`EARTHLY_BRANCHES`
- `BRANCH_ELEMENT`、`WUXING_SHENG`、`WUXING_KE`
- `sexagenary_day_index`、`julian_day_number`

结果：全部一致。

### 3.7 源码独立性

`test_reference_source_is_independent_of_src` 对以下文件做正则扫描：

- `reference/liuyao/domain.py`
- `reference/liuyao/tables.py`
- `reference/liuyao/astronomy.py`

结果：无 `from openmetaphysics` / `import openmetaphysics`。

---

## 4. 复现命令

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest `
  tests\test_liuyao.py `
  tests\test_liuyao_golden_vectors.py `
  reference\tests\test_liuyao_equivalence.py -q
```

期望：**20 passed**（6 + 6 + 8）。

全量回归与 lint 见 `LIUYAO_INTEGRATION_READINESS.md` §4：2026-10-23 实测
**1024 passed + 2 skipped**（1026 collected），ruff 与 knowledge validate 均通过。

---

## 5. 工件摘要

| 工件 | 版本/数量 | 角色 |
|------|-----------|------|
| `LIUYAO_BEHAVIOR_CONTRACT.md` | v1.0.0 / 30 clauses | 行为标准 |
| `golden_vectors.json` | 25（frozen） | 回归锁定 |
| `reference/liuyao/` | 0.1.0 | 独立实现 |
| `reference/tests/test_liuyao_equivalence.py` | 8 tests | 等价证明 |
| `tests/test_liuyao.py` | 6 tests | 生产单测 |
| `tests/test_liuyao_golden_vectors.py` | 6 tests | 生产向量回归 |

**Frozen digests（2026-10-23 实测，SHA-256）**：

| 工件 | SHA-256 |
|------|---------|
| `docs/liuyao/LIUYAO_BEHAVIOR_CONTRACT.md` | `8ec3320997279e6fbf978f590834e6d34947359ecf13b5aae65dcb8fae9f1206` |
| `docs/liuyao/golden_vectors.json` | `144a485c5e2881f5b1648c0de864ce401e4159492a53911d21edd44e4c1059a7` |
| `docs/liuyao/LIUYAO_RULE_INVENTORY.md` | `f157047a0b671d78067301028667e4c24c834f7b932d486688d793b1e2acf2b4` |
| `reference/liuyao/domain.py` | `db174a5d0e7bb1ef511a5cae61e9b705af49f9e093f16c3326e1c1d0b94d9976` |
| `reference/liuyao/tables.py` | `a4b30c881e77150482977be147b8233590f7945895a7a3134a0e145f9b6edbf4` |
| `reference/liuyao/astronomy.py` | `357de8b9f480d1dad14101a9099b3e87c6116cd933c60cb1d1a2048dbb8396ea` |
| `src/openmetaphysics/agents/liuyao.py` | `e4a07a66f97f16416ac0a0d9854eb77a24321d0e3e729ea81b42919df0f8ac4e` |
| `tests/test_liuyao_golden_vectors.py` | `f865bd48879a574a8d7df0090a348de2affbbd301a0b3f50968cbac19649fb27` |
| `reference/tests/test_liuyao_equivalence.py` | `42658de540cf86f4179cc96b935f37639e69440ef2cb42cc46355f249fe2a667` |

> 上述摘要基于 **LF 规范工作区**；`.gitattributes` 已将 `docs/liuyao/**`、
> `reference/liuyao/**`、`src/openmetaphysics/agents/liuyao.py` 与 Liuyao
> 测试/生成器固定为 `text eol=lf`。批准时已复核这些摘要；后续任何变更须
> 新 ACP 并重新登记。

---

## 6. 认证边界

- **不认证**自动 seed 的跨进程确定性；该路径明确排除。
- **不认证** Agent 信封字段（`agent` / `request_id` / `trace` 等）；由生产
  `LiuyaoOutput` 与 API 测试覆盖。
- **不认证**解释文本、RAG 命中、知识条目正确性；这些由 P2.3/P2.4 的独立
  测试治理。
- **不认证**六爻断法/吉凶/应期等未实现能力；契约 §7 已列为范围外。
- 认证以固定输入/固定 seed 为前提；未播种 `random()` 不在范围内。

---

## 7. 签署

| 角色 | 结论 | 日期 |
|------|------|------|
| Reference audit | PASS | 2026-10-23 |
| Freeze review | PASS | 2026-10-23 |
| ACP approval | **APPROVED（D1-D4）** | 2026-10-23 |
| Certification effective | **EFFECTIVE** | 2026-10-23 |
