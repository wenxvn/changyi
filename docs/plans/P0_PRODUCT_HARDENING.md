# P0 Product Hardening

更新时间：2026-09-11
状态：已完成（2026-09-11）

本计划把 `1.md` 中的用户可见要求与仓库实现范围对齐。`1.md` 是执行提示词；本文件是仓库内的实施记录，不把提示词原文当作产品需求展示给用户。

## 目标

- 修复已复现的急症漏检和信息不足降级缺口，并扩大可审计的 Safety regression set。
- 恢复重构前已有的医院外部高德导航动作，不引入地图 SDK 或 API key。
- 清理普通产品页面中的比赛、提示词和内部工程语境。
- 按内容状态改善 Triage、Resources、Map、Trust、Profile 的布局，不改变品牌视觉方向或医疗数据口径。
- 用真实 Flask + `frontend/dist` 建立 Playwright 浏览器 smoke、截图、响应和控制台检查。

## 非目标

- 不重新进行后端架构拆分，不新增账号、数据库、LLM、实时交通、实时急诊或新城市。
- 不重采集/静默修复正式数据，不修改 187 个数据质量异常，不恢复旧模板或旧单体前端。
- 不把辅助分流结果包装成诊断、处方、急救替代或临床决策。

## 分项验收

| 项目 | 验收标准 | 回滚点 | 状态 |
| --- | --- | --- | --- |
| P0-1 Safety | 当前正式 set 的 Emergency False Negative 为 0；新增组合、口语、否定和信息不足 case 有明确标签；全量 Python 回归通过 | 只回滚本分项规则、case、测试和安全卡变更 | 已完成 |
| P0-2 Navigation | 推荐医院、医院详情、资源详情和 Map preview 均可生成带坐标/搜索 fallback 的 AMap URI；无 key、无 SDK | 回滚 navigation utility、调用点和相关测试 | 已完成 |
| P0-3 Copy | 普通页面不出现比赛、评委、prompt、Agent 或内部实现字段；技术详情仅在 Trust 折叠区保留必要版本信息 | 回滚文案与静态审计测试，不回滚业务 API | 已完成 |
| P0-4 Layout | Triage 分析后进入上下文侧栏；资源详情不制造失衡的长页；Map 画布与列表节奏合理；关键移动尺寸可用 | 回滚局部 TSX/CSS，不改变 API 和医学逻辑 | 已完成 |
| P0-5 Browser QA | 真实 Flask shell 下覆盖首页、routine、insufficient、emergency、导航链接、核心页面 smoke、console/network 和截图 | 回滚 Playwright 配置、workflow 步骤和测试，不影响运行时产品 | 已完成 |

## 规则变更记录

Safety 变更前已复现：`胸口压榨样疼痛，喘不过气，还一直冒冷汗` 返回 `ROUTINE`；`喘不上来` 返回 `ROUTINE`；`不舒服` 返回 `ROUTINE` 而非 `INSUFFICIENT_INFORMATION`。规则修复必须保留否定、历史和疑问表达的非急症边界，并以运行结果更新安全卡。

## 验证与交付

完成记录：Safety set 扩展至 38 个样例并通过；恢复 AMap URI；完成普通页面文案、Triage 侧栏和移动布局收口；Playwright 在真实 Flask shell 下通过 5 个 smoke tests 并保存桌面/移动截图；全量门禁、状态、风险和记忆已同步。不 push 远端。
