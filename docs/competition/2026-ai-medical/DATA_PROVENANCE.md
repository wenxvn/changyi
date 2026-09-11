# 数据溯源卡

## 发布原则

每个数据集都必须有 `dataset_id`、区域、来源、来源 URL、许可、采集/验证时间、schema 版本、记录数、SHA-256、隐私级别、脱敏状态、用途和限制。来源或许可不明的字段保持 `null`，不能填“看起来合理”的数字。

## 当前资产盘点

| 数据集 | 当前记录 | 当前状态 | 主要问题 |
| --- | ---: | --- | --- |
| 医院目录（`data/regions/320400/hospitals/catalog.json`） | 21 | `provisional` | 已从组合根外置；公开事实、派生能力和未支持字段分开，逐字段外部 provenance 仍未完成 |
| 医生 JSON（11 个文件） | 2,100 | `public_source_mixed` | 文件结构和来源字段不统一，且 h6 声明总数与实际记录不一致，需按医院拆入 Region Pack |
| 公交线路 | 50 | `public_secondary_masked` | 已有来源描述；时间字段存在异常样本待报告 |
| 公交站点 | 50 | `public_secondary_masked` | 已有来源描述；坐标范围和有效状态需自动检查 |
| 出租车运营样本 | 50 | `derived_masked_sample` | 仅用于统计/可达性原型，不代表实时服务 |
| 骑行站点/车辆 | 50/50 | `derived_masked_sample` | 仅作绿色出行展示，不进入急症排序 |
| 症状疾病 41 类训练集 | 304 行 | `weak_or_synthetic` | 来源与许可有记录，但医学质量和泄漏风险未充分验证 |
| 测试反馈 JSONL | 已移除运行时入口 | `demo_only` | 不再提供写入端点；历史文件若存在也不能扩展到真实用户场景 |

## 质量门

`SOURCE_MOCK` 不得进入主推荐结果。交通、医生和医院数据先通过 `data_validation/validate_datasets.py`，生成 `data_quality_report.json` 和 `data_quality_report.md`；异常只报告，不静默纠正。

## 区域

当前 active pack：`320400 · 常州市`。未来城市包必须独立通过同一 manifest/schema/quality gate 后才可激活。
