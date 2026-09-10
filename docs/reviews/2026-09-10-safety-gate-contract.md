# Review：Safety Gate 状态契约与评估基线

日期：2026-09-10

## 第一层：计划对齐

通过。已建立四态状态枚举、Safety Gate decision、legacy 适配、16-case 评估集和 CI 入口；没有把 `VisitScenario` 混入 `TriageStatus`，也没有修改医学规则或模型。

## 第二层：系统完整性

通过。domain 模块不依赖 Flask、数据仓库或模型；v1 状态映射仍保持原字符串；21 个 pytest、11 项 API smoke、Safety Evaluation、py_compile、Node check、数据扫描和快照检查通过。

## 第三层：生产准备度与安全

发现问题但不阻塞契约切片：评估基线有 1 个 Emergency False Negative，信息不足样例 `不舒服` 当前观察为 `ROUTINE`。case 标签与 `review_required` 状态已显式记录，不能把 0.9231 Recall 当作发布达标，也不能把评估集替代医学审核。

## 结论

状态契约和评估入口可继续保留；下一步优先拆分推荐 pipeline，同时保持 Safety Gate 在普通推荐之前的架构位置。规则修复必须走独立 L3 评审。
