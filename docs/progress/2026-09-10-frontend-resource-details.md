# 2026-09-10 Frontend Resource Details

状态：首版完成，保留逐字段 provenance 门禁  
变更等级：L2  
计划：[2026-09-10-frontend-resource-details.md](../plans/2026-09-10-frontend-resource-details.md)

## 已完成

- 新增 `backend/app/application/resources.py`，集中维护医院/医生公开字段白名单和详情 provenance read model。
- 新增 `/api/v1/hospitals/<id>`、`/api/v1/doctors/<id>`，统一返回 v1 envelope；未知资源返回 `404 RESOURCE_NOT_FOUND`。
- 医院详情不扩散内部床位、评分和日均接诊字段；医生详情不扩散学术成就和原始抓取链接。
- 资源页选择医院/医生后按 id 加载详情，显示来源类别、状态、更新时间/许可登记状态和安全说明；请求有 loading/error/retry/close 状态。
- 更新 resources contract、frontend architecture、scorecard、status、history、review、UI registry、memory 和迁移计划。

## 验证

- `python3 -m py_compile app.py backend/app/api/v1/routes.py backend/app/application/resources.py`：通过。
- `./.venv/bin/pytest -q`：89 passed；覆盖成功、字段白名单和 `RESOURCE_NOT_FOUND`。
- `npm run typecheck`：通过；`npm run test`：6/6 通过。
- 详情 API smoke：医院/医生成功响应含 provenance；未知医院 404；医生相关医院摘要可用。
- 浏览器 desktop/390×844 运行态：资源详情按选择加载，来源登记可见，详情仍可关闭；未改变地图、Trust 或 Emergency 路径。

## 未完成与边界

- 逐字段来源、许可证、更新时间和正式发布范围仍未登记，当前详情只能标记 migration pending / not recorded。
- 正式附近急诊路径、真实导航、结构化 follow-up answer API、完整 route parity、Playwright/视觉/键盘/对比度门禁仍未完成。

## 回滚

可回退资源详情 application builder、v1 详情路由、前端详情 API/parser/状态和对应文档；不影响旧详情接口、资源索引、地图、Trust、triage 或推荐。
