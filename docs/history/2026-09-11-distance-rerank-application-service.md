# 历史记录：医生距离重排 Application Service

日期：2026-09-11

将旧 `/api/recommend/rerank` 的医生/医院查找、真实优先、兼容回退、距离摘要和升序排序移入注入式 `DistanceRerankApplicationService`，保留旧 HTTP 输入与响应。全量测试达到 105/105，characterization、交通与 Safety Evaluation 基线未变化。本次未修改医学规则、推荐权重、交通数据或导航语义。
