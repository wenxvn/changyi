# 2026-09-10 急症候选资格边界进度

## 本次完成

- 在 `backend/app/domain/recommendation/candidates.py` 新增 `hospital_supports_emergency_fallback`。
- `app.py` 急症医生兜底循环改为调用该纯判断函数；医院查找、交通计算、评分、结果组装和排序仍由兼容入口负责。
- 锁定 `emergency=True`、`False`、字段缺失和医院为空四种边界行为。

## 验证

- 目标回归：31/31 通过。
- 全量门禁将在记录收尾前复跑；应覆盖 pytest、Safety Eval、API smoke、编译、数据校验和行为快照。

## 未完成与下一步

急症候选遍历、普通医院候选遍历、应用 service、完整 API route parity、医院 provenance、前端模块化和 Safety Evaluation review_required 项仍未完成；本切片未改变医学规则和急症安全策略。

## 回滚

恢复 `app.py` 的 `hospital.get("emergency")` 内联判断并移除 domain 函数、测试和记录即可。
