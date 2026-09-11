# 常医重构路线图

状态：已完成（2026-09-11）

本路线图的目标是从 Flask 单体 + legacy 浏览器界面渐进收敛到可验证的分层后端和 React 正式前端。实施原则始终是：先建立 characterization，再移动单一边界；保持医学、安全、模型、排序和数据行为；每个切片可回滚。

## 已完成结果

- 建立 `backend/app/api/v1`、application、domain、infrastructure、Region Pack、repositories、model adapter 和质量门禁。
- 抽取 triage、Safety-first publication、recommendation、resource catalog、summary、evidence、map 和 region read 边界。
- React/TypeScript/Vite 前端覆盖首页、分诊/追问/结果、资源/详情、地图、Trust、Profile/History、键盘和 reduced-motion 语义。
- Flask 现在提供 `frontend/dist`；正式前端只调用 `/api/v1/*`，SPA 路由支持刷新。
- 删除旧 `/api/*` 路由、legacy adapter、旧模板/JS/CSS、无用 wrapper、测试反馈写入、备份图片、根 fallback 数据和无用二进制。
- 保留并验证既有 Safety baseline、数据质量登记和推荐/分诊 characterization；没有修改医学行为。

## 长期规则

新需求先读 `AGENTS.md`、`docs/status/current.md`、`docs/architecture/current-state.md` 和风险登记。重大架构变化写 ADR；医学/安全行为变化必须追加 L3 风险、评估和领域审核；生产化变化必须追加 L4 评审。

## 后续入口

未在重构中实现的产品和安全事项统一见 [`docs/POST_REFACTOR_BACKLOG.md`](../POST_REFACTOR_BACKLOG.md)。
