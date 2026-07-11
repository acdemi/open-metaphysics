# 风险分析

> 状态：设计 v1 (2026-07-11)

## 风险矩阵

| 编号 | 风险 | 可能性 | 影响 | 风险等级 | 缓解措施 |
|------|------|--------|------|---------|---------|
| R01 | 规则冲突爆炸：大量规则互相冲突，retain_all 导致结论过多 | 中 | 中 | 🟡 中 | 设置单领域最大结论数上限（如 5）；低置信度结论折叠为「其他」 |
| R02 | 知识节点 attributes 键集合无约束导致数据不一致 | 中 | 高 | 🔴 高 | 为每种 node_type 定义 attributes schema 约束；实现阶段用 discriminated union |
| R03 | 规则条件 field 路径指向不存在的排盘字段 | 中 | 中 | 🟡 中 | 规则注册时校验 field 路径合法性；运行时 missing field 视为条件不满足 |
| R04 | Pattern 定义不足导致跨体系共识无法触发 | 高 | 中 | 🟡 中 | Phase 7 优先实现高频格局（伤官佩印、紫府同宫等 20+ Pattern） |
| R05 | Evidence 聚合后置信度计算公式不合理 | 中 | 高 | 🔴 高 | 公式需在 Phase 7 用黄金向量校准；预留 formula 可配置点 |
| R06 | 知识层多流派解释权重主观性 | 高 | 中 | 🟡 中 | 权重初始值来自经典文献权威性；支持配置覆盖；文档记录权重来源 |
| R07 | 规则版本迁移导致旧结果不可重放 | 低 | 高 | 🟡 中 | 规则 ID 含版本后缀；旧版本保留；superseded_by 链可追溯 |
| R08 | 性能：大量规则评估 + 知识查询拖慢响应 | 中 | 中 | 🟡 中 | 规则按 scope 预过滤；知识查询加缓存；Pattern 匹配可并行 |
| R09 | 设计与实现偏差：Phase 7 实现时发现 Schema 不可行 | 中 | 高 | 🔴 高 | Phase 6 评审需含实现可行性确认；Schema 导出 JSON Schema 验证 |
| R10 | 六体系知识差异大，统一 Schema 无法覆盖 | 中 | 中 | 🟡 中 | 多态 attributes 设计预留扩展；新体系只需新增 node_type + 属性键集合 |

## 风险详情

### R02：attributes 键集合无约束（🔴 高风险）

**问题**：知识节点采用 `attributes: dict[str, Any]` 多态设计，
若不在实现阶段约束每种 node_type 的键集合，会导致数据不一致。

**缓解**：
- Phase 7 实现时，为每种 node_type 定义 `attributes` 的 JSON Schema 子模式。
- 使用 Pydantic discriminated union 或 validator 校验。
- 单元测试覆盖全部 20 种 node_type 的 attributes 合法性。

### R05：置信度公式不合理（🔴 高风险）

**问题**：Evidence-Based Consensus 的置信度计算涉及证据权重、来源可信度、跨体系增强因子。
若公式不合理，多结论排序将失去意义。

**缓解**：
- Phase 7 实现后，用 10+ 黄金向量案例校准公式参数。
- 公式参数（如 cross_system_bonus 范围）设为可配置。
- 预留 ADR 记录公式变更。

### R09：设计与实现偏差（🔴 高风险）

**问题**：Phase 6 为纯设计，Phase 7 实现时可能发现某些 Schema 在 Python/Pydantic 中不可行。

**缓解**：
- Phase 6 的 Pydantic 模型定义已确保语法合法（可直接实例化）。
- JSON Schema 可通过 `model_json_schema()` 导出验证。
- Phase 6 评审需包含「实现可行性」确认项。

## 非风险项（已确认安全）

- **确定性引擎不受影响**：规则层和知识层均在引擎 `calculate()` 之后运行，不修改排盘数字。
- **现有测试不受影响**：Phase 6 不修改 `src/` 任何代码。
- **隐私不受影响**：知识层和规则层均为本地数据，不涉及网络。
