# Inquiry Dataset Schema（未来采集用）

本目录只定义 schema / 校验器 / **synthetic_example**，不包含真实患者多轮数据。

## 顶层字段

- `schema_version`: `inquiry-dataset/v1`
- `source`: `synthetic_example` | `sandbox_log` | `opted_in_clinic` | `public_deidentified`
- `annotation_status`: `unlabeled` | `weak` | `expert_reviewed` | `rejected`
- `sessions[]`

## Session 字段

| 字段 | 说明 |
| --- | --- |
| `session_id` | 匿名会话 ID，禁止可逆标识 |
| `initial_text` | 用户初始自由文本（须脱敏） |
| `extracted_present_symptoms` | 标准症状码 present |
| `extracted_absent_symptoms` | 标准症状码 absent |
| `safety_state` | EMERGENCY / URGENT / ROUTINE / INSUFFICIENT_INFORMATION |
| `turns[]` | 追问轮次 |
| `department_label` | 标注科室（可空） |
| `final_route` | 最终路由（可空） |

## Turn 字段

`turn_index`, `question_id`, `question_text`, `answer` ∈ {yes,no,unsure,present,absent,unknown}

## 数据质量与匿名化约束

1. 禁止真实姓名、手机号、身份证、邮箱、住址门牌、病历号。
2. `source=synthetic_example` 的样本永远不得并入真实评测集。
3. 红旗相关否定解析不得直接改写生产 Safety；只用于研究标注。
4. 需保留 `annotation_status`；`expert_reviewed` 才可进入训练/校准主表。
5. 入库前运行 `validate_dataset`；失败样本进入隔离区，不得静默丢弃标签错误。
