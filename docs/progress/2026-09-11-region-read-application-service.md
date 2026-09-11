# 进度：Region Read Application Service

日期：2026-09-11  
计划：[2026-09-11-region-read-application-service.md](../plans/2026-09-11-region-read-application-service.md)  
决策：[ADR-0019](../decisions/0019-region-read-application-service.md)

## 已完成

- 新增 `backend/app/application/regions.py`，只负责活动区域 readiness 和公开摘要读取。
- `create_app` 注册 `changyi.region_read_service`；配置覆盖的 `REGION_ROOT` 仍在请求时生效。
- `/api/v1/ready`、`/api/v1/regions` 改为通过 service 读取；health、状态码、字段和 envelope 保持。

## 验证

- `.venv/bin/python -m pytest -q`：116 passed。
- `python3 -m py_compile backend/app/__init__.py backend/app/api/v1/routes.py backend/app/application/regions.py`：通过。
- v1 ready/regions contract 已随全量测试通过；`git diff --check`：通过。

## 未覆盖

- 未实现跨城市切换、远程 Region Pack、正式数据发布审核或生产部署。
