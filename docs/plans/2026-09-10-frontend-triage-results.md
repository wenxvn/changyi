# 常医智导前端迁移计划：Triage、Follow-up 与四态结果

状态：进行中  
日期：2026-09-10  
变更等级：L2（前端状态边界、既有 v1 API 接入和安全 UI 展示；不改变医学规则、模型或推荐排序）

## 目标

在并行 `frontend/` 中完成可演示的 Triage Workspace、一次一个问题的 follow-up，以及 Routine/Urgent/Emergency 三种独立结果组件。所有状态、科室、追问、推荐医院和医生均来自 `/api/v1`；Emergency 只展示安全行动和附近急诊入口，不调用普通资源推荐。

## 非目标

- 不修改 `analyze_medical_triage`、红旗关键词、Safety Gate、模型或推荐权重。
- 不把前端的 `followup.needed` 重新命名为医学诊断；页面只说明“系统建议补足信息”。
- 不新增结构化医疗答案 API；本切片使用既有 v1 契约，将用户选择以补充描述提交回后端。
- 不切换 legacy `/`，不删除旧路由，不接入真实定位、120 外部呼叫服务或第三方地图。

## 关键决策

- **状态真源**：`triage_status`、`matched_department`、`followup` 和推荐对象都只从后端响应读取。
- **追问推进**：一次显示一个问题；选项点击后把问题/答案作为用户补充文本重新提交，保留原始描述和当前上下文。
- **安全短路**：`EMERGENCY` 只进入 EmergencyResult；不请求 `/api/v1/recommendations`，不展示评分、医生榜单或普通路径。
- **信息不足**：既有 legacy 数据可能返回 `ROUTINE + followup.needed=true`；UI 显示“当前安全状态由 API 返回，同时建议补充信息”，不擅自把状态改成 `INSUFFICIENT_INFORMATION`。
- **推荐解释**：用户层展示后端已返回的 explanations/reasons；不展示 feature 原始小数，不把推荐分数称为诊断概率。

## 实施步骤

1. 扩展前端 API 类型、运行时 schema 和 `triage.ts`，接入 followups/recommendations。
2. 抽取可复用的 Follow-up Prompt、Current Understanding 和 Recommendation Preview 组件。
3. 重构 TriagePage 为输入、后端状态、一次一个追问和重试状态机。
4. 实现 RoutineResult、UrgentResult、EmergencyResult；Emergency 使用高对比低动效布局和 `tel:120` 入口。
5. 增加 Node boundary tests 和后端 API smoke，覆盖 routine、follow-up、emergency short-circuit、invalid input 和 recommendation error。
6. 在四个 viewport 检查输入、追问、结果、空态、错误态、移动层级和 console/network；更新 UI registry、进度、历史、scorecard 和 review。

## 验收标准

- 首页提交后进入 Triage Workspace；后端状态和科室可见。
- 有追问时一次只显示一个问题，选项可重新提交，急症不显示追问。
- Emergency 结果首屏包含状态标题、紧急评估提示、`拨打 120` 和附近急诊入口；无普通推荐排序。
- Routine/Urgent 结果分别强调普通门诊路径与尽快评估；推荐医院优先于医生，并展示来源/辅助免责声明。
- API 网络失败、模型不可用或推荐失败均有明确降级文案，不显示伪造成功结果。
- legacy 默认入口、旧 API、Safety Evaluation 和推荐快照不变。

## 回滚

回退本计划新增的 frontend API/页面/组件/文档即可；不影响 Flask 默认 `/` 和现有后端接口。
