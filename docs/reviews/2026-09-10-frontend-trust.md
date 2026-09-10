# Review：Frontend Trust Center

日期：2026-09-10  
范围：`backend/app/application/evidence.py`、`/api/v1/evidence`、Evidence schema/API、`frontend/src/pages/TrustPage.tsx`、相关样式与文档  
计划：[2026-09-10-frontend-trust.md](../plans/2026-09-10-frontend-trust.md)

## 1. 计划对齐

结论：通过，首版范围已完成。

- 只读证据服务和 Trust Center 已接通，指标、版本、来源、质量和限制均由 API/仓库报告提供。
- 页面明确显示 provisional、不是临床验证、review_required 和医院/医生来源限制。
- 未修改医学规则、模型文件、推荐排序、legacy 默认入口或旧 API 行为。

## 2. 系统完整性

结论：通过。

- 后端证据服务对质量报告/数据集清单做了结构边界保护；安全评估不可用时返回降级状态，不暴露内部异常类型。
- 前端请求统一经过共享 client，运行时 parser 检查 Evidence 结构；页面没有直接 `fetch` 或 `window._*` 状态。
- 页面不把数据质量问题转成临床风险，不把离线指标转成诊断/疗效/官方推荐，也不让 review_required 充当发布门禁。
- 浏览器 desktop 与 390×844 mobile 已看到真实 API 数据、安全评估区块、数据指纹和限制区块。

## 3. 生产准备度

结论：未达到最终 cutover/competition-ready 门槛，但本切片没有新增 P1 阻断。

- [P1] 安全评估仍有已知边界：当前指标为 Red Flag Recall `0.9231`、Under-triage `0.0769`、Emergency False Negative `1`；需医学审核，不可宣称临床安全。
- [P1] 医院逐字段 provenance、医生公开资料适配、地图/附近急诊尚未具备正式发布契约；资源详情已有 provisional 首版，但仍需逐字段审核。
- [P1] 尚无 Playwright 核心流程、截图 baseline、keyboard/contrast 矩阵和 frontend CI job。
- [P2] 证据页只展示前 8 条 manifest，完整清单仍需通过 API/审查工具读取；当前质量报告有 187 个登记问题。

## 总结

Trust Center 首版可用于本地原型演示和复核，不应替代临床验证、人工审核或发布放行流程；下一切片优先 F9 地图/急诊路径，然后补 E2E、视觉、无障碍和 CI 门禁。
