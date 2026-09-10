# ADR-0004：推荐流水线采用显式输入的纯函数边界

- 状态：已接受
- 日期：2026-09-10
- 关联计划：`2026-09-10-recommendation-scoring-boundary`、`2026-09-10-recommendation-feature-boundary`、`2026-09-10-recommendation-rerank-boundary`、`2026-09-10-recommendation-score-composition`

## 背景

`app.py` 同时负责医院/医生候选生成、交通与距离计算、feature、score、rerank 和解释。推荐排序属于 L3 领域逻辑，若直接整体搬迁，容易在没有可定位证据的情况下改变权重、风险惩罚、急症优先级或 API 输出。

## 选项

- 选项 A：一次性把整个推荐函数迁移到独立 service。迁移速度快，但候选、数据访问、医学风险和展示语义同时变化，回滚与差异定位困难。
- 选项 B：按 candidate、feature、score、rerank、explain 逐个建立显式输入的纯函数边界。每步较慢，但可用稳定快照、API smoke 和领域单测确认行为保持。

## 决定

选择选项 B。推荐 domain 先承载无 Web、无全局数据读取和无模型调用的纯函数：共享 scoring、医院 feature、医院 score 组合和医院候选 rerank。候选数据、交通/距离、医院目录和 legacy API 暂由 `app.py` 负责，并通过显式参数或回调注入 domain；不在本 ADR 中修改权重、红旗规则、医学文案或 `fairness` 对外语义。

## 理由

该方案符合 ADR-0003 的渐进式拆分原则，并可直接复用当前稳定 characterization snapshot。急症 rerank 旁路、风险惩罚和 Safety-first public output 都能在每个切片单独回归，不会因架构整理被误当成医学策略升级。

## 影响

- `backend/app/domain/recommendation/` 可独立测试并逐步扩展到 candidate/explain 和医生 score。
- `app.py` 保留兼容私有名称和旧 `/api/*` 行为，短期内仍是 composition shell。
- 交通数据、医院逐字段 provenance、`fairness` 语义和医学规则审核仍是开放风险，不因模块抽取而自动获得可信度结论。

## 验证与回滚

每个切片必须通过全量 pytest、API smoke、相关 Safety Evaluation、Python/JavaScript 检查、数据质量检查和 characterization snapshot；当前快照 SHA-256 为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。若快照、接口或安全门禁出现未解释变化，回退对应切片即可恢复原有 `app.py` 组合路径，不涉及数据和模型回滚。
