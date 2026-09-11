# 常医前端重构计划：Legacy 静态资源缺口收口

状态：已完成  
日期：2026-09-11  
变更等级：L1（静态资源与入口声明；不改变业务行为）

## 目标

修复 UI audit 已记录的 legacy favicon 与 Leaflet layers 图标 404，使用仓库内可审查的 SVG 资源，减少运行态噪声并保持地图控件视觉入口。

## 非目标

- 不删除现有图片，不修改地图/定位/导航行为，不引入外部 CDN 或远程资源。
- 不改变医疗文案、分诊、推荐、数据来源、旧路由或 Leaflet JS 版本。
- 不宣称完整 viewport、console、E2E 或视觉 baseline 已完成。

## 验收

- `templates/index.html` 显式声明仓库内 favicon；Leaflet layers 控件的标准/retina CSS 均指向仓库内 SVG。
- 静态文件存在、CSS/HTML 边界测试通过；Flask 静态 URL smoke 返回 200；完整 pytest、frontend tests/build 和 diff 检查通过。

## 回滚

恢复原 favicon 缺省行为与 Leaflet CSS 图片 URL，移除新增 SVG、测试和记录即可；不影响业务代码和数据。

## 实施结果

- 新增 `static/favicon.svg` 和 `static/images/leaflet-layers.svg`，并更新 legacy template/CSS。
- 新增静态资源边界测试；全量 pytest 为 `108/108`。
- 未修改业务逻辑；完整 UI/E2E 矩阵仍按开放风险继续。
