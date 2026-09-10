# 2026-09-10 Frontend Resources

状态：已完成（首版）  
变更等级：L2  
计划：[2026-09-10-frontend-resources.md](../plans/2026-09-10-frontend-resources.md)

## 已完成

- 新增 `api/resources.ts`、资源列表类型和运行时 schema，所有请求经共享 v1 client。
- `/resources` 首屏读取医院索引；切换医生 tab 才读取 2,100 条医生公开资料。
- 支持医院/医生关键词筛选、来源状态、缺失字段空态、医院/医生公开资料预览和地图入口。
- 不显示推荐分、学术成就排序或未经 provenance 确认的官方承诺；地图不冒充附近急诊。
- 同步 architecture、contract、UI registry、status、memory、history 和 review。

## 验证

- `npm run typecheck`：通过。
- `npm run test`：4/4 Node boundary tests 通过。
- `npm run build`：通过；最新产物 gzip 约 JS 78.8 kB、CSS 10.0 kB。
- 后端 `python3 -m py_compile app.py backend/app/api/v1/routes.py`、`node --check static/js/app.js`、pytest：86/86 通过。
- 浏览器：医院索引、关键词筛选、资料预览、医生 tab 按需加载和医生资料预览通过；390×844 `bodyScrollWidth=375`、无横向溢出，console error/warning 为空。

## 未完成与边界

- 资源索引与详情已拆为两个边界；详情由后续 `frontend-resource-details` 计划按选择加载，当前索引仍不代表完整资料。
- 地图列表同步、真实附近急诊资源、Trust evidence API、Playwright/E2E、视觉 baseline、键盘/对比度审查和 CI frontend job 仍待后续。

## 下一步

继续维护资源详情 provenance，配合 F9/F10 和正式急诊路径补齐自动化门禁和 cutover 评审。
