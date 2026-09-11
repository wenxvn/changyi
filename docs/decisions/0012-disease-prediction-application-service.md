# ADR-0012：以 Application Service 编排疾病预测接口

状态：已接受  
日期：2026-09-11  
范围：`backend/app/application/prediction.py` 与 `/api/predict-disease`

## 背景

旧 prediction handler 同时选择请求字段、调用本地模型、判断 unavailable/empty 和生成详情症状标签。这样 HTTP 层与模型适配边界混杂，也让模型不可用的状态契约难以独立测试。

## 决定

- 新增 `DiseasePredictionApplicationService`，注入现有 prediction 和 standard-tag helper，只负责编排与产生 `DiseasePredictionResult`。
- `app.py` 继续负责 request 读取、空输入 400、available/empty 状态码和旧 JSON 字段。
- 不改变推理函数、模型版本、结果文案和任何 Safety-first 发布策略；模型结果不被表述为诊断。

## 影响

正向影响：模型 endpoint 的 unavailable/empty/detail 分支可在无 Flask 环境中测试，后续模型 adapter 迁移有明确边界。

代价：模型和症状标签实现仍在 legacy composition root，低置信度/数据质量和医学审核仍是开放风险。

## 回滚

恢复原 prediction handler 内的调用与 enrichment 即可，不涉及数据或模型回滚。
