# Review：医院 candidate 命中边界

日期：2026-09-10

## 第一层：计划对齐

通过。只移动医院目标科室命中和 strength 回退判断，没有改变候选全集、排序、权重、API 字段或医学规则。

## 第二层：系统完整性

通过。函数只接收显式医院映射和目标科室，复用已抽取的科室关系纯函数，不读取 Flask、全局医院列表、交通数据或模型。

## 第三层：生产准备度

发现问题但不阻塞本切片：医院目录字段 provenance、`fairness` 语义、交通样本生成/cache、v1 route adapter parity 和安全评估缺口仍开放；内部 strength 分数仍需避免对外误解为官方评级。

## 结论

本切片可进入医院 candidate 遍历或 API adapter parity 拆分，继续以候选快照、API smoke 和数据事实语义检查作为门禁。
