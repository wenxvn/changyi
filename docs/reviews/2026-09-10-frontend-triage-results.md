# Review：Frontend Triage / Follow-up / Results

日期：2026-09-10  
范围：`frontend/src/api`、`frontend/src/components/medical`、`frontend/src/pages/TriagePage.tsx`、相关样式与契约  
计划：[2026-09-10-frontend-triage-results.md](../plans/2026-09-10-frontend-triage-results.md)

## 1. 计划对齐

结论：通过，首版范围已完成。

- 已接入 triage/followups/recommendations v1 client、一次一个追问和 Routine/Urgent/Emergency 三类结果表达。
- Emergency 短路、医院优先于医生、推荐解释和免责声明符合计划。
- 结构化答案、附近急诊地图和资源详情属于计划内后续，不被当前结果页伪装完成。

## 2. 系统完整性

结论：通过。

- 页面和组件没有直接 `fetch` 或 legacy `window._*` 状态；API 请求集中于 client。
- 状态只由服务端响应驱动；前端没有新增关键词、疾病、红旗或排序规则。
- Emergency 不调用 recommendations，且运行态没有医院路径或医生预览。
- 推荐分、匹配分和 feature 原始值没有进入用户层文案；医院来源/更新时间仍保留不确定性说明。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，但没有阻止当前并行开发的关键回归。

- [P1] Emergency 附近急诊仍是地图建设中入口，需要真实且经过审核的急诊资源接口后才能完成。
- [P1] 还没有 Playwright 核心流程、截图 baseline、keyboard/contrast 矩阵和 CI frontend job。
- [P2] follow-up 仍用补充文本重提，不能提供结构化会话审计；需要后端契约支持后再升级。
- [P2] 医院/医生逐字段 provenance 和详情页仍未完成。

## 总结

本切片可用于本地竞赛演示和继续并行开发；在上述 P1 项完成前，不应切换为默认入口或标记 competition-ready。
