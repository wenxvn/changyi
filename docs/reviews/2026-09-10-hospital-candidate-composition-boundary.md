# Review：医院单 candidate 组合边界

日期：2026-09-10

## 第一层：计划对齐

通过。组合函数接收显式输入，既有医院 feature、风险、score、解释和结果字段保持；未调整候选全集、距离、交通样本、权重、rerank 或医学规则。

## 第二层：系统完整性

通过。domain 函数不读取 Flask、全局医院列表、Region repository、模型或缓存；`app.py` 仍负责遍历和准备交通上下文，急症路径仍保留风险惩罚与安全优先排序。

## 第三层：生产准备度

发现问题但不阻塞本切片：医院 candidate 遍历和交通样本生成/cache 仍在 legacy，医院目录逐字段 provenance、`fairness` 语义、v1 route adapter parity 和 Safety 缺口仍开放。

## 结论

本切片可进入医院候选遍历或 API adapter parity；继续以稳定快照、API smoke、Safety Evaluation 和“展示交通不等于实时可达性”检查作为门禁。
