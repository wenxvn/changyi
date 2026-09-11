# Review：目录索引与统计 Read Model

日期：2026-09-11  
范围：`backend/app/application/resources.py`、旧目录索引/统计 routes、相关测试  
计划：[2026-09-11-legacy-catalog-read-model.md](../plans/2026-09-11-legacy-catalog-read-model.md)  
决策：[0015-legacy-catalog-read-model.md](../decisions/0015-legacy-catalog-read-model.md)

## 1. 计划对齐

结论：通过。三个只读路由已复用目录 service，统计和索引结果保持。

## 2. 系统完整性

结论：通过。service 不依赖 Flask，不读取文件，不改变推荐或医疗逻辑；数据集合通过 supplier 提供。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] 目录 provenance、数据质量、刷新/版本化和正式发布审核仍开放。
- [P1] 完整 legacy route parity、正式附近急诊路径、E2E/视觉/无障碍矩阵和远端 CI 首次运行仍未完成。
- [P2] 统计仍是内存 read model，不能作为实时运营指标承诺。

## 总结

本切片完成目录索引/统计边界收敛，不宣称数据治理或生产运营统计已完成。
