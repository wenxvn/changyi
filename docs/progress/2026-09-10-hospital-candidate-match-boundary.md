# 2026-09-10 医院 candidate 命中边界进度

## 本次完成

- 在 `backend/app/domain/recommendation/candidates.py` 新增 `resolve_hospital_candidate_match`。
- `app.py` 继续遍历全部医院并计算交通、feature、score，只将目标科室匹配和 `strength_score` 回退判定委托给纯函数。
- 保持精确强项分数、已列出科室 `75`、相关科室 `70`、无命中 `50` 和匹配科室字段行为不变。

## 验证

- 目标测试：19/19 通过。
- 全量 pytest：64/64 通过。
- API smoke：13/13 通过（含 400/404 边界）。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

医院全量 candidate 遍历、交通样本生成与 cache 生命周期、API route adapter parity、医院逐字段 provenance 和前端模块化仍未完成；本切片没有改变医院候选全集或排序策略。

## 回滚

恢复 `app.py` 中的医院匹配分支并移除 domain 函数及对应测试/记录即可；不影响其他 candidate、feature、score 和 traffic 边界。
