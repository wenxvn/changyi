# 2026-09-10 交通样本计算边界进度

## 本次完成

- 在 `backend/app/domain/recommendation/traffic.py` 新增公交站、出租车、自行车站点和车辆分布四类样本计算函数。
- `app.py` 的数据加载函数继续提供样本集合和距离函数，医院交通样本计算已委托 domain；缓存与 `_bus_route_stats` 汇总职责保持不变。
- 测试覆盖距离阈值、分档分数、缺失坐标、空样本、平均值、排序和自行车展示字段。

## 验证

- 目标测试：29/29 通过。
- 全量 pytest：78/78 通过。
- API smoke：13/13 通过（含 400/404 边界）。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

交通缓存失效/生命周期、医院 candidate 遍历、API 应用服务层、医院逐字段 provenance、前端模块化和 Safety Evaluation 已知 review_required 项仍未完成；交通样本仍不是实时路况。

## 回滚

恢复 `app.py` 中四类交通样本循环并移除 domain 函数及对应测试/记录即可；不影响交通 payload 和推荐 score 合同。
