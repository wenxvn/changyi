# 2026-09-10 交通样本索引边界进度

## 本次完成

- 在 `backend/app/domain/recommendation/traffic.py` 新增 `index_traffic_rows`，只负责将已计算的 station/taxi/bike 样本行按 `hospital_id` 索引。
- `app.py` 继续负责样本加载、交通特征计算和 `_TRANSIT_ACCESS_CACHE` 生命周期，只调用索引函数。
- 锁定空输入、原始行对象保留和重复 ID 后者覆盖行为。

## 验证

- 目标测试：15/15 通过。
- 全量 pytest：61/61 通过。
- API smoke：13/13 通过（含 400/404 边界）。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

医院 candidate 遍历、交通样本生成/map 之外的缓存治理、API route adapter parity、医院逐字段 provenance 和前端模块化仍未完成；本切片没有改变交通样本口径，也没有把交通样本提升为实时事实。

## 回滚

恢复 `app.py` 中三张 map 的内联字典推导并移除索引函数及对应测试/记录即可；不影响交通特征和推荐 scoring 函数。
