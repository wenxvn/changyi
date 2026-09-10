# H-20260910-005：完成并行前端问诊与结果首版

- 类型：前端功能、Safety UX、记录
- 变更等级：L2
- 结果：Triage / Follow-up / Routine / Urgent / Emergency 首版完成；legacy 默认入口保持不变。

## 事件

将并行前端从首页输入推进到问诊工作区。用户输入先经过 v1 triage，再由 follow-up 契约提供一次一个问题的补充；跳过追问后才读取 v1 recommendations。结果展示遵循“行动 → 科室 → 医院路径 → 医生预览 → 解释”的顺序。

## 安全与兼容

- Emergency 结果单独渲染，保留服务端风险信号，提供 `tel:120` 入口，不请求或展示普通推荐。
- Routine/Urgent 只呈现服务端返回状态和解释，不将推荐分显示为概率，不把科室/医院匹配包装为诊断。
- `ROUTINE + followup.needed=true` 按现有后端事实原样保留，同时给出补充信息入口。
- 未修改红旗规则、Safety Gate、模型、推荐排序或 legacy API 行为。

## 验证

前端 typecheck、3 个 boundary tests、Vite build、86 个 pytest，以及桌面/移动端问诊、追问、资源路径和急症短路运行态检查通过；完整结构化 follow-up、附近急诊地图和自动化 E2E 尚未完成。

## 后续

接入资源、地图和 Trust Center 的真实 v1 契约，并在所有核心流程通过 E2E、视觉、移动和无障碍门禁后再讨论默认入口切换。
