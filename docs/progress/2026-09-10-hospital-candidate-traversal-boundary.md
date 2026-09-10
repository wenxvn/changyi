# 2026-09-10 医院候选遍历边界进度

## 本次完成

- 在 `backend/app/domain/recommendation/candidate.py` 新增 `build_hospital_candidates`，通过显式回调接收距离、可达性、交通访问和单候选组合能力。
- `app.py` 医院推荐入口改为调用该 orchestration 函数，rerank 仍留在兼容入口。
- 保持医院遍历顺序、first_visit/urgent 交通 ranking policy、结果字段和快照行为。

## 验证

- 目标回归：35/35 通过。
- 全量 pytest、Safety Eval、API smoke、编译、数据校验、行为快照和 `git diff --check` 已通过：pytest 85/85，API smoke 13/13，数据扫描 27 个文件、187 个异常，快照 SHA-256 为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

急症候选整体遍历/排序、交通数据加载与刷新策略、应用 service、完整 API route parity、医院 provenance、前端模块化和 Safety Evaluation review_required 项仍未完成；本切片未改变医学规则和急症安全策略。

## 回滚

恢复 `app.py` 医院逐候选循环并移除 domain orchestration 函数、测试和记录即可。
