# H-20260910-004：建立竞赛版并行前端首个体验切片

- 类型：前端架构、产品体验、记录
- 变更等级：L2
- 结果：完成 Foundation、App Shell、Homepage 和最小 Triage 首步；legacy 默认入口未改变。

## 事件

在既有 Flask/legacy 前端行为基线之上，建立 React/TypeScript/Vite 并行前端。新首页采用 Warm Precision 视觉方向，以自然语言症状输入、Care Path Visual、AI Journey、常州城市智能层和 Trust CTA 组成首屏到长页叙事。为避免硬编码运行指标，新增 `/api/v1/summary` 只读契约，并在 UI 中保留 Region Pack、来源类别和迁移状态。

## 兼容与安全

- 没有修改红旗规则、分诊状态映射、模型输出或推荐排序。
- 新前端不保存或推断医学规则，triage 状态只展示后端返回。
- `/`、legacy `/api/*` 和现有 `/api/v1/*` 继续可回滚使用；Vite 仅作为独立开发入口。
- 医院目录仍标记为 `migration_pending`，没有把来源不完整的数据宣称为正式事实。

## 验证

前端 typecheck、Node boundary tests、Vite build、后端语法检查、86 个 pytest，以及四种目标 viewport 的浏览器运行态检查均通过；完整 follow-up/result parity、Playwright、独立截图 baseline 和 CI frontend job 尚未完成，已登记到进度和评审记录。

## 后续

下一切片从 `/api/v1/triage/followups` 接入一次一个问题的追问，再实现 Routine/Urgent/Emergency 结果组件，并在医学审核与安全门禁通过后推进 route parity。
