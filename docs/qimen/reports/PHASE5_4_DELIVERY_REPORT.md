# Phase 5.4 — Qimen Freeze Candidate Review 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Architecture Governance / Domain Review
> **状态**: 已交付 — 结论 **PASS WITH CONDITIONS**

---

## 1. Executive Summary

正式评审完成：**结论 PASS WITH CONDITIONS**。12 条冻结规则内部一致、无矛盾（含跨规则链条 D4→D5→D6 / D4→D7→D9 / D5/D7→D12 / D1→D3 / D13→D1 逐盘验证）；D2/D14 均分类为**非阻塞技术债**；21 向量达到候选冻结最低覆盖；契约化前置条件已列明。本 Sprint 零代码改动（评审仅产物 1 文档 + 2 处数据核验修正）。评审文档：`docs/qimen/QIMEN_FREEZE_REVIEW.md`。

## 2. Frozen Rule Review Table

| Rule | Status | Risk |
|------|--------|------|
| D1 阴阳遁 | PASS | Low（双边界测试+6 边界向量） |
| D3 局数公式 | PASS | Low（ju 1-9 全覆） |
| D4 地盘 | PASS | Low（18 组不变量） |
| D5 值符 | PASS | Low（经典例核验） |
| D6 天盘 | PASS | Low（几何唯一解；零转盘 3 向量） |
| D7 值使 | PASS | Medium（流派注记；经典例+回归双锁） |
| D8 天禽转盘 | PASS | Low-Med（Schema 约束唯一可行） |
| D9 八门 | PASS | Low |
| D10 八神 | PASS | Medium（阴遁逆布派注记） |
| D11 空亡 | PASS | Low（干支规则独立验证） |
| D12 中宫寄坤二 | PASS | Medium（主流；已裁定；4 中宫向量） |
| D13 真太阳时 | PASS | Low（复用 core.solar_time） |

每条含 定义/实现位置/测试/向量覆盖/风险 五要素（文档 §2.1 全表）；跨规则一致性 6 链条全部核验通过（§2.2）。

## 3. Deferred Decision Review

| 项 | 分类 | 判定 |
|----|------|------|
| **D2 三元** | **B. Non-blocking technical debt** | 日号近似为"已文档化近似"（非隐藏不一致）；不阻止运行时冻结候选，仅阻止 ju/三元字段升级 normative；替换需 ACP+21 向量迁移（成本已量化）——维持 Deferred |
| **D14 晚子时** | **B. Non-blocking technical debt** | 行为确定（不换日）；0 向量覆盖（23-24 点无输入）；冻结任一派均无依据——维持 Deferred，契约 Sprint 补向量后裁定 |

## 4. Golden Vector Assessment

| 维度 | Status |
|------|--------|
| 局数 | PASS（阳 1-9 全覆；阴 {2,3,5,7} ≥3） |
| 阴阳遁 | PASS（阳 12 / 阴 9；双遁转盘+零转盘） |
| 节气 | PASS with gap（12/24；阳遁序列 8/12、阴遁 4/12；含冬至/夏至/立春切换对；缺口走相同代码路径） |
| 时辰 | PASS（时支 子丑寅卯辰巳午 7 支；未申酉戌亥及 23-24 点未覆盖=与 D14 一致） |
| 真太阳时 | PASS（21/21 走真太阳路径；跨辰向量 ×1；无坐标回退仅测试覆盖） |
| 中宫 | PASS（值符落中宫 ×3、值使落中宫 ×2、旬首在中宫取门 ×1） |

**判定：达到 Candidate Freeze 最低覆盖**。

## 5. Freeze Decision

# **PASS WITH CONDITIONS**

- ✅ 冻结规则 12/12 一致（§2.2 链条验证）
- ✅ 向量覆盖达标（§4）
- ✅ Deferred 非阻塞（§3）
- ✅ 稳定性：404 tests / 21 向量 / 100 随机盘 / 确定性 JSON
- ✅ 架构边界无越界
- **Conditions**：① 契约 Sprint 显式声明 D2 日号近似的规范地位（或裁定真拆补法）；② 补 春分/秋分/晚子时 3 向量；③ 未来变更仍走 ACP+版本递增+向量迁移

## 6. Future Roadmap

1. **Qimen Behavior Contract Sprint**（推荐下一步）：12 规则→条款、21 向量→fixtures、补 3 向量、D2 声明
2. **Reference Runtime Qimen Domain Sprint**：依契约移植（纯 Python 无 sxtwl 依赖，可移植性已验证）
3. 功能扩展（格局/用神，新授权）
4. Consensus integration（契约冻结后）

## Governance Compliance

```
qimen 算法 未修改 ✅   Frozen Rules 未修改 ✅   D2 未解决 ✅
Behavior Contract 未创建 ✅   reference/ 未修改 ✅   Schema 未修改 ✅
proto/ specification/ contracts/ 未修改 ✅   其他 Agent 未修改 ✅
解释层/RAG/Consensus 未添加 ✅   RuntimeAdapter 不需要（无跨语言实现）✅
```

评审中修正的自身错误：Z_yin2 值符星为天柱（非天禽）；天禽为值符星的向量是 Y_ju5（旬首戊@中宫）—— 已按数据文件核实并更新评审文档。
