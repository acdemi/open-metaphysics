# 单元测试计划

> 状态：设计 v1 (2026-07-11)
> 本文件仅规划测试用例，不实现测试代码。实现阶段按此计划编写。

## 1. Rule 层测试

### 1.1 Rule Schema 验证

| 测试用例 | 验证内容 |
|---------|---------|
| test_rule_valid_full | 完整合法 Rule 对象可通过 Pydantic 验证 |
| test_rule_invalid_id_format | ID 不匹配 `rule:{system}:{slug}:v{n}` 格式时拒绝 |
| test_rule_empty_conditions | conditions 为空列表时拒绝（min_length=1） |
| test_rule_empty_results | results 为空列表时拒绝（min_length=1） |
| test_rule_priority_bounds | priority 超出 [0,100] 时拒绝 |
| test_rule_confidence_bounds | confidence 超出 [0,1] 时拒绝 |
| test_rule_version_format | version 不匹配语义版本格式时拒绝 |

### 1.2 RuleCondition 操作符

| 测试用例 | 验证内容 |
|---------|---------|
| test_condition_equals | equals 操作符正确匹配 |
| test_condition_contains | contains 在列表字段中正确匹配 |
| test_condition_in | in 操作符正确匹配集合 |
| test_condition_greater_than | 数值大于比较 |
| test_condition_matches | 正则匹配 |
| test_condition_negate | negate=true 时取反逻辑 |
| test_condition_exists | exists/not_exists 逻辑 |

### 1.3 RuleEngine 评估

| 测试用例 | 验证内容 |
|---------|---------|
| test_engine_all_conditions_met | 全部条件满足时 matched=true |
| test_engine_partial_conditions | 部分条件不满足时 matched=false |
| test_engine_priority_ordering | 高优先级规则先评估 |
| test_engine_conflict_retain_all | 冲突策略 retain_all 保留全部结果 |
| test_engine_conflict_highest_wins | 冲突策略 highest_priority_wins 仅保留最高优先级 |
| test_engine_scope_filter | scope 不匹配的规则不评估 |

## 2. Knowledge 层测试

### 2.1 KnowledgeNode Schema

| 测试用例 | 验证内容 |
|---------|---------|
| test_node_valid_full | 完整合法节点可通过验证 |
| test_node_invalid_id_format | ID 不匹配 `kn:{type}:{slug}` 时拒绝 |
| test_node_empty_systems | systems 为空时拒绝（min_length=1） |
| test_node_all_node_types | 20 种 node_type 均可创建 |
| test_node_schools_multiple | 多流派解释正确存储 |

### 2.2 KnowledgeStore 查询

| 测试用例 | 验证内容 |
|---------|---------|
| test_store_get_node | 按 ID 获取节点 |
| test_store_query_by_type | 按 node_type 过滤 |
| test_store_query_by_tags | 按 tags 过滤 |
| test_store_query_by_system | 按 system 过滤 |
| test_store_get_relations | 获取节点的所有关系 |
| test_store_find_path | 两节点间的路径查找 |
| test_store_resolve_school | 按流派解析节点解释 |

### 2.3 Relation Schema

| 测试用例 | 验证内容 |
|---------|---------|
| test_relation_valid | 合法关系可通过验证 |
| test_relation_all_types | 15 种 relation_type 均可创建 |
| test_relation_directed_vs_undirected | 有向/无向关系区分 |
| test_relation_evidence_list | 关系证据列表正确存储 |

## 3. Pattern 层测试

| 测试用例 | 验证内容 |
|---------|---------|
| test_pattern_valid | 合法 Pattern 可通过验证 |
| test_pattern_rule_ids | 关联规则 ID 正确存储 |
| test_pattern_knowledge_node_ids | 关联知识节点 ID 正确存储 |
| test_pattern_matcher_single_rule | 单规则格局匹配 |
| test_pattern_matcher_multi_rule | 多规则组合格局匹配 |
| test_pattern_matcher_cross_system | 跨体系格局识别 |
| test_pattern_matcher_no_match | 不满足条件时不匹配 |

## 4. Evidence 层测试

| 测试用例 | 验证内容 |
|---------|---------|
| test_evidence_valid | 合法 Evidence 可通过验证 |
| test_evidence_empty_items | evidence_items 为空时拒绝 |
| test_evidence_item_source_types | 4 种 source_type 均可创建 |
| test_evidence_builder_from_rules | 从 RuleEvaluation 组装证据 |
| test_evidence_builder_from_patterns | 从 PatternMatch 组装证据 |

## 5. Evidence-Based Consensus 测试

| 测试用例 | 验证内容 |
|---------|---------|
| test_consensus_single_domain_single_conclusion | 单领域单结论 |
| test_consensus_single_domain_multi_conclusion | 单领域多结论并存（科研0.81/管理0.72/创业0.69） |
| test_consensus_multi_domain | 多领域分组 |
| test_consensus_confidence_ordering | 结论按 confidence 降序排列 |
| test_consensus_cross_system_pattern_bonus | 跨体系 Pattern 识别时置信度增强 |
| test_consensus_conflict_retain_all | 冲突时保留全部证据 |
| test_consensus_conflict_detection | 正确检测跨智能体冲突 |
| test_consensus_evidence_traceability | 每结论可追溯到规则/格局/知识节点 |
| test_consensus_overall_confidence_bounds | overall_confidence 在 [0,1] 内 |
| test_consensus_legacy_compat | 旧 ConsensusReport 仍可工作（legacy 模式） |

## 6. 集成测试（黄金向量）

| 测试用例 | 验证内容 |
|---------|---------|
| test_golden_bazi_shang_guan_pei_yin | 八字伤官佩印格局：规则匹配 + 证据 + 共识 |
| test_golden_ziwei_zi_fu_tong_gong | 紫微紫府同宫格局：格局匹配 + 证据 |
| test_golden_cross_system_wen_chang | 八字+紫微同时识别文昌相关格局：跨体系增强 |
| test_golden_multi_conclusion_career | 职业领域多结论并存场景 |
| test_golden_conflict_resolution | 冲突规则 retain_all 场景 |

## 7. 回归测试

| 测试用例 | 验证内容 |
|---------|---------|
| test_existing_bazi_unchanged | 八字引擎计算结果不受规则层影响 |
| test_existing_ziwei_unchanged | 紫微引擎计算结果不受规则层影响 |
| test_existing_consensus_legacy | 旧 ConsensusAgent 在 legacy 模式下仍工作 |
| test_existing_golden_vectors | 现有黄金向量测试仍通过 |
