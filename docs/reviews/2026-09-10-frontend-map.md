# Review：Frontend Map

日期：2026-09-10  
范围：`backend/app/application/map_view.py`、`/api/v1/map`、Map schema/API、`frontend/src/pages/MapPage.tsx`、相关样式与文档  
计划：[2026-09-10-frontend-map.md](../plans/2026-09-10-frontend-map.md)

## 1. 计划对齐

结论：通过，首版范围已完成。

- 当前坐标资源从 v1 API 返回，列表与 marker 共用 items，选中预览和急诊字段筛选已实现。
- 未请求定位权限、未引入外部地图/导航、未伪造推荐 marker 或实时急诊状态。
- 不完整/非法坐标已收敛为稳定 `400 INVALID_LOCATION`，默认无定位仍可正常浏览。

## 2. 系统完整性

结论：通过。

- 地图 view builder 过滤缺失/非有限坐标，服务端统一生成投影和可选 Haversine 直线距离；前端 parser 校验坐标和 marker 类型。
- 页面请求统一经过共享 client，不直接调用 `fetch`、不使用 `window._*`，筛选与选择只改变展示状态。
- 页面持续展示 `legacy_catalog_pending_provenance`、非导航和急诊字段限制，没有把资源字段包装成官方推荐或临床结论。
- 浏览器 desktop 与 390×844 已看到真实资源、列表/marker 预览联动和含急诊字段筛选。

## 3. 生产准备度

结论：未达到最终 cutover/competition-ready 门槛，但本切片没有新增 P1 阻断。

- [P1] 当前为轻量位置示意，不是导航地图；真实附近急诊路径、交通时间和推荐上下文 marker 尚无契约。
- [P1] 医院逐字段 provenance、更新时间、许可和正式资源详情仍未齐备。
- [P1] 尚无 Playwright 核心流程、截图 baseline、keyboard/contrast 矩阵和 frontend CI job。
- [P2] 用户定位与隐私边界未实现；本切片选择不请求定位以避免无明确隐私契约的传输。

## 总结

地图首版可用于本地原型演示和资源位置复核，不应替代导航、急救指令或官方推荐；下一切片优先补正式急诊路径/资源详情契约和质量门禁。
