# Frontend Triage / Follow-up / Recommendation Contract

2026-10-10核心算法收敛L2：`triage.symptom_tags`已按对象数组解析（`tag/matched_terms/body_system/red_flag_related/source`），兼容旧字符串；`htriage_analysis.department_candidates[].source`只读展示，`population_context/score0`仅人群入口。只消费既有v1响应，不改医学逻辑，见ALGORITHM_WEB_PRESENTATION.md。

2026-10-10追问往返差异（L2只读）：`TriagePage`快照上一轮证据并下发`previousTags/previousDepts/previousDept`，`CurrentUnderstanding`/`TriageResults`仅标注“补充后新增/更新”，不驱动分诊与推荐；首轮无标注。见`ui-registry.md`。

2026-10-10追问槽位联动（L2只读）：`FollowupPrompt`展示`missing_slots[0]`为本题补充目标，文案闭环到证据卡更新；后端零改动，前端21/21、build过。

2026-10-06核心证据分离：department_candidates.source可为population_context，此入口score=0，仅人群适用入口，不代表疾病概率；人口词不进入symptom_tags或disease_candidates。symptom_tags实际为对象数组；当前前端string[]过滤是待接入缺口，后续见ALGORITHM_WEB_PRESENTATION.md。

2026-10-04：asthma_rescue_check三个value为present/none/unknown。未答/unknown/其他非声明值保持INFO/null方向/无普通排序，问题可再确认且居前；原条件不变、同qid替换，不能提交重复qid。present或原文明确个人方案最大救援量后仍不缓解ER；none仍URGENT及时评估。通用red_flag_check none不能清该未知，现有实际呼吸强危险仍优先ER。此为患者自述的辅助确认，不验证药量，不提供用药指令。

2026-10-04复合当前风险：单侧小腿肿痛、排尿疼痛合并腰侧痛/发热可进入URGENT及时评估。其severity_bucket为复合症状/需及时评估，推荐resource_strategy.code=urgent_assessment、expert_enabled=false，普通recommended_doctors=[]、weights_used={}，医院保留目录参考。前端应呈现服务端及时线下说明与ranking_notice，不把它显示成慢病随访/专家号预约，也不宣称实时接诊保证。其他URGENT慢病策略不变，ER/INFO仍优先。

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
