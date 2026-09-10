# 2026-09-10 医院候选 rerank 边界

## 目标

完成 P2-S3 第三小步：抽取医院候选的基础排序、区域多样性和普通场景三甲数量约束，保持急症旁路和推荐快照行为不变。

## 已完成

- 新增 `backend/app/domain/recommendation/pipeline.py`，只接受候选列表、triage level、Top-N 和区域解析回调。
- `app.py` 的 legacy `recommend` 改为注入 `_hospital_district`；候选生成、feature 计算和权重仍留在 legacy。
- 新增 routine/urgent 约束测试，以及 emergency bypass 测试。

## 验证

- 全量 pytest：34/34 通过。
- API smoke：11/11 通过。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

医院/医生 candidate、score、explain 和交通 feature 仍未完全拆出；`fairness` 对外语义和逐字段 provenance 仍需审查。下一步继续拆 candidate/score 组合，不修改医学规则或推荐权重。

## 回滚

回退本切片即可恢复 `recommend` 内联 rerank，不涉及数据、模型、规则或 API。
