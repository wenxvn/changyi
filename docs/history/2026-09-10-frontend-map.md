# 历史：Frontend Map 首版

日期：2026-09-10

## 事件

在 Trust Center 首版之后，将并行前端 `/map` 从 shell 空态推进为 API 驱动的医院位置示意和列表/marker 联动视图，并新增 `/api/v1/map`。

## 事实

- 当前 API 默认返回 21 个带坐标的医院资源；20 个资源带接口急诊字段，页面按 `EMERGENCY_CAPABLE` 与 `NORMAL` 区分 marker。
- 默认不请求用户定位；明确传入合法 `lat/lng` 时返回 Haversine 直线距离，不能解释为导航或急救到院时间。
- 列表和 marker 选择共享同一响应 items；选中医院可查看地址、坐标、急诊字段和来源限制。
- 当前医院目录仍为 `legacy_catalog_pending_provenance`，没有生成推荐 marker 或官方排序。

## 验证

后端 pytest 88 passed，前端边界测试 6/6，TypeScript/build/legacy JS 语法检查通过；浏览器 desktop 与 390×844 mobile 已检查真实加载、筛选、预览和布局。

## 回滚

删除或回退本切片新增的 map view service、v1 route、Map 页面和对应文档即可；不需要回退 Trust、Resources、triage 或 legacy 代码。
