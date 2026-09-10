# 前端可信证据契约

日期：2026-09-10  
范围：并行前端只读 Trust Center

## 请求

```text
GET /api/v1/evidence
```

请求经过 `frontend/src/api/client.ts`，返回统一 `{ data, meta, error }` envelope。`data` 由后端读取当前仓库内已提交的评测/质量报告、模型 JSON、Region Pack manifest 和应用配置组装。

## 数据

```json
{
  "disclaimer": "当前为原型阶段离线评估与数据来源摘要，不代表临床验证、官方推荐或诊断结论。",
  "status": "provisional",
  "region": {"code": "320400", "pack_version": "...", "source": {"path": "...", "sha256": "...", "format": "json", "record_count": null, "collections": {}}},
  "versions": {"app": "...", "ranking": "...", "triage_rules": "...", "model": "...", "dataset": "..."},
  "safety": {
    "available": true,
    "schema_version": "...",
    "case_count": 0,
    "red_flag_count": 0,
    "red_flag_recall": 0.0,
    "under_triage_rate": 0.0,
    "over_triage_rate": 0.0,
    "emergency_false_negative": 0.0,
    "insufficient_information_count": 0,
    "insufficient_information_matches": 0,
    "review_required": [],
    "report_source": "...",
    "label": "Safety Evaluation · provisional"
  },
  "model": {
    "available": true,
    "label": "症状模型离线评估",
    "model_type": "...",
    "training_rows": 0,
    "test_rows": 0,
    "class_count": 0,
    "vocabulary_size": 0,
    "top1_accuracy": 0.0,
    "top3_accuracy": 0.0,
    "evaluation_scope": "...",
    "model_source": {"path": "...", "sha256": "...", "format": "json", "record_count": null, "collections": {}},
    "training_data_source": {"path": "...", "sha256": "...", "format": "csv", "record_count": 0, "collections": {}}
  },
  "data_quality": {"available": true, "report_source": "...", "schema_version": "...", "dataset_count": 0, "issue_count": 0, "status": "issues_present"},
  "dataset_manifest": [],
  "limitations": []
}
```

`red_flag_recall`、`under_triage_rate`、`over_triage_rate`、`top1_accuracy` 和 `top3_accuracy` 是评测比例，不能当作临床概率；`emergency_false_negative` 是红旗样例漏检数量，不是百分比。报告缺失时对应证据标记为不可用或 `null`，前端显示“未提供”。`sha256` 是文件指纹，不等于来源许可、内容正确或临床适配。

## 展示安全边界

- Trust Center 必须同时显示 `provisional` 和“不代表临床验证”的文案。
- `review_required` 只作为人工复核清单，不视为发布放行条件。
- 数据质量 `issue_count` 只表示报告登记的问题数量，不改写为临床风险数量。
- 版本和来源用于复现、审查和回滚；不能被解释成官方推荐或模型保证。
