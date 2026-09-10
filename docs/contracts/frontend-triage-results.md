# Frontend Triage / Follow-up / Recommendation Contract

状态：v1 draft  
变更等级：L2（消费既有 v1 响应；不改变医学逻辑）

## Shared request

`POST /api/v1/triage`、`POST /api/v1/triage/followups` 和 `POST /api/v1/recommendations` 当前共享 `RecommendationRequest`：

```json
{
  "condition": "用户用自然语言描述的症状和补充信息",
  "scenario": "common",
  "district": "可选区域"
}
```

`condition` 必须是非空字符串，最长 2000 字符；前端不得添加未声明字段。

## Triage response

统一 envelope 为 `{data, meta, error}`。`data` 至少包含：

- `condition`
- `triage_status`：`EMERGENCY`、`URGENT`、`ROUTINE` 或 `INSUFFICIENT_INFORMATION`
- `matched_department`：服务端返回的就医方向，可为空
- `triage.followup`：`needed`、`confidence`、`missing_slots`、`questions`
- `triage.red_flag_tags` / `triage.reasons`：仅展示服务端已发布的安全说明

前端只消费这些字段，不根据文本重新计算状态。

## Follow-up response

`POST /api/v1/triage/followups` 返回：

- `condition`
- `triage_status`
- `matched_department`
- `followup.questions[]`：每项含 `id`、`question`、`options`、可选 `reason`

当前接口不接收结构化答案。前端一次展示一项问题，将用户选择附加为补充描述，再次提交到 v1；这只是输入编排，不是医学判断。

## Recommendation response

`POST /api/v1/recommendations` 返回：

- `recommended_hospitals[]`：医院对象、距离、服务端 explanations 和交通摘要
- `recommended_doctors[]`：医生对象、服务端 reasons 和就诊路径
- `resource_strategy`：服务端的路径和资源策略说明
- `data_source` / `effective_scenario`

Routine/Urgent 页面先展示医院路径，再展示少量公开医生预览。`composite_score`、`match_score` 和 feature 原始值仅用于后端排序，不在用户层展示为概率或医疗效果。

## Safety rules for consumers

- `EMERGENCY`：只显示安全行动、120 入口、服务端风险说明和附近急诊建设中入口；不请求或展示普通推荐榜单。
- `URGENT`：强调尽快专业评估；若出现危险信号，以急诊建议为先。
- `ROUTINE`：不表示诊断成立，只表示当前返回状态允许继续了解就医路径。
- `INSUFFICIENT_INFORMATION` 或 `followup.needed=true`：优先补充信息；既有 legacy 可能返回 `ROUTINE + followup.needed=true`，前端不得擅自改写状态。
- API 错误、模型不可用、空列表和超时必须进入明确降级 UI，不伪造成功结果。
