# 2026-09-10 医院综合 score 组合边界

## 目标

完成 P2-S3 下一小步：抽取医院 feature 的权重组合、风险惩罚和 feature snapshot 组装，保持推荐行为不变。

## 已完成

- 在 `backend/app/domain/recommendation/scoring.py` 新增 `score_hospital_candidate` 纯函数。
- `app.py` 保留候选循环和输入准备，改为通过兼容导入调用 score helper。
- 新增权重组合、风险惩罚、上/下界裁剪和交通展示字典保留测试。

## 验证

- 全量 pytest：37/37 通过。
- API smoke：11/11 通过。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

医院/医生 candidate、explain、医生 score 和交通 feature 仍未完全拆出；`fairness` 对外语义和逐字段 provenance 仍需审查。下一步继续拆 candidate/explain 组合，不修改医学规则或推荐权重。

## 回滚

回退本切片即可恢复 `recommend` 内联 score 组合，不涉及数据、模型、规则或 API。
