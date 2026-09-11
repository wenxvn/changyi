# 2026-09-11 交通目录 Application Service 进度

## 本次完成

- 交通线路、站点、出租车、公共自行车、共享车辆五类 payload 和公交派生统计已移入 `TransitCatalogApplicationService`。
- `/api/transit/*` 路由保留原 URL、JSON 字段、summary 和脱敏样本口径；医院交通可达性仍调用既有纯函数。
- 新增 service unit，覆盖集合 payload、summary、票价/公司/线路统计和医院 access 合并。

## 验证

- Python compile：通过。
- 全量 pytest：`104/104` 通过。
- characterization snapshot、交通计算测试和 Safety Evaluation：基线保持。

## 未完成与下一步

交通 repository 的数据新鲜度/刷新、跨进程一致性、推荐急症整体排序、完整 legacy route parity 和远端 CI 仍开放；交通样本不代表实时路况。

## 回滚

恢复旧交通 routes 与 `_bus_route_stats`，移除本切片 service、测试和记录即可。
