# Phase 6：规则层（Rule Engine）与知识层（Knowledge Layer）设计

## 角色

你现在是 OpenMetaphysics 项目的首席架构师（Principal Architect）和核心开发工程师。

在开始任何开发之前，请完整阅读：

* README.md
* docs/
* context/
* tests/

充分理解现有架构。

不得推翻已经完成并通过测试的模块。

---

# 项目目标

本阶段不是增加新的命理系统。

本阶段目标是：

建立 OpenMetaphysics 的统一规则层（Rule Layer）和知识层（Knowledge Layer）。

未来：

八字

紫微

奇门

六爻

梅花

大六壬

都必须能够接入这一层。

这一层将成为：

Consensus Agent

Explain Agent

RAG

未来 MCP

共同的数据基础。

---

# 第一原则

Rule First.

Knowledge Second.

LLM Last.

凡是能够通过规则表达的内容，

禁止交给 LLM。

LLM 仅负责：

解释

总结

自然语言生成。

---

# 第一阶段

设计 Rule Schema。

要求：

每一条规则必须可以结构化表示。

例如：

规则编号

规则名称

所属体系

规则类型

输入条件

输出结果

优先级

适用范围

冲突规则

引用来源

可信度

版本

JSON 示例：

{
"id": "",
"system": "",
"rule_type": "",
"conditions": [],
"results": [],
"priority": 0,
"source": "",
"version": "",
"confidence": 1.0
}

---

# 第二阶段

设计 Knowledge Schema。

知识节点至少支持：

五行

十神

天干

地支

十二宫

十四主星

辅星

神煞

格局

职业

性格

婚姻

健康

财富

流年

大运

用神

喜神

忌神

调候

所有节点必须拥有：

唯一ID

中文名称

英文标识

所属体系

来源

解释

标签

可信度

多个流派支持。

---

# 第三阶段

设计 Relation。

至少支持：

生

克

冲

刑

合

害

扶助

制约

对应

影响

增强

削弱

指向

属于

引用

所有关系允许：

方向

权重

证据

来源。

---

# 第四阶段

设计 Evidence Schema。

Consensus Agent 不允许直接输出结论。

必须输出：

Evidence。

例如：

{
"domain": "career",
"conclusion": "适合科研",
"confidence": 0.82,
"evidence": [
{
"rule": "伤官佩印",
"source": "滴天髓",
"weight": 0.91
},
{
"rule": "文昌入命",
"source": "紫微斗数全书",
"weight": 0.76
}
]
}

---

# 第五阶段

建立 Pattern Layer。

Pattern 用于连接：

规则

知识

Agent

例如：

Pattern：

伤官佩印

Pattern：

官印相生

Pattern：

杀印相生

Pattern：

紫府同宫

Pattern：

机月同梁

Pattern：

羊陀夹命

每个 Pattern：

可以由多个规则组成。

多个 Agent 可以共同识别同一个 Pattern。

Consensus Agent 不直接比较 JSON。

而比较：

Pattern。

---

# 第六阶段

重新设计 Consensus。

目标：

从：

Weighted Average

升级为：

Evidence Based Consensus。

Consensus：

不是投票。

而是：

Evidence Aggregation。

必须支持：

多个不同结论同时存在。

例如：

职业：

科研

0.81

管理

0.72

创业

0.69

并给出所有支持证据。

---

# 本阶段禁止事项

禁止：

实现前端。

禁止：

增加 Docker。

禁止：

数据库持久化。

禁止：

增加新的 Agent。

禁止：

修改已经稳定的八字、紫微计算。

---

# 本阶段交付物

必须输出：

1、Knowledge Layer Architecture

2、Rule Layer Architecture

3、JSON Schema

4、Pydantic Model

5、Mermaid ER Diagram

6、Mermaid Flow Diagram

7、Architecture Decision Record（ADR）

8、Implementation Roadmap（Phase 6 ~ Phase 9）

9、单元测试计划（无需实现）

10、风险分析

注意：

本阶段以设计为主。

只有在架构确认后，

才允许进入代码实现阶段。

不要提前实现数据库。

不要提前实现 Neo4j。

先完成模型设计。
# Phase 6：规则层（Rule Engine）与知识层（Knowledge Layer）设计

## 角色

你现在是 OpenMetaphysics 项目的首席架构师（Principal Architect）和核心开发工程师。

在开始任何开发之前，请完整阅读：

* README.md
* docs/
* context/
* tests/

充分理解现有架构。

不得推翻已经完成并通过测试的模块。

---

# 项目目标

本阶段不是增加新的命理系统。

本阶段目标是：

建立 OpenMetaphysics 的统一规则层（Rule Layer）和知识层（Knowledge Layer）。

未来：

八字

紫微

奇门

六爻

梅花

大六壬

都必须能够接入这一层。

这一层将成为：

Consensus Agent

Explain Agent

RAG

未来 MCP

共同的数据基础。

---

# 第一原则

Rule First.

Knowledge Second.

LLM Last.

凡是能够通过规则表达的内容，

禁止交给 LLM。

LLM 仅负责：

解释

总结

自然语言生成。

---

# 第一阶段

设计 Rule Schema。

要求：

每一条规则必须可以结构化表示。

例如：

规则编号

规则名称

所属体系

规则类型

输入条件

输出结果

优先级

适用范围

冲突规则

引用来源

可信度

版本

JSON 示例：

{
"id": "",
"system": "",
"rule_type": "",
"conditions": [],
"results": [],
"priority": 0,
"source": "",
"version": "",
"confidence": 1.0
}

---

# 第二阶段

设计 Knowledge Schema。

知识节点至少支持：

五行

十神

天干

地支

十二宫

十四主星

辅星

神煞

格局

职业

性格

婚姻

健康

财富

流年

大运

用神

喜神

忌神

调候

所有节点必须拥有：

唯一ID

中文名称

英文标识

所属体系

来源

解释

标签

可信度

多个流派支持。

---

# 第三阶段

设计 Relation。

至少支持：

生

克

冲

刑

合

害

扶助

制约

对应

影响

增强

削弱

指向

属于

引用

所有关系允许：

方向

权重

证据

来源。

---

# 第四阶段

设计 Evidence Schema。

Consensus Agent 不允许直接输出结论。

必须输出：

Evidence。

例如：

{
"domain": "career",
"conclusion": "适合科研",
"confidence": 0.82,
"evidence": [
{
"rule": "伤官佩印",
"source": "滴天髓",
"weight": 0.91
},
{
"rule": "文昌入命",
"source": "紫微斗数全书",
"weight": 0.76
}
]
}

---

# 第五阶段

建立 Pattern Layer。

Pattern 用于连接：

规则

知识

Agent

例如：

Pattern：

伤官佩印

Pattern：

官印相生

Pattern：

杀印相生

Pattern：

紫府同宫

Pattern：

机月同梁

Pattern：

羊陀夹命

每个 Pattern：

可以由多个规则组成。

多个 Agent 可以共同识别同一个 Pattern。

Consensus Agent 不直接比较 JSON。

而比较：

Pattern。

---

# 第六阶段

重新设计 Consensus。

目标：

从：

Weighted Average

升级为：

Evidence Based Consensus。

Consensus：

不是投票。

而是：

Evidence Aggregation。

必须支持：

多个不同结论同时存在。

例如：

职业：

科研

0.81

管理

0.72

创业

0.69

并给出所有支持证据。

---

# 本阶段禁止事项

禁止：

实现前端。

禁止：

增加 Docker。

禁止：

数据库持久化。

禁止：

增加新的 Agent。

禁止：

修改已经稳定的八字、紫微计算。

---

# 本阶段交付物

必须输出：

1、Knowledge Layer Architecture

2、Rule Layer Architecture

3、JSON Schema

4、Pydantic Model

5、Mermaid ER Diagram

6、Mermaid Flow Diagram

7、Architecture Decision Record（ADR）

8、Implementation Roadmap（Phase 6 ~ Phase 9）

9、单元测试计划（无需实现）

10、风险分析

注意：

本阶段以设计为主。

只有在架构确认后，

才允许进入代码实现阶段。

不要提前实现数据库。

不要提前实现 Neo4j。

先完成模型设计。
