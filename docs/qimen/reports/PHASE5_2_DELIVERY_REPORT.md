# Phase 5.2 — Qimen Rule Decision 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Architecture Decision + Algorithm Stabilization
> **状态**: 已交付（后续演进见 Phase 5.3/5.4 存档）

---

## 1. Executive Summary

完成 D1-D14 规则裁定：**12 项冻结（Freeze）、2 项延迟冻结（Deferred）、0 项替换**。零代码变更（决策 Sprint 不触算法）。新增 `docs/qimen/QIMEN_RULE_DECISION.md`（裁定记录）与 2 个稳定化测试。400 tests passing，无阻塞。

## 2. Rule Decision Summary

| ID | 决策项 | Decision | Status | 理由 |
|----|--------|----------|--------|------|
| D1 | 阴阳遁 | 保留 | **Freeze** | 通行规则，测试锁定 |
| D2 | 三元划分 | 保留 | **Deferred** | 日号近似非主流；替换全向量失效，需 ACP |
| D3 | 局数公式 | 保留 | **Freeze** | 公式稳定（偏移源依赖 D2，已注明） |
| D4 | 地盘 | 保留 | **Freeze** | 经典规则，无分歧 |
| D5 | 值符 | 保留 | **Freeze** | 经典例核验 |
| D6 | 天盘 | 保留 | **Freeze** | 转盘法几何唯一自洽解 |
| D7 | 值使 | 保留 | **Freeze** | 休门逐时经典例 + 戊辰时寄坤回归用例双锁 |
| D8 | 天禽 | 保留（不寄宫） | **Freeze** | Schema 约束 9宫↔9星 一一对应 |
| D9 | 八门 | 保留 | **Freeze** | 通行转盘法 |
| D10 | 八神 | 保留（顺布） | **Freeze** | 主流；阴遁逆布为少数派（注明） |
| D11 | 空亡 | 保留 | **Freeze** | 干支规则独立可验证 |
| D12 | 中宫寄宫 | **明确选择寄坤二** | **Freeze** | 转盘法主流；寄艮八为罕见派 |
| D13 | 真太阳时 | 保留 | **Freeze** | 复用既有模块；跨辰行为已验证 |
| D14 | 晚子时 | 保留（不换日） | **Deferred** | 两派并存，零向量覆盖，零成本开放 |

## 3. Frozen / Deferred Rules

- **Frozen (12)**：F1(D1) F2(D3) F3(D4) F4(D5) F5(D6) F6(D7) F7(D8) F8(D9) F9(D10) F10(D11) F11(D12) F12(D13) — 每条对应 `test_frozen_rule_regression` 中可观察断言，变更须 ACP + 向量迁移 + 版本递增
- **Deferred (2)**：D2 三元（解锁条件：用户/Reference Runtime 裁定 + ACP 批准向量迁移）；D14 晚子时（行为仍以当前实现为工程基线）

## 4. Modified Files

| 文件 | 变更 |
|------|------|
| `docs/qimen/QIMEN_RULE_DECISION.md` | **新增** — 裁定记录（Summary/Frozen/Deferred/Migration/Extension Boundary/Vector 分类） |
| `docs/qimen/QIMEN_ALGORITHM_ASSUMPTIONS.md` | 追加 Phase 5.2 裁定交叉引用 |
| `tests/test_qimen.py` | +2 测试（冻结规则回归、Golden 元数据校验） |
| `src/openmetaphysics/agents/qimen.py` | 无变更（本 Sprint 正确零代码） |

## 5. Golden Vector Status

| 向量 | 分类 | 冻结依赖 |
|------|------|----------|
| G1 阳遁转盘 | candidate normative（升级标注） | F1-F12 |
| G2 阴遁零转 | candidate normative（升级标注） | F1-F12 |
| G3 中宫寄宫 | candidate normative（升级标注） | F1-F12（含 F11 寄坤二，已裁定） |

三向量 `ju`/`triple_offset`/`day_of_month` 依赖 D2 → 整体维持 candidate，未升 full normative。**未创建 Behavior Contract**（遵约束）。`GOLDEN_METADATA` 表锁定 engine_version 0.3.0 + method/placement + 假设文档出处，`test_golden_metadata_validation` 强制输入/版本/假设一致。

## 6. Test Results

```
ruff check            ✅ All checks passed
ruff format --check   ✅ 68 files already formatted
pytest                ✅ 400 passed (398 + 2 new)
qimen tests           ✅ 29/29
```

## 7. Remaining Risks

| 风险 | 等级 | 缓解 |
|------|------|------|
| D2 日号三元 vs 主流拆补法结果差异 | **高** | 已显式 Deferred，迁移路径与影响在 Decision §4 记录 |
| D10 阴遁逆布派 | 中 | 冻结声明 + 变更即 ACP |
| D7 值使步数流派 | 中 | 经典例 + 回归用例双重锁定 |
| D14 晚子时 | 低 | Deferred，开放 |
| Golden 未覆盖 1~4 局/晚子时 | 低 | 5.2 建议补齐 |

## 8. Recommended Next Sprint

- **Qimen 参考向量扩充**：补 1~4 局、晚子时、真太阳时跨辰边界输入（为契约化铺路）
- **Reference Runtime 奇门域 Sprint**：若启动，以本裁定 F1-F12 为输入约束对齐
- 后续功能 Sprint（需新授权）：格局判断 / 用神 / Consensus integration

## Governance Compliance

```
reference/ 未修改 ✅   docs/specification/ 未修改 ✅
Behavior Contracts 未创建/未修改 ✅   Schema 未修改 ✅
其他 Agent 未修改 ✅   RuntimeAdapter 未实现 ✅
无格局判断/吉凶/用神/RAG/Consensus ✅   qimen.py 零代码变更 ✅
```
