# Review：Frontend Foundation / App Shell / Homepage

日期：2026-09-10  
范围：`frontend/`、`/api/v1/summary`、相关迁移文档与 UI registry  
计划：[2026-09-10-frontend-migration-foundation-home.md](../plans/2026-09-10-frontend-migration-foundation-home.md)

## 1. 计划对齐

结论：通过。

- Foundation、App Shell、Homepage、城市摘要契约和最小 Triage 首步均已落地。
- 旧 `/`、legacy API 和 v1 兼容边界未切换，符合计划中的 rollback 约束。
- 完整追问、结果页、Emergency 独立页面、资源/地图/Trust 详情明确保留为后续切片，没有在本次重构中伪装完成。

## 2. 系统完整性

结论：通过，但存在已登记的测试能力缺口。

- API 请求经过单一 client；页面组件未直接调用 `fetch`，未依赖 `window._*` 全局状态。
- summary 指标来自运行数据，响应携带来源和迁移状态；前端未复制医学规则。
- 响应式布局、语义控件、label、focus-visible 和 reduced-motion 已实现；运行态 AX 树、移动导航和 Journey 交互已检查。
- 当前只有 Node boundary tests；Vitest/Testing Library/Playwright 尚未加入，不能把本切片标记为完整自动化测试覆盖。

## 3. 生产准备度

结论：未达到切换默认入口的门槛；这是计划内状态，不是本切片失败。

- 默认 legacy 入口和回滚路径仍可用。
- 需要完成完整 triage/follow-up/result route parity、Safety UX 矩阵、Emergency 首屏核验、截图 baseline、keyboard/contrast 审查和 CI frontend job。
- 医院目录逐字段 provenance、许可证和更新时间仍待补全；UI 继续显示 `migration_pending`。

## 问题清单

1. P1：完整追问、四态结果与 Emergency 独立安全首屏尚未实现；切换入口前必须完成。
2. P1：Playwright、视觉 baseline、keyboard/contrast 和 CI frontend job 尚未建立；当前仅有运行态人工证据与 Node boundary test。
3. P2：医院目录来源元数据尚不完整；正式发布前需完成数据治理与复核。

未发现阻止本切片继续并行开发的关键回归或安全问题。
