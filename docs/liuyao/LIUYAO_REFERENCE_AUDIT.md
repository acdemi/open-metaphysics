# Liuyao Reference Audit

> **Status**: audit PASS — FROZEN（2026-10-23，ACP-LIUYAO-001）
> **Date**: 2026-10-23
> **Contract**: `docs/liuyao/LIUYAO_BEHAVIOR_CONTRACT.md` v1.0.0（Frozen）
> **Reference**: `reference/liuyao/` v0.1.0
> **Production**: `src/openmetaphysics/agents/liuyao.py`
> **Vectors**: `docs/liuyao/golden_vectors.json`（25）
> **Scope**: LY-01~LY-11、LC-001~LC-052 范围（实际 30 条）的 Reference 行为一致性

本审计回答一个问题：**Reference 是否逐条实现了契约，且没有引入生产实现之外的
行为？** 结论为 **PASS**；审计中发现的 1 处 Reference 偏差已在冻结前修正，
3 处边界已在契约中显式化或声明为冻结外。

---

## 1. 审计方法

| 层 | 方法 | 证据 |
|----|------|------|
| 静态 | Reference 源码逐条对照契约；确认无 `openmetaphysics` 导入、无网络/存储/LLM 依赖 | `reference/liuyao/*.py` |
| 行为 | 生产 ↔ Reference 同输入逐字节比较 | `reference/tests/test_liuyao_equivalence.py` |
| 向量 | 25 条 golden vectors 的合法/拒绝路径 | `tests/test_liuyao_golden_vectors.py` |
| 表 | Reference 表与生产表一致性守卫 | 同名测试中的 `test_reference_tables_match_production_tables` |
| 边界 | 23:00 换日、seed 起卦、时区、互卦、信封 | 单元 + 等价 + 静态审计 |

---

## 2. 规则审计（LY-01~LY-11）

| Rule | 契约位置 | Reference 实现 | 生产实现 | 判定 |
|------|----------|----------------|----------|------|
| LY-01 起卦获取 | LC-004 | `compute()` + `_three_coin_casts()` | `LiuyaoEngine._casts()` | PASS（显式 seed/casts） |
| LY-02 本卦爻性 | LC-010~012 | `_yao()` | `_yao()` | PASS |
| LY-03 变卦翻爻 | LC-013~014 | `_changed_yao()` | `_changed_yao()` | PASS |
| LY-04 互卦 | LC-015~016 | `compute()` 的 `mutual_casts` | 同 | PASS |
| LY-05 文王卦序 | LC-020 | `hexagram_from_lines()` | `core.models.hexagram_from_lines()` | PASS |
| LY-06 京房八宫 | LC-021 | `BA_GONG` + `_PALACE_OF` | 同表 | PASS |
| LY-07 世应 | LC-023~024 | `SHI_BY_POS` + `(shi+2)%6+1` | 同 | PASS |
| LY-08 纳甲 | LC-030 | `NAJIA_STEM` + `najia_branch()` | 同表 | PASS |
| LY-09 六亲 | LC-031/034 | `wuxing_relation()` + `LIU_QIN_BY_RELATION` | 同 | PASS |
| LY-10 六神 | LC-032~033 | `sexagenary_day_index()` + 23:00 rollover | 同 | PASS |
| LY-11 用神 | LC-040~041 | `select_yong_shen()` | `_select_yong_shen()` | PASS |

---

## 3. 条款审计（30/30）

| Clause | 要求（摘要） | Reference 证据 | 判定 |
|--------|--------------|----------------|------|
| LC-001 | `casts` 必须 6 个 | `len(casts) != 6` 抛错 | PASS |
| LC-002 | cast ∈ {6,7,8,9} | 值域检查 | PASS |
| LC-003 | `born_at` 必须时区感知 | 冻结前修正为 `ValueError`；见 §5.1 | PASS |
| LC-004 | 显式 `seed` 确定性起卦 | `random.Random(seed)`；4 个 seed 等价 | PASS |
| LC-010 | `original` 恒 6 爻 | `_yao` 逐爻构造 | PASS |
| LC-011 | 6/8 阴、7/9 阳 | `is_yin = cast in (6, 8)` | PASS |
| LC-012 | 6/9 为动爻 | `is_changing = cast in (6, 9)` | PASS |
| LC-013 | 变卦动爻翻转且稳定 | `_changed_yao`：9→8、6→7 | PASS |
| LC-014 | 无动爻时 `changed_hexagram=null` | `any(is_changing)` 分支 | PASS |
| LC-015 | 互卦 2/3/4 + 3/4/5，恒稳定；`cast_value` 保留源 cast | `mutual_casts` + `force_stable=True` | PASS |
| LC-016 | `mutual_hexagram` 恒存在 | 无条件计算 | PASS |
| LC-020 | 文王卦序 1..64 | `hexagram_from_lines` | PASS |
| LC-021 | 京房八宫 | `_PALACE_OF` | PASS |
| LC-022 | 宫位五行 | `_TRIGRAM_ELEMENT[palace]` | PASS |
| LC-023 | 世爻 1..6 | `SHI_BY_POS[palace_pos]` | PASS |
| LC-024 | 应爻 = 世 + 2（模 6） | `((shi + 2) % 6) + 1` | PASS |
| LC-025 | 六亲按宫位五行关系 | `wuxing_relation` + 表 | PASS |
| LC-030 | 每爻纳甲 | `NAJIA_STEM` + `najia_branch` | PASS |
| LC-031 | 每爻六亲 | `LIU_QIN_BY_RELATION` | PASS |
| LC-032 | 每爻六神 | `SIX_SPIRITS` | PASS |
| LC-033 | 23:00 日界换日 | `born.hour >= 23` 分支 | PASS |
| LC-034 | 六亲不随六神变化 | 两字段独立构造 | PASS |
| LC-040 | 无问题 → 世爻用神 | `select_yong_shen(None)` | PASS |
| LC-041 | 关键词命中 → 对应六亲 | `YONG_SHEN_RULES` 顺序匹配 | PASS |
| LC-042 | 输出信封字段 | Reference 返回 chart body；`agent` 由生产 `LiuyaoOutput` 添加 | PASS（层边界；见 §5.4） |
| LC-043 | 同输入同输出 | 等价测试 + 生产复现测试 | PASS |
| LC-044 | 输出字段集固定 | Reference dict 键与 `LiuyaoChart` 一致 | PASS |
| LC-050 | 计算层无 LLM | 静态扫描无 LLM/API 导入 | PASS |
| LC-051 | 无网络/数据库/存储副作 | 静态扫描无网络/DB 导入；仅 `random.Random` | PASS |
| LC-052 | 解释层不得改写计算结果 | Reference 不产生解释文本；生产解释层只读 chart | PASS |

---

## 4. 独立性与副作用

- `reference/liuyao/domain.py`、`tables.py`、`astronomy.py` 仅导入标准库与
  `reference.liuyao.*`；`test_reference_source_is_independent_of_src` 持续守卫。
- Reference 不读取文件、不访问网络、不写数据库；唯一随机源是
  `random.Random(seed)`，仅在 LC-004 显式 seed 路径使用。
- Reference 不生成解释、建议、吉凶判断或 LLM 文本；输出仅为 chart body。
- Reference 表为冻结副本；`test_reference_tables_match_production_tables`
  守卫 `HEXAGRAMS` / `TRIGRAMS` / 干支 / 五行 / 历法函数与生产表一致。

---

## 5. 审计发现与处置

### 5.1 tz-naive `born_at`（已修正）

| 项 | 内容 |
|----|------|
| 发现 | 生产 `AgentInput` 拒绝 tz-naive；Reference 原先静默按 UTC 处理 |
| 影响 | LC-003 在 Reference 侧不成立；等价测试未覆盖该拒绝路径 |
| 处置 | Reference 改为抛 `ValueError("born_at must be timezone-aware")`；新增 `LY_inv_004` 与等价拒绝断言 |
| 状态 | **关闭**（冻结前修正；生产算法零改动） |

### 5.2 自动 seed（冻结外）

| 项 | 内容 |
|----|------|
| 发现 | 生产在 `casts` 与 `seed` 均缺省时自动 seed；`derive_seed` 使用 `hash()`，受 `PYTHONHASHSEED` 影响，跨进程不可复现 |
| 影响 | 不能作为冻结行为；否则违反 LC-043 的确定性承诺 |
| 处置 | 契约 LC-004/LC-D04 明确：自动 seed **不属于冻结契约**；Reference 拒绝该输入；等价测试新增边界断言，防止误把该路径纳入等价 |
| 状态 | **已声明**（非阻塞；未来若纳入须 ACP） |

### 5.3 互卦 `cast_value`（已澄清）

| 项 | 内容 |
|----|------|
| 发现 | 契约 LC-015 只写“全部稳定”，未写 `cast_value` 是否归一化 |
| 实现 | 生产与 Reference 均保留源 cast（6/9），仅 `is_changing=false` |
| 处置 | LC-015 补充该语义；无代码变更 |
| 状态 | **关闭** |

### 5.4 输出信封（层边界）

| 项 | 内容 |
|----|------|
| 发现 | LC-042 描述 Agent 输出信封；Reference `compute()` 返回 chart body |
| 处置 | 审计按层拆分：LC-042 由生产 `LiuyaoOutput` / Agent 层验证；等价比较针对 chart body |
| 状态 | **已声明**（不视为 Reference 缺口） |

### 5.5 文档漂移（已修正）

| 项 | 内容 |
|----|------|
| 发现 | `LIUYAO_RULE_INVENTORY.md`、`reference/liuyao/README.md` 原写 24 向量；`CAPABILITY_STATUS.md` 把 candidate 写成 Integration Ready；`SCHEMAS.md §3.4` 的自动 seed 描述与实现不符 |
| 处置 | 本 Sprint 已修正为 25 向量 / Integration Ready / `derive_seed(request_id, client_nonce)`；见 `LIUYAO_INTEGRATION_READINESS.md` §5 |
| 状态 | **关闭（文档层）** |

---

## 6. 审计结论

**PASS**：30/30 条款有 Reference 证据；LY-01~LY-11 全部覆盖；25 条向量中
21 条合法路径逐字节等价、4 条拒绝路径行为一致；40/40 生成输入、4 个 seed、
5 个换日边界均等价。唯一实质偏差（tz-naive）已在冻结前修正；自动 seed 已
明确排除在冻结契约之外。

**生效**：本审计随 `ACP-LIUYAO-001` 于 2026-10-23 批准生效；Reference v0.1.0
为 **Certified**，契约与向量为 **Frozen**。
