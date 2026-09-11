# Review：Legacy 静态资源缺口收口

日期：2026-09-11  
范围：`templates/index.html`、`static/css/leaflet.css`、新增 SVG、静态资源测试  
计划：[2026-09-11-legacy-static-assets.md](../plans/2026-09-11-legacy-static-assets.md)

## 1. 计划对齐

结论：通过。favicon 和 Leaflet layers CSS 已切换到仓库内资源，未改变业务或地图交互。

## 2. 系统完整性

结论：通过。资源为本地 SVG，无外部请求；HTML/CSS 明确引用，静态边界测试覆盖文件存在和旧 URL 清除。

## 3. 生产准备度

结论：未达到最终 UI cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] 完整 viewport/console、E2E、视觉 baseline 和无障碍矩阵仍未完成。
- [P2] Leaflet marker 默认 PNG 路径仍由 legacy JS/默认图标机制管理，未在本切片扩大资源替换范围。

## 总结

已收口 audit 中两处明确静态缺口，不宣称 legacy UI 资产治理或完整视觉 QA 完成。
