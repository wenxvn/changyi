# Review：医生距离重排 Application Service

日期：2026-09-11  
范围：`backend/app/application/recommendation.py`、rerank route、相关测试  
计划：[2026-09-11-distance-rerank-application-service.md](../plans/2026-09-11-distance-rerank-application-service.md)  
决策：[0014-distance-rerank-application-service.md](../decisions/0014-distance-rerank-application-service.md)

## 1. 计划对齐

结论：通过。rerank 的目录查找、距离 read model 和排序已移入 service，旧 HTTP 行为保留。

## 2. 系统完整性

结论：通过。service 不依赖 Flask，不读取文件，不实现医学规则；真实/兼容选择和距离函数显式注入。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] 距离/交通事实语义、整体推荐排序、完整 route parity、provenance 和正式急诊路径仍开放。
- [P1] 直线距离不能作为导航或急救到院保证；前端应继续使用边界文案。
- [P2] 坐标输入仍为 legacy adapter 解析，后续可统一到 versioned location schema。

## 总结

本切片完成距离重排应用边界，不宣称推荐或交通质量得到临床/生产验证。
