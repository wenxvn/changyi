# 进度：Frontend Map

日期：2026-09-10  
状态：首版完成，保留正式地图/急诊门禁

## 已完成

- 新增 `backend/app/application/map_view.py`，从现有医院坐标构建只读 map payload，包含 marker 类型、轻量投影、来源和可选直线距离。
- 新增 `/api/v1/map`，非法/不完整坐标返回 `400 INVALID_LOCATION`，默认不需要定位。
- 新增前端 Map 类型、runtime parser、`getMap()` 和 `/map` 页面。
- 列表与 marker 共用同一批 API items；支持选中联动、资源预览和含急诊字段筛选。
- 地图页面明确标注非导航、不请求定位、来源待补齐，不生成无上下文推荐 marker。
- 更新 map 契约、迁移计划、架构、评分卡、UI registry、status、history、review 和 memory。

## 验证

- `/api/v1/map` 默认响应 200、21 个坐标资源；带 `lat/lng` 返回 Haversine 直线距离；只传 `lat` 返回 400 `INVALID_LOCATION`。
- `./.venv/bin/pytest -q`：88 passed。
- `npm run typecheck`、`npm run test`：6/6；`npm run build`：通过，gzip 约 JS 84.0 kB、CSS 12.2 kB。
- `node --check static/js/app.js`、`git diff --check`：通过。
- 浏览器运行态：Map desktop/mobile 可加载真实资源；列表选择打开医院预览，含急诊字段筛选显示 20 个位置，390×844 无明显横向溢出。

## 未完成

- 当前是轻量位置示意，不是第三方地图/导航；真实附近急诊路径和推荐上下文 marker 尚无正式契约。
- 医院逐字段 provenance、医生/医院详情、结构化 follow-up answer API、完整 route parity 和生产定位/隐私审查仍未完成。
- Playwright/E2E、独立截图 baseline、keyboard/contrast 审查和 frontend CI job 仍需补齐。

## 下一步

为正式急诊路径和资源详情建立来源/更新时间/许可契约，再补核心流程 E2E、视觉/无障碍门禁和 frontend CI；继续保持 legacy 默认路由不变。
