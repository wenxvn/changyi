# 计划：抽取交通 feature 与可达性 score 边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成
- 关联 ADR：`docs/decisions/0004-recommendation-domain-boundaries.md`

## 目标

将医院交通样本摘要和医院可达性 score 的纯计算移入推荐 domain，明确“交通展示字段”和“参与排序字段”的边界，保持急症/较重场景的距离优先策略。

## 非目标

- 不改变公交、出租车、骑行数据、样本口径、距离公式、推荐权重或 API 字段。
- 不迁移交通数据加载、医院全局列表、缓存、repository、路由或前端渲染。
- 不把交通样本推断包装为实时路况、医疗事实或到院保障。

## 当前基线

- `_hospital_traffic_access` 和 `_access_score` 仍在 `app.py`，同时包含样本摘要、排序参与字段和分诊场景分支。
- 稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 方案与边界

- 新增 `backend/app/domain/recommendation/traffic.py`，只接受显式 station/taxi/bike 摘要、距离和 triage level。
- `app.py` 保留交通样本 map/cache 和医院 ID 查找，仅把 payload 计算与可达性 score 交给 domain。
- 通过展示字段、急症旁路、普通场景交通融合、全量测试和快照验证行为保持。

## 原子步骤

- [x] 建立交通 feature/score helper 并接入 legacy 推荐。
- [x] 新增展示字段、距离优先和普通交通融合正/反例测试。
- [x] 运行全量测试、API smoke、快照、静态检查和数据质量检查。
- [x] 更新架构、评分卡、风险、进度、历史和 review。

## 验收标准

- 推荐稳定快照哈希不变，legacy/v1 字段和排序不变。
- 交通 domain 不依赖 Web、数据加载、医院全局列表或模型。
- `bike_display_note` 仍明确不参与医疗推荐排序；急症/较重场景仍按距离优先。

## 回滚

回退本切片即可恢复交通摘要和可达性 score 在 `app.py` 内联执行，不涉及数据、模型、规则或 API。

## 验证结果

- 全量 pytest：56/56 通过。
- API smoke：13/13 通过；Safety Evaluation Set：16 个 case，既有 baseline 保持。
- 推荐 characterization snapshot 哈希仍为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`；Python compile、Node check、数据质量和 `git diff --check` 通过。
- `bike_display_note` 保持“共享骑行仅用于绿色出行展示，不参与医疗推荐排序”；急症/较重场景仍忽略公交/出租车排序权重。
