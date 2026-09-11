# Review：摘要、证据与地图应用服务接缝

日期：2026-09-11  
范围：`backend/app/application/summary.py`、`evidence.py`、`map_view.py` 及 v1 三条只读路由  
计划：[2026-09-11-summary-evidence-map-application-services.md](../plans/2026-09-11-summary-evidence-map-application-services.md)  
决策：[0018-summary-evidence-map-application-services.md](../decisions/0018-summary-evidence-map-application-services.md)

## 1. 计划对齐

结论：通过。三类只读投影均已从路由内联组合移到显式 application service，既有输入、输出和错误适配保持。

## 2. 系统完整性

结论：通过。service 只读取注入的区域、目录、交通和报告依赖；未复制医学规则、推荐排序或数据加载逻辑。新增 unit tests 覆盖成功、区域 fallback、证据委托和地图急诊标记。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，本切片没有新的 P1 代码阻断。

- [P1] 正式急诊路径、逐字段 provenance、完整 legacy parity、独立 factory、远端 CI 和生产安全仍开放。
- [P2] 地图仍是静态位置示意；距离为直线距离，不是导航或实时可达性。

## 总结

本切片降低了 `app.py` 的只读编排职责，为后续 factory composition 和独立 API 验证建立接缝；不宣称完成医疗或生产发布审核。
