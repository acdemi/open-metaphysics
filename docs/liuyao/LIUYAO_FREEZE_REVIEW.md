# Liuyao Freeze Review

> **Sprint**: 六爻契约冻结审查（Phase B → Contract Freeze）
> **日期**: 2026-10-23
> **结论**: **PASS / FROZEN** —— 契约 v1.0.0 + 25 向量 + Reference 认证
> 已于 2026-10-23 经 `ACP-LIUYAO-001` 批准
> **性质**: 评审与冻结记录；不修改其他域
> **输入**: `LIUYAO_BEHAVIOR_CONTRACT.md` / `golden_vectors.json` /
> `reference/liuyao/` / `LIUYAO_REFERENCE_AUDIT.md`

---

## 1. 审查范围

| 工件 | 当前状态 | 本次审查 |
|------|----------|----------|
| 规则清单 | Frozen（LY-01~LY-11） | 定义完整性、与实现一致 |
| 行为契约 | Frozen v1.0.0（30 条） | 条款可测试性、边界显式化 |
| Golden Vectors | Frozen（25） | 覆盖充分性、可复现性、拒绝路径 |
| Reference | v0.1.0 自包含，Certified | 条款实现、表一致、独立性 |
| 等价证明 | 21/21 + 40/40 + 边界 | 是否足以支撑冻结 |
| 状态文档 | Integration Ready（25 / 30 条） | 已升级 |

**不在范围**：新增六爻断法（六冲/六合/应期计算等）、解释层扩写、Consensus
接入、其他域契约、`docs/specification/`、`reference/contracts/`。

---

## 2. 规则审查

| Rule | 定义对齐 | 实现对齐 | 向量覆盖 | 测试覆盖 | 判定 |
|------|----------|----------|----------|----------|------|
| LY-01 起卦 | YES | `LiuyaoEngine._casts` | `LY_norm_006` + 4 seed 等价 | `test_seed_replay_is_deterministic` | FROZEN |
| LY-02 本卦 | YES | `_yao` | `LY_norm_001~010` | 全部 golden | FROZEN |
| LY-03 变卦 | YES | `_changed_yao` | `LY_norm_003/004/005/007` | `test_all_nine_is_qian_changing_to_kun` | FROZEN |
| LY-04 互卦 | YES | `mutual_casts` | `LY_edge_005` | `test_mutual_hexagram_present` | FROZEN |
| LY-05 卦序 | YES | `hexagram_from_lines` | 全部 normal | golden + 等价 | FROZEN |
| LY-06 八宫 | YES | `BA_GONG` | 全部 normal（`palace`） | golden | FROZEN |
| LY-07 世应 | YES | `SHI_BY_POS` | 全部 normal | golden | FROZEN |
| LY-08 纳甲 | YES | `NAJIA_STEM` + `najia_branch` | `LY_norm_001`（乾）等 | `test_qian_najia_and_liuqin_canonical` | FROZEN |
| LY-09 六亲 | YES | `wuxing_relation` | 全部 normal | 同上 | FROZEN |
| LY-10 六神 | YES | 日干 + 23:00 换日 | `LY_edge_006` / `LY_bound_001~003` | 换日等价 ×5 | FROZEN |
| LY-11 用神 | YES | 关键词表 | `LY_norm_008/009` + `LY_edge_001~004` | `test_yong_shen_keyword_selection` | FROZEN |

**判定规则**：四列均为 YES 才进入 FROZEN —— 11/11 满足。

---

## 3. 向量充分性

### 3.1 数量与类别

| 类别 | 数量 | 覆盖重点 |
|------|------|----------|
| normal | 10 | 全阳/全阴/全动/全静/混合/seed/单动/用神 |
| edge | 6 | 无问题/多关键词/出行/考试/互卦/22:00 |
| boundary | 5 | 23:00、23:30、00:00、闰日、跨年 |
| invalid | 4 | 5 爻、cast=5、cast=10、tz-naive |
| **合计** | **25** | 21 条合法路径 + 4 条拒绝路径 |

### 3.2 冻结规则覆盖

| 冻结规则 | 边界向量 | 判定 |
|----------|----------|------|
| LY-01 起卦 | `LY_norm_006`（seed）+ 4 个额外 seed 等价 | PASS |
| LY-02/03 本变卦 | `LY_norm_001~005/007` + `LY_norm_010`（无动） | PASS |
| LY-04 互卦 | `LY_edge_005` | PASS |
| LY-05/06/07 卦序/宫/世应 | 全部 normal（自动断言 chart 字段） | PASS |
| LY-08/09 纳甲/六亲 | 全部 normal + 乾卦 canonical 单测 | PASS |
| LY-10 六神 | `LY_edge_006` + `LY_bound_001~005` | PASS |
| LY-11 用神 | `LY_norm_008/009` + `LY_edge_001~004` | PASS |
| LC-003 时区 | `LY_inv_004`（新增） | PASS |

**判定**：25 向量达到候选冻结最低覆盖；新增 `LY_inv_004` 关闭了 tz-naive
拒绝路径的盲区。向量仍由生产引擎生成，故其角色是**回归锁定**，不是独立
正确性证明；独立证明由 Reference 等价测试承担。

---

## 4. 边界与 Deferred 裁定

| 项 | 裁定 | 理由 |
|----|------|------|
| LC-D04 自动 seed | **冻结外** | 受 `PYTHONHASHSEED` 影响，跨进程不可复现；冻结仅覆盖显式 `casts`/`seed` |
| LC-D04 Reference 行为 | 拒绝无 `casts`/`seed` | 与冻结范围一致；测试显式锁定该边界 |
| tz-naive `born_at` | 拒绝 | 与生产 `AgentInput` 一致；冻结前修正 Reference |
| 互卦 `cast_value` | 保留源 cast | 生产与 Reference 已有行为；契约补写，不改代码 |
| LC-042 信封 | Agent 层验证 | Reference 返回 chart body；等价比较限定 chart |
| 23:00 换日 | 冻结 | 与 BaZi 契约的 23:00 政策一致；边界向量覆盖 |
| 卦名/爻辞/断语 | 不进入计算契约 | 属知识/解释层，禁止在本契约新增 |

**结论**：无阻塞性 Deferred；自动 seed 的排除是本次冻结的显式条件之一。

---

## 5. 参考实现与等价

| 检查 | 结果 |
|------|------|
| Reference 源码独立性 | PASS（3 文件无 `openmetaphysics` 导入） |
| Reference 表与生产表 | PASS（六类表 + 2 个历法函数） |
| 21 条合法向量 | PASS（逐字节） |
| 40 条生成输入 | PASS（`SEED=20260916`） |
| 4 个显式 seed | PASS（0/1/12345/2^31-1） |
| 5 个换日边界 | PASS（22:59/23:00/23:30/00:00/跨年） |
| 4 条拒绝路径 | PASS（长度/值域/时区） |
| Reference 副作用 | 无网络、无存储、无 LLM、无解释生成 |

详见 `LIUYAO_REFERENCE_AUDIT.md` 与 `LIUYAO_REFERENCE_CERTIFICATION.md`。

---

## 6. 架构边界

本 Sprint 的改动限定在 Liuyao 契约冻结面：

- `docs/liuyao/LIUYAO_BEHAVIOR_CONTRACT.md`
- `docs/liuyao/golden_vectors.json`
- `docs/liuyao/LIUYAO_REFERENCE_AUDIT.md`（新增）
- `docs/liuyao/LIUYAO_FREEZE_REVIEW.md`（新增）
- `docs/liuyao/LIUYAO_REFERENCE_CERTIFICATION.md`（新增）
- `docs/liuyao/LIUYAO_INTEGRATION_READINESS.md`（新增）
- `reference/liuyao/domain.py`（仅 LC-003 拒绝路径）
- `reference/tests/test_liuyao_equivalence.py`（新增边界断言）
- `tests/test_liuyao_golden_vectors.py`（25/4 计数）
- `tools/gen_liuyao_golden_vectors.py`（新增 `LY_inv_004`）
- `docs/governance/ACP/ACP-LIUYAO-001.md`（IMPLEMENTED）
- `.gitattributes`（Liuyao 作用域 LF，保证 SHA-256 可复算）
- 状态文档刷新（见 Integration Readiness §5）

**零触碰**：`docs/specification/`、`reference/contracts/`、其他域算法/契约/
向量、`src/openmetaphysics/agents/liuyao.py`、共享 `core/engines.py`。

---

## 7. 风险登记

| Risk | 等级 | 处置 |
|------|------|------|
| 自动 seed 被误认为冻结行为 | Medium | 契约 LC-004/LC-D04 + 边界测试显式排除 |
| 向量由生产生成，存在“自证”风险 | Medium | Reference 独立实现 + 21/21 等价 + 40 生成输入 |
| 23:00 换日与部分流派不一致 | Low | 已冻结为项目政策；变更须 ACP |
| 用神关键词表覆盖有限 | Low | 契约只冻结“表驱动选择”，不承诺语义完整性 |
| 生产内部死代码/猴子补丁 | Low | 不影响可观测行为；单独清理，不在冻结面内改算法 |
| 状态文档提前写 Frozen | Low | 已按 ACP 批准升级；无提前宣称 |

---

## 8. 审查结论

**PASS / FROZEN**：11/11 规则、30/30 条款、25 向量、21/21 等价、40/40
生成输入、4 条拒绝路径全部满足冻结条件；无阻塞性 Deferred。

**已完成**：

1. `ACP-LIUYAO-001` 于 2026-10-23 获人工批准（D1-D4）。
2. 契约/向量 metadata 已从 `candidate` 改为 `frozen`。
3. `CAPABILITY_STATUS.md` 等状态指针已升级为 `Integration Ready`。
4. 全量验证见 `LIUYAO_INTEGRATION_READINESS.md` §4。

**剩余**：按 H7 取得合并授权；合并前不 push origin。Liuyao 当前准确状态为
**Integration Ready（Certified Frozen Capability）**。
