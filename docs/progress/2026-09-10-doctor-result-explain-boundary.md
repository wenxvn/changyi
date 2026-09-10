# 2026-09-10 医生结果解释与组装边界

## 目标

抽取普通医生候选的解释生成、分数快照和结果对象组装，保持原有推荐行为和急症安全路径。

## 已完成

- 新增 `backend/app/domain/recommendation/candidate.py`。
- `app.py` 通过兼容导入调用普通医生候选 result builder。
- 解释优先级、四项截断、无信号 fallback、分数精度、惩罚明细和策略字段均保留。
- 急症兜底召回结果仍在 `app.py`，未迁移或改写。

## 验证

- 全量 pytest：49/49 通过。
- API 主 smoke：11/11 通过；另加空输入 400 与未知路径 404 边界检查 2/2 通过。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

医院/医生 candidate 过滤、交通组合、急症兜底 explain 和剩余资源组合仍未完全拆出；`fairness` 对外语义和逐字段 provenance 仍需审查。下一步继续拆 candidate 过滤与交通组合，不修改医学规则或推荐权重。

## 回滚

回退本切片即可恢复医生结果解释和组装在 `app.py` 内联执行，不涉及数据、模型、规则或 API。
