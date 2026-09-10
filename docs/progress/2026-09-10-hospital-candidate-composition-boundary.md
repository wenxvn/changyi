# 2026-09-10 医院 candidate 组合边界进度

## 本次完成

- 在 `backend/app/domain/recommendation/candidate.py` 新增 `compose_hospital_candidate`，组合显式医院、病情、目标科室、triage、距离、可达性、交通和权重输入。
- `app.py` 的医院循环保留候选遍历、距离、交通样本和缓存上下文准备，单候选 feature、风险惩罚、score、解释和结果组装已委托 domain。
- 急症医院能力惩罚、交通权重禁用标记、科室命中和结果字段均增加回归覆盖。

## 验证

- 目标测试：31/31 通过。
- 全量 pytest：66/66 通过。
- API smoke：13/13 通过（含 400/404 边界）。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

医院全量 candidate 遍历、交通样本生成与 cache 生命周期、API route adapter parity、医院逐字段 provenance 和前端模块化仍未完成；Safety Evaluation 已知 review_required 项仍需医学审核。

## 回滚

恢复 `app.py` 医院循环中的 feature/score/result 组合代码并移除 `compose_hospital_candidate` 及对应测试/记录即可；不影响已完成的纯函数边界。
