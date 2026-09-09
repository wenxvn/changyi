# 产品规格

## 核心 Journey

```text
症状描述 → 输入清理 → 症状标准化 → 否定识别 → Safety Gate
  → 信息充分性 → 必要追问 → 就医方向 → 科室匹配
  → 医院候选 → 医院排序 → 医生排序 → 交通重排/展示 → 推荐解释
```

## 状态定义

`TriageLevel`：`EMERGENCY`、`URGENT`、`ROUTINE`、`INSUFFICIENT_INFORMATION`。它只表示安全分层。

`VisitScenario`：`FIRST_VISIT`、`SPECIALTY_FOLLOWUP`、`ROUTINE_OUTPATIENT` 等就诊场景。它只影响资源与展示权重，不能覆盖安全门。

## 用户应先看到什么

- `EMERGENCY`：需要优先进行紧急医疗评估、附近急诊和拨打 120 的入口；不展示普通医生排行榜作为第一视觉。
- `URGENT`：尽快到对应专科评估，并提醒继续观察红旗信号。
- `ROUTINE`：普通门诊/社区首诊方向、科室、医院和医生资源参考。
- `INSUFFICIENT_INFORMATION`：明确缺口并提出有限追问，不强行生成疾病结论。

## 解释分层

- 用户层：推荐原因、下一步、距离、数据更新时间和来源徽标。
- 技术层：规则版本、模型版本、排序版本、特征和消融结果。

## 运行边界

无需登录即可完成核心体验；收藏和历史仅是浏览器本地 Demo 数据，不称为患者档案。反馈默认最小收集，不记录完整原始问诊文本。
