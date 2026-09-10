# Review：医院推荐 feature 边界

日期：2026-09-10

## 第一层：计划对齐

通过。计划中的 feature 模块、兼容导入、测试、快照和记录均完成；没有迁移交通或完整推荐组合。

## 第二层：系统完整性

通过。新模块只接受显式医院/病情/分诊输入，不依赖 Flask、Region、repository 或模型；旧排序调用路径保持可用。后续补齐 feature 直接正/反例后，与 rerank 切片合计 34 个 pytest 和快照通过。

## 第三层：生产准备度

发现问题但不阻塞本切片：feature 使用的医院字段仍缺逐字段 provenance，`fairness` 仍是内部历史语义，完整 candidate/score/rerank pipeline 尚在单体。问题已保留在风险和评分卡。

## 结论

本切片可继续进入完整推荐 pipeline 拆分；下一步以 candidate/feature/score 边界测试和快照比较为门禁。
