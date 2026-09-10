# 2026-09-10 医院 candidate 结果组装边界

## 目标

抽取医院候选的稳定结果对象组装，保持医院遍历、距离、交通、feature、score 和 rerank 行为不变。

## 已完成

- 在 `backend/app/domain/recommendation/candidate.py` 新增 `build_hospital_recommendation_result`。
- `app.py` 继续负责医院遍历、交通样本查找、feature/score 计算和 rerank，只调用 result builder。
- 结果字段、分数精度、医院/feature/交通/权重/解释对象保留测试已加入。

## 验证

- 全量 pytest：58/58 通过。
- API 主 smoke：11/11 通过；另加空输入 400 与未知路径 404 边界检查 2/2 通过。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

医院 candidate 遍历、交通样本 map/cache、急症兜底 explain 和 API route adapter parity 仍未完全拆出；`fairness` 对外语义和逐字段 provenance 仍需审查。

## 回滚

回退本切片即可恢复医院 candidate 结果组装在 `app.py` 内联执行。
