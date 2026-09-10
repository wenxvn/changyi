# Review：医院候选 rerank 边界

日期：2026-09-10

## 第一层：计划对齐

通过。计划中的 rerank helper、legacy 注入、routine/urgent 约束测试、急症旁路、快照和记录均完成；没有调整权重、阈值、候选数据或 API 字段。

## 第二层：系统完整性

通过。新模块不依赖 Flask、医院全局列表、Region repository 或模型；区域解析通过显式回调注入。`recommend` 的候选生成与 feature 计算仍在原边界内，快照保持不变。

## 第三层：生产准备度

发现问题但不阻塞本切片：完整 candidate/score/explain 组合、交通数据边界、医院目录 provenance 和 `fairness` 语义仍未完成审查；GitHub Actions 远端首次运行也待推送后确认。问题已保留在当前状态、评分卡和风险登记。

## 结论

本切片可进入后续 candidate/score 拆分；继续以稳定快照、API smoke 和急症旁路测试作为回归门禁。
