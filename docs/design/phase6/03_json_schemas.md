# JSON Schema 定义

> 状态：设计 v1 (2026-07-11)
> 所有 Schema 可通过 `Model.model_json_schema()` 导出为标准 JSON Schema。

---

## 1. Rule JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Rule",
  "type": "object",
  "required": ["id", "name", "system", "rule_type", "conditions", "results", "priority", "source", "version", "confidence"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^rule:[a-z]+:[a-z_]+:v[0-9]+$",
      "description": "全局唯一规则 ID"
    },
    "name": { "type": "string", "description": "规则名称（中文）" },
    "name_en": { "type": "string", "description": "英文标识" },
    "system": {
      "type": "string",
      "enum": ["bazi", "ziwei", "qimen", "liuyao", "meihua", "liuren"]
    },
    "rule_type": {
      "type": "string",
      "enum": ["pattern_recognition", "relation_derivation", "ten_god_determination",
               "yong_shen_determination", "element_balance", "domain_inference",
               "conflict_resolution", "da_yun_analysis"]
    },
    "conditions": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/RuleCondition" }
    },
    "results": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/RuleResult" }
    },
    "priority": { "type": "integer", "minimum": 0, "maximum": 100, "default": 50 },
    "scope": { "$ref": "#/$defs/RuleScope" },
    "conflicts": {
      "type": "array",
      "items": { "type": "string" },
      "description": "冲突规则 ID 列表"
    },
    "conflict_strategy": {
      "type": "string",
      "enum": ["highest_priority_wins", "retain_all", "merge"],
      "default": "retain_all"
    },
    "source": { "$ref": "#/$defs/SourceRef" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
    "deprecated": { "type": "boolean", "default": false },
    "superseded_by": { "type": "string", "description": "替代此规则的新规则 ID" }
  },
  "$defs": {
    "RuleCondition": {
      "type": "object",
      "required": ["field", "operator"],
      "properties": {
        "field": { "type": "string", "description": "排盘数据路径" },
        "operator": {
          "type": "string",
          "enum": ["equals", "not_equals", "contains", "not_contains", "in",
                   "not_in", "greater_than", "less_than", "exists", "not_exists", "matches"]
        },
        "value": {},
        "negate": { "type": "boolean", "default": false },
        "description": { "type": "string" }
      }
    },
    "RuleResult": {
      "type": "object",
      "required": ["domain", "conclusion", "weight"],
      "properties": {
        "domain": {
          "type": "string",
          "enum": ["career", "personality", "marriage", "health", "wealth",
                   "education", "family", "travel", "legal", "overall"]
        },
        "conclusion": { "type": "string" },
        "conclusion_node_id": { "type": "string" },
        "weight": { "type": "number", "minimum": 0, "maximum": 1 },
        "direction": {
          "type": "string",
          "enum": ["positive", "negative", "neutral"],
          "default": "positive"
        }
      }
    },
    "RuleScope": {
      "type": "object",
      "properties": {
        "systems": { "type": "array", "items": { "type": "string" } },
        "gender": {
          "type": "array",
          "items": { "type": "string", "enum": ["male", "female"] }
        },
        "age_range": {
          "type": "array",
          "items": { "type": "integer" },
          "minItems": 2,
          "maxItems": 2
        }
      }
    },
    "SourceRef": {
      "type": "object",
      "required": ["text"],
      "properties": {
        "text": { "type": "string" },
        "chapter": { "type": "string" },
        "author": { "type": "string" },
        "page": { "type": "integer" },
        "url": { "type": "string" },
        "credibility": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.8 }
      }
    }
  }
}
```

### Rule JSON 示例

```json
{
  "id": "rule:bazi:shang_guan_pei_yin:v1",
  "name": "伤官佩印",
  "name_en": "wounded_officer_adorned_by_seal",
  "system": "bazi",
  "rule_type": "pattern_recognition",
  "conditions": [
    { "field": "ten_gods_map.values", "operator": "contains", "value": "伤官", "description": "命局中有伤官" },
    { "field": "ten_gods_map.values", "operator": "contains", "value": "正印", "description": "命局中有正印" },
    { "field": "day_master_strength", "operator": "less_than", "value": 0.4, "description": "日主偏弱" }
  ],
  "results": [
    { "domain": "career", "conclusion": "适合科研", "conclusion_node_id": "kn:career:research", "weight": 0.91, "direction": "positive" },
    { "domain": "personality", "conclusion": "聪慧好学", "conclusion_node_id": "kn:personality:intellectual", "weight": 0.85, "direction": "positive" }
  ],
  "priority": 80,
  "scope": { "systems": ["bazi"], "gender": null },
  "conflicts": ["rule:bazi:shang_guan_jian_sha:v1"],
  "conflict_strategy": "retain_all",
  "source": { "text": "滴天髓", "chapter": "伤官", "credibility": 0.95 },
  "confidence": 1.0,
  "version": "1.0.0"
}
```

---

## 2. KnowledgeNode JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "KnowledgeNode",
  "type": "object",
  "required": ["id", "node_type", "name_cn", "name_en", "systems", "source", "interpretation", "confidence"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^kn:[a-z_]+:[a-z_0-9]+$",
      "description": "全局唯一知识节点 ID"
    },
    "node_type": {
      "type": "string",
      "enum": ["wuxing", "ten_god", "heavenly_stem", "earthly_branch", "palace",
               "main_star", "auxiliary_star", "shen_sha", "pattern", "career",
               "personality", "marriage", "health", "wealth", "annual_fortune",
               "major_luck", "yong_shen", "xi_shen", "ji_shen", "tiao_hou"]
    },
    "name_cn": { "type": "string" },
    "name_en": { "type": "string" },
    "systems": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string", "enum": ["bazi", "ziwei", "qimen", "liuyao", "meihua", "liuren"] }
    },
    "source": { "$ref": "#/$defs/SourceRef" },
    "interpretation": { "type": "string", "description": "标准解释" },
    "tags": { "type": "array", "items": { "type": "string" } },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "schools": {
      "type": "array",
      "items": { "$ref": "#/$defs/SchoolView" },
      "description": "多流派解释"
    },
    "attributes": {
      "type": "object",
      "description": "类型特定属性（按 node_type 预定义键集合）"
    }
  },
  "$defs": {
    "SchoolView": {
      "type": "object",
      "required": ["school", "interpretation"],
      "properties": {
        "school": { "type": "string", "description": "流派名称" },
        "interpretation": { "type": "string" },
        "source": { "$ref": "#/$defs/SourceRef" },
        "weight": { "type": "number", "minimum": 0, "maximum": 1, "default": 1.0 }
      }
    },
    "SourceRef": {
      "type": "object",
      "required": ["text"],
      "properties": {
        "text": { "type": "string" },
        "chapter": { "type": "string" },
        "author": { "type": "string" },
        "page": { "type": "integer" },
        "url": { "type": "string" },
        "credibility": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.8 }
      }
    }
  }
}
```

### KnowledgeNode JSON 示例

```json
{
  "id": "kn:wuxing:mu",
  "node_type": "wuxing",
  "name_cn": "木",
  "name_en": "wood",
  "systems": ["bazi", "ziwei", "qimen", "liuyao"],
  "source": { "text": "尚书·洪范", "credibility": 1.0 },
  "interpretation": "木主仁，性直，主生长升发，对应东方、春季、青色、肝胆。",
  "tags": ["阳", "东方", "春季", "肝胆"],
  "confidence": 1.0,
  "schools": [
    {
      "school": "子平",
      "interpretation": "甲木为参天大树，乙木为花草藤萝。木旺需金伐成材，木弱需水滋生。",
      "source": { "text": "滴天髓", "credibility": 0.95 },
      "weight": 1.0
    },
    {
      "school": "盲派",
      "interpretation": "木象主条达，重象不重理，看木在命局中的刑冲合害。",
      "source": { "text": "盲师口传", "credibility": 0.7 },
      "weight": 0.8
    }
  ],
  "attributes": {
    "yin_yang": "阳",
    "season": "春",
    "direction": "东",
    "color": "青",
    "organ": "肝胆",
    "generates": "kn:wuxing:huo",
    "generated_by": "kn:wuxing:shui",
    "controls": "kn:wuxing:tu",
    "controlled_by": "kn:wuxing:jin"
  }
}
```

---

## 3. Relation JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Relation",
  "type": "object",
  "required": ["id", "source_node_id", "target_node_id", "relation_type", "direction", "weight"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^rel:.+$",
      "description": "关系唯一 ID"
    },
    "source_node_id": { "type": "string", "description": "源知识节点 ID" },
    "target_node_id": { "type": "string", "description": "目标知识节点 ID" },
    "relation_type": {
      "type": "string",
      "enum": ["sheng", "ke", "chong", "xing", "he", "hai",
               "fuzhu", "zhiyue", "duiying", "yingxiang",
               "zengqiang", "xueroo", "zhixiang", "shuyu", "yinyong"],
      "description": "生/克/冲/刑/合/害/扶助/制约/对应/影响/增强/削弱/指向/属于/引用"
    },
    "direction": {
      "type": "string",
      "enum": ["directed", "undirected"],
      "default": "directed"
    },
    "weight": { "type": "number", "minimum": 0, "maximum": 1, "default": 1.0 },
    "evidence": {
      "type": "array",
      "items": { "$ref": "#/$defs/RelationEvidence" }
    },
    "source": { "$ref": "#/$defs/SourceRef" },
    "conditions": {
      "type": "array",
      "items": { "type": "object" },
      "description": "关系生效的条件（可选）"
    }
  },
  "$defs": {
    "RelationEvidence": {
      "type": "object",
      "required": ["description"],
      "properties": {
        "description": { "type": "string" },
        "source": { "$ref": "#/$defs/SourceRef" },
        "weight": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    },
    "SourceRef": {
      "type": "object",
      "required": ["text"],
      "properties": {
        "text": { "type": "string" },
        "chapter": { "type": "string" },
        "author": { "type": "string" },
        "credibility": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.8 }
      }
    }
  }
}
```

### Relation JSON 示例

```json
{
  "id": "rel:wuxing:mu:sheng:wuxing:huo:v1",
  "source_node_id": "kn:wuxing:mu",
  "target_node_id": "kn:wuxing:huo",
  "relation_type": "sheng",
  "direction": "directed",
  "weight": 1.0,
  "evidence": [
    {
      "description": "木生火，木为火之母，火为木之子",
      "source": { "text": "尚书·洪范", "credibility": 1.0 },
      "weight": 1.0
    }
  ],
  "source": { "text": "素问·阴阳应象大论", "credibility": 0.95 }
}
```

---

## 4. Evidence JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Evidence",
  "type": "object",
  "required": ["domain", "conclusion", "confidence", "evidence_items"],
  "properties": {
    "domain": {
      "type": "string",
      "enum": ["career", "personality", "marriage", "health", "wealth",
               "education", "family", "travel", "legal", "overall"]
    },
    "conclusion": { "type": "string", "description": "结论文本" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "evidence_items": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/EvidenceItem" }
    }
  },
  "$defs": {
    "EvidenceItem": {
      "type": "object",
      "required": ["source_type", "source_id", "source_name", "source_ref", "weight"],
      "properties": {
        "source_type": {
          "type": "string",
          "enum": ["rule", "pattern", "knowledge_node", "relation"]
        },
        "source_id": { "type": "string", "description": "规则/格局/知识节点 ID" },
        "source_name": { "type": "string", "description": "名称" },
        "source_ref": { "type": "string", "description": "引用来源文本" },
        "weight": { "type": "number", "minimum": 0, "maximum": 1 },
        "agent": { "type": "string", "description": "识别此证据的智能体" }
      }
    }
  }
}
```

### Evidence JSON 示例

```json
{
  "domain": "career",
  "conclusion": "适合科研",
  "confidence": 0.82,
  "evidence_items": [
    {
      "source_type": "rule",
      "source_id": "rule:bazi:shang_guan_pei_yin:v1",
      "source_name": "伤官佩印",
      "source_ref": "滴天髓",
      "weight": 0.91,
      "agent": "bazi"
    },
    {
      "source_type": "pattern",
      "source_id": "pattern:ziwei:wen_chang_ru_ming:v1",
      "source_name": "文昌入命",
      "source_ref": "紫微斗数全书",
      "weight": 0.76,
      "agent": "ziwei"
    }
  ]
}
```

---

## 5. Pattern JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Pattern",
  "type": "object",
  "required": ["id", "name_cn", "name_en", "systems", "rule_ids", "version"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^pattern:[a-z_]+:[a-z_0-9]+:v[0-9]+$"
    },
    "name_cn": { "type": "string" },
    "name_en": { "type": "string" },
    "systems": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string", "enum": ["bazi", "ziwei", "qimen", "liuyao", "meihua", "liuren"] }
    },
    "rule_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "组成此格局的规则 ID 列表"
    },
    "knowledge_node_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "关联的知识节点 ID"
    },
    "agent_identifiers": {
      "type": "array",
      "items": { "type": "string", "enum": ["bazi", "ziwei", "qimen", "liuyao", "consensus"] },
      "description": "能识别此格局的智能体"
    },
    "domain_tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "关联领域标签"
    },
    "interpretation": { "type": "string" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "source": { "$ref": "#/$defs/SourceRef" },
    "version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" }
  },
  "$defs": {
    "SourceRef": {
      "type": "object",
      "required": ["text"],
      "properties": {
        "text": { "type": "string" },
        "credibility": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.8 }
      }
    }
  }
}
```

### Pattern JSON 示例

```json
{
  "id": "pattern:bazi:shang_guan_pei_yin:v1",
  "name_cn": "伤官佩印",
  "name_en": "wounded_officer_adorned_by_seal",
  "systems": ["bazi"],
  "rule_ids": ["rule:bazi:shang_guan_pei_yin:v1"],
  "knowledge_node_ids": ["kn:ten_god:shang_guan", "kn:ten_god:zheng_yin"],
  "agent_identifiers": ["bazi"],
  "domain_tags": ["career", "education"],
  "interpretation": "伤官佩印，主聪慧好学，适合学术科研。印制伤官之傲，化泄为用。",
  "confidence": 0.9,
  "source": { "text": "滴天髓", "credibility": 0.95 },
  "version": "1.0.0"
}
```

---

## 6. Evidence-Based Consensus JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EvidenceConsensusReport",
  "type": "object",
  "required": ["request_id", "domains", "aggregation_method"],
  "properties": {
    "request_id": { "type": "string" },
    "domains": {
      "type": "array",
      "items": { "$ref": "#/$defs/DomainConsensus" },
      "description": "每个领域的共识结果（支持多结论并存）"
    },
    "aggregation_method": {
      "type": "string",
      "enum": ["evidence_based"],
      "description": "固定为 evidence_based（取代旧 weighted/majority/all）"
    },
    "cross_domain_patterns": {
      "type": "array",
      "items": { "type": "string" },
      "description": "跨体系识别到的 Pattern ID 列表"
    },
    "conflicts": {
      "type": "array",
      "items": { "$ref": "#/$defs/ConsensusConflict" }
    },
    "overall_confidence": { "type": "number", "minimum": 0, "maximum": 1 }
  },
  "$defs": {
    "DomainConsensus": {
      "type": "object",
      "required": ["domain", "conclusions"],
      "properties": {
        "domain": {
          "type": "string",
          "enum": ["career", "personality", "marriage", "health", "wealth",
                   "education", "family", "travel", "legal", "overall"]
        },
        "conclusions": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/ConclusionWithEvidence" },
          "description": "多个不同结论同时存在，按置信度降序排列"
        }
      }
    },
    "ConclusionWithEvidence": {
      "type": "object",
      "required": ["conclusion", "confidence", "evidence_items"],
      "properties": {
        "conclusion": { "type": "string" },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "evidence_items": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/EvidenceItem" }
        },
        "contributing_agents": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "EvidenceItem": {
      "type": "object",
      "required": ["source_type", "source_id", "source_name", "source_ref", "weight"],
      "properties": {
        "source_type": { "type": "string", "enum": ["rule", "pattern", "knowledge_node", "relation"] },
        "source_id": { "type": "string" },
        "source_name": { "type": "string" },
        "source_ref": { "type": "string" },
        "weight": { "type": "number", "minimum": 0, "maximum": 1 },
        "agent": { "type": "string" }
      }
    },
    "ConsensusConflict": {
      "type": "object",
      "required": ["agents", "domain", "conclusions", "severity"],
      "properties": {
        "agents": { "type": "array", "items": { "type": "string" } },
        "domain": { "type": "string" },
        "conclusions": { "type": "array", "items": { "type": "string" } },
        "severity": { "type": "string", "enum": ["low", "medium", "high"] },
        "resolution": { "type": "string", "enum": ["retain_all", "highest_confidence", "merged"] }
      }
    }
  }
}
```

### Evidence-Based Consensus JSON 示例

```json
{
  "request_id": "req-001",
  "aggregation_method": "evidence_based",
  "domains": [
    {
      "domain": "career",
      "conclusions": [
        {
          "conclusion": "适合科研",
          "confidence": 0.81,
          "contributing_agents": ["bazi", "ziwei"],
          "evidence_items": [
            { "source_type": "rule", "source_id": "rule:bazi:shang_guan_pei_yin:v1", "source_name": "伤官佩印", "source_ref": "滴天髓", "weight": 0.91, "agent": "bazi" },
            { "source_type": "pattern", "source_id": "pattern:ziwei:wen_chang:v1", "source_name": "文昌入命", "source_ref": "紫微斗数全书", "weight": 0.76, "agent": "ziwei" }
          ]
        },
        {
          "conclusion": "适合管理",
          "confidence": 0.72,
          "contributing_agents": ["bazi"],
          "evidence_items": [
            { "source_type": "rule", "source_id": "rule:bazi:guan_yin:v1", "source_name": "官印相生", "source_ref": "子平真诠", "weight": 0.82, "agent": "bazi" }
          ]
        },
        {
          "conclusion": "适合创业",
          "confidence": 0.69,
          "contributing_agents": ["bazi"],
          "evidence_items": [
            { "source_type": "rule", "source_id": "rule:bazi:shi_shen_zhi_cai:v1", "source_name": "食神生财", "source_ref": "滴天髓", "weight": 0.78, "agent": "bazi" }
          ]
        }
      ]
    }
  ],
  "cross_domain_patterns": ["pattern:bazi:shang_guan_pei_yin:v1", "pattern:ziwei:wen_chang:v1"],
  "conflicts": [],
  "overall_confidence": 0.78
}
```
