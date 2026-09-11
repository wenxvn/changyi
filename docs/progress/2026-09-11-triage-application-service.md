# 2026-09-11 Triage Application Service

状态：首版完成，保持 v1/legacy 行为  
变更等级：L3（行为保持的分诊发布编排重构）  
计划：[2026-09-11-triage-application-service.md](../plans/2026-09-11-triage-application-service.md)  
决策：[0007-triage-application-service-boundary.md](../decisions/0007-triage-application-service-boundary.md)

## 已完成

- 新增 `backend/app/application/triage.py`，定义注入式 `TriageApplicationService`。
- v1 triage payload 的现有顺序保持：legacy triage → Safety Gate → Safety-first triage → model prediction/publication → htriage public/publication。
- v1 follow-up projection 移入 service；`app.py` 仅保留依赖组装、request 校验、响应 envelope 和薄兼容 wrapper。
- 没有修改红旗规则、分诊状态、追问规则、模型、推荐排序、URL、状态码或字段契约。

## 验证

- `tests/test_triage_application_service.py`：2 个 service unit 通过，覆盖 Emergency abstain 编排和 follow-up projection。
- `./.venv/bin/pytest -q`：91 passed。
- v1/legacy Emergency contract、Safety-first publication tests 和推荐快照继续通过。
- Python compile、API smoke、`git diff --check` 通过。

## 未完成与边界

- 推荐 application service、结构化 follow-up answer API 和完整 legacy route parity 仍未完成，需独立切片。
- Safety Evaluation 当前仍保留 Red Flag Recall `0.9231`、Under-triage `0.0769`、Emergency False Negative `1`；本切片没有把重构结果当作医学放行。

## 回滚

恢复 `app.py` 内部 triage/follow-up 编排并移除 service、unit test 和对应文档即可；不影响模型、规则、数据和前端。
