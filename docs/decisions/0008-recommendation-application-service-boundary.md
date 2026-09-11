# ADR-0008：以 Application Service 统一推荐结果编排

状态：已接受  
日期：2026-09-11  
范围：`backend/app/application/recommendation.py` 与 legacy/v1 recommendation adapters

## 背景

推荐入口已经拆出多个 domain candidate、feature、score、rerank 和 traffic seam，但最终 triage、资源策略、医院/医生调用、版本权重和公开 payload 仍集中在 `app.py`。这使应用层责任不清，也增加了 legacy 与 v1 迁移时误改排序的风险。

## 决策

- 新 service 接受已解析的 context，通过注入函数编排既有推荐能力；它不负责请求解析、数据访问、医学判断或排序算法。
- legacy/v1 继续共享 service，但由 adapter 决定是否 strict parse、医生 top-n、enhanced 和 Safety-first publication 参数。
- service 的输出字段与调用顺序由推荐快照、API contract 和 Emergency Safety-first tests 保护；任何权重、候选资格或规则变更必须另立 L3 评审。

## 影响

正向影响：推荐编排可独立测试，route adapter 变薄，未来可逐步替换 legacy implementation。代价：短期保留 app composition root 和旧入口，service 仍通过注入的现有函数工作。

## 未决事项

交通数据新鲜度/缓存刷新、急症整体排序、逐字段资源 provenance 和完整 route parity 仍需单独计划；不得借本 ADR 改变业务口径。
