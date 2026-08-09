# Domain Capability Template

> 领域能力登记模板（Domain Capability Template）
> 每个命理领域复制本模板填写，并登记于 `docs/governance/CAPABILITY_STATUS.md`。
> 标准依据: `docs/governance/CAPABILITY_LIFECYCLE.md`
> 更新: 2026-08-09

---

## Domain Metadata

| 字段 | 值 | 说明 |
|------|----|------|
| **name** | `<domain>` | 领域名（bazi / ziwei / qimen / liuyao） |
| **version** | `<vX.Y.Z>` | 能力版本（与契约版本解耦，随变更递增） |
| **status** | `<status>` | 生命周期状态，仅允许：Experimental / Implemented / Contract Candidate / Contract Frozen / Reference Certified / Integration Ready |
| 负责人 | `<owner>` | （可选）领域维护者 |

**填写说明**: status 必须真实反映已完成工件；未完成阶段不得标注为已完成。

---

## Calculation Layer

| 字段 | 值 | 说明 |
|------|----|------|
| **algorithm source** | `<路径>` | 确定性算法实现位置（如 `src/openmetaphysics/domain/qimen/`） |
| **determinism** | `<是/否 + 证据>` | 纯函数、无随机/时钟/IO/LLM；确定性测试证据 |
| **schema** | `<路径>` | 输入/输出 Pydantic 模型 + JSON Schema 导出位置（如 `docs/SCHEMAS.md §3.3`） |
| 测试 | `<路径, 数量>` | （可选）测试文件与用例数 |

**退出标准（Stage 1 → 2）**: 确定性算法可运行 + Schema 定义 + 测试全绿。

---

## Contract Layer

| 字段 | 值 | 说明 |
|------|----|------|
| **contract version** | `<vX.Y.Z>` | Behavior Contract 版本（如 `qimen:behavior:v1.0.0`） |
| **golden vectors** | `<数量 / 路径>` | 规范向量数量与位置（normative fixtures） |
| 冻结规则 | `<清单>` | （可选）冻结规则 ID 清单 |
| 政策裁定 | `<清单>` | （可选）流派分歧裁定记录（如 Qimen D2/D14） |

**退出标准（Stage 2 → 3）**: Freeze Review PASS + 契约版本确立 + 向量机器回归通过。

---

## Reference Layer

| 字段 | 值 | 说明 |
|------|----|------|
| **independent implementation** | `<路径>` | `reference/<domain>/` 自包含实现（禁止导入 `src/`） |
| **verification** | `<结果>` | 契约条款审计（如 14/14 QC）+ 等价测试（如 30/30 逐字节） |
| 认证报告 | `<路径>` | （可选）reference certification report |

**退出标准（Stage 3 → 4）**: 契约审计通过 + 等价测试通过 + 认证工件齐备。

---

## Integration Layer

| 字段 | 值 | 说明 |
|------|----|------|
| **evidence output** | `<说明>` | 确定性观测结果如何供 Evidence/上层消费（信封格式） |
| **consensus compatibility** | `<说明>` | 与 Consensus 层的兼容方式（AgentOutput 信封 / 未来跨域聚合） |

**退出标准（Stage 4）**: 治理注册完成（`CAPABILITY_STATUS.md`）+ 变更政策生效。

---

## 变更政策（模板默认）

达到 Contract Frozen 后，任何规则/算法/向量变更必须执行:

1. ACP 流程（等待人工批准）
2. 契约版本递增
3. Golden Vector 迁移（不可原地修改）
4. Reference Runtime 更新 + 重新认证
