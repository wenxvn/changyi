# 进度：摘要、证据与地图应用服务接缝

日期：2026-09-11  
计划：[2026-09-11-summary-evidence-map-application-services.md](../plans/2026-09-11-summary-evidence-map-application-services.md)  
决策：[ADR-0018](../decisions/0018-summary-evidence-map-application-services.md)

## 已完成

- `backend/app/application/summary.py` 接管 v1 runtime summary 的区域、医院、医生和公交指标组合。
- `EvidenceApplicationService` 固定项目根目录并注入既有 triage evaluator；保留 provisional evidence、报告来源和限制说明。
- `MapViewApplicationService` 注入医院与区域 supplier；保留可选坐标解析、Haversine 距离、急诊标记和“位置示意非导航”提示。
- 三条 v1 路由只保留 HTTP 参数/错误适配和 `_v1_success` envelope。

## 验证

- `.venv/bin/python -m pytest -q`：114 passed。
- `python3 -m py_compile app.py backend/app/application/summary.py backend/app/application/evidence.py backend/app/application/map_view.py`：通过。
- `git diff --check`：通过。

## 未覆盖

- 仍未实现实时急诊可用性、正式附近急诊导航或逐字段 provenance；这些属于后续医学/数据审核范围。
