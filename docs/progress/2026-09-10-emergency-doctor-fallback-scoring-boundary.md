# 2026-09-10 急症医生兜底评分边界进度

## 本次完成

- 在 `backend/app/domain/recommendation/candidate.py` 新增 `score_emergency_doctor_fallback`。
- `app.py` 继续负责急诊医院候选筛选、距离准备和排序；急症兜底评分公式改为调用显式 domain 函数。
- 锁定主任/副主任/主治/其他职称分值、手术经验缺省值、医院质量、可及性和优先级加权行为。

## 验证

- 目标测试：21/21 通过。
- 全量 pytest：83/83 通过。
- API smoke：13/13 通过（含 400/404 边界）。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

急症候选筛选与整体遍历、完整应用服务层、API route parity、医院 provenance、前端模块化和 Safety Evaluation review_required 项仍未完成；本切片未改变医学规则和急症安全策略。

## 回滚

恢复 `app.py` 急症兜底内联评分计算并移除 domain 函数/测试/记录即可；不影响普通医生评分和医院推荐。
