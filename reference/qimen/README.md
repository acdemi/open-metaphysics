# Reference Qimen Domain

> **状态**: Phase 5.9B 实现 + **Phase 5.7 对齐（依契约 v1.0.0；独立性声明：不导入 src）**
> **契约**: [QIMEN_BEHAVIOR_CONTRACT.md](../../docs/specification/QIMEN_BEHAVIOR_CONTRACT.md) v1.0.0 (Frozen)
> **规范向量**: [golden_vectors.json](../../docs/qimen/golden_vectors.json)（24, normative fixtures）
> **产品运行时**: `src/openmetaphysics/agents/qimen.py`（engine v0.3.0）
> **验收**: `reference/tests/` 独立套件（E016: 24/24 逐字节一致 + 源码独立性检查；E017: 30/30 等价）

---

## 1. Reference Domain 边界

`reference/qimen/` 是奇门遁甲领域的 **Reference Domain**：

- ✅ 领域概念建模（盘面 / 遁局 / 天地盘 / 值符值使 / 星门神 / 空亡中宫）
- ✅ 流派差异显式记录（见 [concepts/schools.md](concepts/schools.md)）
- ✅ Runtime 与 Reference 对照（见 [runtime_vs_reference.md](runtime_vs_reference.md)）
- ✅ **契约实现**: [domain.py](domain.py) —— 依契约 QC-001~014 构建九宫盘，输出与 24 规范向量逐字节一致（由测试强制）
- ❌ 不定义新行为 —— 行为权威唯一来源是契约 v1.0.0

### 层级关系

```
docs/specification/QIMEN_BEHAVIOR_CONTRACT.md   ← 行为权威（Frozen v1.0.0）
docs/qimen/golden_vectors.json                  ← 规范回归装置（24, immutable）
src/openmetaphysics/agents/qimen.py             ← 产品运行时（契约绑定）
reference/qimen/domain.py                       ← 本域实现（契约对齐，验收=向量一致）
src/openmetaphysics/core/*                          ← 共享基础层（节气/干支/真太阳时, Phase 1）
reference/*.py (Rule/Pattern/Evidence/...)      ← 既有 Reference Runtime 层（不属本域）
```

## 2. 目录结构

```
reference/qimen/
├── README.md                   # 本文件：Domain 边界
├── domain.py                   # ★ 契约实现 (Phase 5.9B, 24/24 向量一致)
├── runtime_vs_reference.md     # Runtime ↔ Reference 对照
└── concepts/                   # 领域概念建模
    ├── board.md                # 盘面模型（九宫）
    ├── dundun_ju.md            # 遁与局（阴阳遁 / 三元 / 局数）
    ├── plates.md               # 天地盘
    ├── zhifu_zhishi.md         # 值符与值使
    ├── stars_doors_gods.md     # 九星 / 八门 / 八神
    ├── void_central.md         # 空亡与中宫
    └── schools.md              # ★ 流派差异记录（强制项）
```

## 3. 约束（本域强制）

1. **不修改** `src/openmetaphysics/agents/qimen.py`
2. **不修改** `docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`
3. **不修改** `docs/qimen/golden_vectors.json`
4. 实现变更后必须通过 `tests/test_reference_qimen.py`（24/24 向量一致）
5. **所有流派差异必须显式记录**（`concepts/schools.md`）

违反以上任何一条即视为越界，需 ACP。

## 4. 文档测试

`tests/test_qimen_reference_docs.py`：结构存在性 / 实现层存在 / 链接可解析 / 外部引用 / 流派记录。`tests/test_reference_qimen.py`：24/24 向量验收 + 确定性 + 与 Product Runtime 双实现互证。

## 5. 参考文档

| 文档 | 用途 |
|------|------|
| [QIMEN_BEHAVIOR_CONTRACT.md](../../docs/specification/QIMEN_BEHAVIOR_CONTRACT.md) | 行为权威（Frozen v1.0.0） |
| [QIMEN_RULE_DECISION.md](../../docs/qimen/QIMEN_RULE_DECISION.md) | 规则裁定记录（D1-D14） |
| [QIMEN_ALGORITHM_ASSUMPTIONS.md](../../docs/qimen/QIMEN_ALGORITHM_ASSUMPTIONS.md) | 算法假设明细 |
| [QIMEN_FREEZE_REVIEW.md](../../docs/qimen/QIMEN_FREEZE_REVIEW.md) | Freeze 评审 |
| [QIMEN_FREEZE_GAP.md](../../docs/qimen/QIMEN_FREEZE_GAP.md) | 冻结缺口（已关闭） |
| [QIMEN_D2_IMPACT_ANALYSIS.md](../../docs/qimen/QIMEN_D2_IMPACT_ANALYSIS.md) | D2 迁移影响分析 |
| [golden_vectors.json](../../docs/qimen/golden_vectors.json) | 24 规范向量 |


### 共享基础层依赖（显式记录）

`domain.py` 从 `src/openmetaphysics/core/` 导入节气时刻/日干支/真太阳时
（Phase 1 共享基础，自研核心 IP C-04）。奇门规范性表格与规则全部自包含于
`domain.py`，不依赖 src agents。
