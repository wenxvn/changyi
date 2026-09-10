# 2026-09-10 Frontend Triage / Follow-up / Results

状态：已完成（首版）  
变更等级：L2  
计划：[2026-09-10-frontend-triage-results.md](../plans/2026-09-10-frontend-triage-results.md)

## 目标

在并行前端中把首页输入推进到可演示的 Triage Workspace，支持一次一个追问，并为 Routine/Urgent/Emergency 建立不同的结果表达。

## 已完成

- 扩展 API 类型和运行时校验，接入 `/api/v1/triage/followups` 与 `/api/v1/recommendations`。
- 创建 `CurrentUnderstanding`、`FollowupPrompt` 和 `TriageResults`，将输入、服务端状态、追问、资源路径和安全结果拆开。
- 追问一次只显示一个问题；选项或短文本会作为补充描述重新提交既有 v1 接口，当前不伪造结构化答案契约。
- Routine/Urgent 先展示医院路径，再展示少量公开医生预览；推荐解释来自服务端，未展示推荐分或 feature 原始值。
- Emergency 独立显示高风险、服务端返回的风险信号、120 电话入口和明确免责声明；不请求普通推荐，不渲染医院/医生排行榜。
- 增加错误、loading、空列表、跳过追问和模型不可用文案边界，并同步 architecture、contract、UI registry、status、history 和 review。

## 验证

- `npm run typecheck`：通过。
- `npm run test`：3/3 Node boundary tests 通过。
- `npm run build`：通过；当前产物 gzip 约 JS 75.9 kB、CSS 8.7 kB。
- 后端现有全量 pytest：86/86 通过；triage/followups/recommendations API 运行态样例已核对。
- 浏览器：追问 STEP 1/8 → STEP 2/8、跳过后加载医院/医生路径、Urgent 结果和 Emergency 安全短路均通过；390×844 与 1440×900 结果布局检查通过，console error/warning 为空。

## 未完成与边界

- 当前 follow-up API 不支持结构化答案，前端采用补充文本重提；若要保留答案对象、会话 id 或服务端多轮状态，需要另立 API 契约。
- Emergency 的“附近急诊”按钮目前明确标记为建设中并进入地图空态；本切片没有调用普通推荐接口来代替急诊服务。
- 医院详情、医生详情、真实地图同步、Trust evidence API、Playwright 和 CI 前端 job 仍待后续切片。
- 现有 backend 仍可能返回 `ROUTINE + followup.needed=true`；前端展示“建议补足信息”但不擅自改写 `triage_status`。

## 下一步

实现 F7/F8/F9/F10：资源搜索与详情、地图列表同步和可信 AI 证据页，再补完整 E2E、截图 baseline、无障碍审查和 cutover 门禁。
