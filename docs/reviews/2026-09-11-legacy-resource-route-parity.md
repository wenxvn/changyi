# Review：旧资源路由收敛到目录 Application Service

日期：2026-09-11  
范围：`backend/app/application/resources.py`、旧资源 routes、resource tests  
计划：[2026-09-11-legacy-resource-route-parity.md](../plans/2026-09-11-legacy-resource-route-parity.md)  
决策：[0010-legacy-resource-route-parity.md](../decisions/0010-legacy-resource-route-parity.md)

## 1. 计划对齐

结论：通过。六类旧资源读路由已复用 service，HTTP 形状和历史选择规则保留。

## 2. 系统完整性

结论：通过。service 不依赖 Flask，不实现医学判断，不读取文件；旧路由只做参数、响应和错误映射。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] 逐字段 provenance、正式资源发布、全部 legacy route parity 和远端 CI 首次运行仍开放。
- [P1] 正式附近急诊路径、Playwright/E2E、视觉/无障碍矩阵仍未完成。
- [P2] 目录仍一次返回当前集合，分页/检索和缓存策略不在本切片。

## 总结

本切片完成了资源路由的低风险边界收敛，可以继续处理其他 legacy adapter；不能宣称旧 API 已完成整体 parity 或资源来源治理。
