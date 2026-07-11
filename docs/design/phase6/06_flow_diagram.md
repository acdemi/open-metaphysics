# Mermaid Flow Diagram（流程图）

> 状态：设计 v1 (2026-07-11)

## 1. 整体数据流：从排盘到证据聚合共识

```mermaid
flowchart TD
    A[AgentInput 请求] --> B[确定性引擎 calculate]
    B --> C[排盘结构 BaziChart / ZiweiChart / ...]
    C --> D[Rule Engine 规则评估]
    C --> E[Knowledge Graph 知识查询]
    D --> F[RuleEvaluation 规则评估结果]
    E --> G[KnowledgeNode + Relation 查询结果]
    F --> H[Pattern Matcher 格局匹配]
    G --> H
    H --> I[PatternMatch 格局匹配结果]
    F --> J[Evidence Builder 证据组装]
    I --> J
    G --> J
    J --> K[Evidence 证据集]
    K --> L[AgentOutput 增强: result + evidence + patterns]

    subgraph 多智能体并行
        L
    end

    L --> M[Consensus Agent 证据聚合]
    M --> N[按 Domain 分组]
    N --> O[同 Domain 内多结论聚合]
    O --> P[EvidenceConsensusReport]
    P --> Q[Explain Agent 解释渲染]
    Q --> R[最终响应 JSON]

    style B fill:#e8f5e9
    style D fill:#fff3e0
    style E fill:#e3f2fd
    style H fill:#f3e5f5
    style M fill:#fce4ec
    style Q fill:#f5f5f5
```

## 2. 规则评估流程（Rule Engine 内部）

```mermaid
flowchart TD
    START[排盘结构输入] --> LOAD[加载适用规则 RuleRegistry.query scope]
    LOAD --> LOOP{遍历每条 Rule}
    LOOP --> COND{评估 conditions}
    COND -->|全部满足| MATCHED[规则匹配 matched=true]
    COND -->|不满足| SKIP[跳过 matched=false]
    MATCHED --> PRIOR{检查 priority}
    PRIOR --> CONF{检查 conflicts}
    CONF -->|有冲突| STRAT{conflict_strategy}
    STRAT -->|retain_all| KEEP[保留全部结果]
    STRAT -->|highest_priority_wins| WIN[仅保留最高优先级]
    STRAT -->|merge| MERGE[结果加权合并]
    KEEP --> EVAL[RuleEvaluation]
    WIN --> EVAL
    MERGE --> EVAL
    SKIP --> EVAL
    EVAL --> NEXT{还有规则?}
    NEXT -->|是| LOOP
    NEXT -->|否| DONE[输出 RuleEvaluation 列表]

    style MATCHED fill:#c8e6c9
    style SKIP fill:#ffcdd2
    style KEEP fill:#bbdefb
```

## 3. 格局匹配流程（Pattern Matcher）

```mermaid
flowchart LR
    subgraph 输入
        RE[RuleEvaluation 列表]
        KG[KnowledgeNode 查询]
    end

    subgraph Pattern Matching
        PM[遍历 Pattern 定义]
        PM --> CHECK{Pattern.rule_ids 全部匹配?}
        CHECK -->|是| NODE{Pattern.knowledge_node_ids 存在?}
        CHECK -->|否| SKIP_P[跳过]
        NODE -->|是| MATCH_P[PatternMatch 匹配成功]
        NODE -->|否| SKIP_P
    end

    MATCH_P --> OUT[PatternMatch 列表]
    OUT --> CROSS{跨体系 Pattern 检测}
    CROSS -->|多 Agent 识别同一 Pattern| CROSS_MATCH[跨体系共识标记]
    CROSS -->|仅单体系| SINGLE[单体系标记]

    style MATCH_P fill:#c8e6c9
    style CROSS_MATCH fill:#fff9c4
```

## 4. Evidence-Based Consensus 聚合流程

```mermaid
flowchart TD
    INPUT[收集所有 Agent 的 Evidence + PatternMatch] --> GROUP[按 Domain 分组]
    GROUP --> DOMAIN_LOOP{遍历每个 Domain}

    DOMAIN_LOOP --> CONC_LOOP{遍历该 Domain 内所有结论}
    CONC_LOOP --> AGG[聚合同一结论的证据]
    AGG --> CALC[计算置信度: 证据加权 + 来源可信度 + 跨体系增强]
    CALC --> SORT[按置信度降序排列]
    SORT --> NEXT_CONC{还有结论?}
    NEXT_CONC -->|是| CONC_LOOP
    NEXT_CONC -->|否| NEXT_DOMAIN{还有 Domain?}
    NEXT_DOMAIN -->|是| DOMAIN_LOOP
    NEXT_DOMAIN -->|否| CONFLICT[冲突检测]

    CONFLICT --> CROSS_P[提取跨体系 Pattern]
    CROSS_P --> OVERALL[计算 overall_confidence]
    OVERALL --> REPORT[EvidenceConsensusReport]

    style AGG fill:#bbdefb
    style CALC fill:#fff9c4
    style REPORT fill:#c8e6c9
```

## 5. 置信度计算公式（设计说明）

单条结论的 `confidence` 计算方式（非代码，仅设计公式）：

```
conclusion_confidence = normalize(
    Σ(evidence_item.weight × source.credibility × agent_confidence_factor)
    / count(evidence_items)
    × cross_system_bonus
)

其中：
  - source.credibility: 引用来源的可信度（SourceRef.credibility）
  - agent_confidence_factor: 识别此证据的智能体的原始置信度
  - cross_system_bonus: 若多体系识别同一 Pattern，置信度增强（1.0 ~ 1.2）
  - normalize: 截断到 [0, 1]
```

## 6. 与现有 Consensus Agent 的对比

```mermaid
flowchart LR
    subgraph 旧方案 Weighted Average
        OLD_IN[AgentOutput 列表] --> OLD_W[按 confidence 加权]
        OLD_W --> OLD_MAT[五行一致性矩阵]
        OLD_MAT --> OLD_AVG[加权平均 confidence]
        OLD_AVG --> OLD_OUT[单一 ConsensusReport]
    end

    subgraph 新方案 Evidence Based
        NEW_IN[Evidence + PatternMatch] --> NEW_GRP[按 Domain 分组]
        NEW_GRP --> NEW_AGG[证据聚合]
        NEW_AGG --> NEW_MULTI[多结论并存]
        NEW_MULTI --> NEW_OUT[EvidenceConsensusReport]
    end

    style OLD_OUT fill:#ffcdd2
    style NEW_OUT fill:#c8e6c9
```

| 维度       | 旧方案（Weighted Average）         | 新方案（Evidence Based）              |
|-----------|-----------------------------------|---------------------------------------|
| 聚合对象   | AgentOutput.confidence            | Evidence + PatternMatch               |
| 结论数量   | 单一结论                          | 多结论并存                            |
| 可追溯性   | 仅 confidence 数值                | 每结论附带全部证据                    |
| 跨体系比较 | 比较五行一致性                    | 比较共同 Pattern                      |
| 冲突处理   | 降低 overall_confidence           | retain_all，保留全部证据              |
