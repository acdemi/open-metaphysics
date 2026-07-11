# Mermaid ER Diagram（实体关系图）

> 状态：设计 v1 (2026-07-11)

## 知识层 + 规则层 + 共识层 实体关系

```mermaid
erDiagram
    RULE ||--o{ RULE_CONDITION : "has"
    RULE ||--o{ RULE_RESULT : "produces"
    RULE ||--o{ RULE : "conflicts_with"
    RULE ||--o{ PATTERN : "composes"

    KNOWLEDGE_NODE ||--o{ SCHOOL_VIEW : "has_school"
    KNOWLEDGE_NODE ||--o{ RELATION : "source_of"
    KNOWLEDGE_NODE ||--o{ RELATION : "target_of"
    KNOWLEDGE_NODE ||--o{ PATTERN : "referenced_by"
    KNOWLEDGE_NODE ||--o{ RULE_RESULT : "conclusion_node"

    RELATION ||--o{ RELATION_EVIDENCE : "supported_by"

    PATTERN ||--o{ RULE : "rule_ids"
    PATTERN ||--o{ KNOWLEDGE_NODE : "knowledge_node_ids"
    PATTERN }o--o{ AGENT : "agent_identifiers"

    RULE_EVALUATION }o--|| RULE : "evaluates"
    PATTERN_MATCH }o--|| PATTERN : "matches"

    EVIDENCE_ITEM }o--|| RULE : "source_rule"
    EVIDENCE_ITEM }o--|| PATTERN : "source_pattern"
    EVIDENCE_ITEM }o--|| KNOWLEDGE_NODE : "source_node"

    EVIDENCE ||--o{ EVIDENCE_ITEM : "contains"
    CONCLUSION_WITH_EVIDENCE ||--o{ EVIDENCE_ITEM : "backed_by"
    DOMAIN_CONSENSUS ||--o{ CONCLUSION_WITH_EVIDENCE : "conclusions"
    EVIDENCE_CONSENSUS_REPORT ||--o{ DOMAIN_CONSENSUS : "domains"
    EVIDENCE_CONSENSUS_REPORT ||--o{ CONSENSUS_CONFLICT : "conflicts"
    EVIDENCE_CONSENSUS_REPORT ||--o{ PATTERN : "cross_domain_patterns"

    RULE {
        string id PK
        string name
        MetaphysicsSystem system
        RuleType rule_type
        int priority
        float confidence
        string version
        SourceRef source
    }

    RULE_CONDITION {
        string field
        ConditionOperator operator
        any value
        bool negate
    }

    RULE_RESULT {
        Domain domain
        string conclusion
        string conclusion_node_id FK
        float weight
        ResultDirection direction
    }

    KNOWLEDGE_NODE {
        string id PK
        NodeType node_type
        string name_cn
        string name_en
        list systems
        string interpretation
        float confidence
        dict attributes
    }

    SCHOOL_VIEW {
        string school
        string interpretation
        float weight
    }

    RELATION {
        string id PK
        string source_node_id FK
        string target_node_id FK
        RelationType relation_type
        RelationDirection direction
        float weight
    }

    RELATION_EVIDENCE {
        string description
        float weight
    }

    PATTERN {
        string id PK
        string name_cn
        string name_en
        list systems
        float confidence
        string version
    }

    RULE_EVALUATION {
        string rule_id FK
        bool matched
        list results
    }

    PATTERN_MATCH {
        string pattern_id FK
        string matched_by
        float confidence
    }

    EVIDENCE_ITEM {
        EvidenceSourceType source_type
        string source_id
        string source_name
        string source_ref
        float weight
        string agent
    }

    EVIDENCE {
        Domain domain
        string conclusion
        float confidence
    }

    CONCLUSION_WITH_EVIDENCE {
        string conclusion
        float confidence
        list contributing_agents
    }

    DOMAIN_CONSENSUS {
        Domain domain
    }

    EVIDENCE_CONSENSUS_REPORT {
        string request_id PK
        string aggregation_method
        float overall_confidence
    }

    CONSENSUS_CONFLICT {
        list agents
        Domain domain
        list conclusions
        string severity
        string resolution
    }

    AGENT {
        string name
        string engine_version
    }
```

## 核心实体说明

- **RULE** 是规则层的核心实体，包含条件（RULE_CONDITION）和结果（RULE_RESULT），可声明冲突关系。
- **KNOWLEDGE_NODE** 是知识层的核心实体，支持多流派（SCHOOL_VIEW），通过 RELATION 构成知识图谱。
- **PATTERN** 是连接层：组合多个 RULE，引用多个 KNOWLEDGE_NODE，被多个 AGENT 识别。
- **EVIDENCE_ITEM** 是多态引用：可指向 RULE、PATTERN 或 KNOWLEDGE_NODE，是共识层的最小证据单元。
- **EVIDENCE_CONSENSUS_REPORT** 取代旧 ConsensusReport：按 DOMAIN 分组，每个 DOMAIN 内多个 CONCLUSION_WITH_EVIDENCE 并存。
