# ADR-0013：以 Application Service 编排交通目录读模型

状态：已接受  
日期：2026-09-11  
范围：旧 `/api/transit/*` 路由与 `backend/app/application/transit.py`

## 背景

旧交通路由直接读取全局数据集合，公交统计还在 `app.py` 计算多级 summary 并调用医院可达性函数。这样让 HTTP 层与数据 read model、统计和展示/推荐边界混在一起。

## 决定

- 新增 `TransitCatalogApplicationService`，通过 supplier 注入已加载数据和既有医院可达性函数。
- service 只返回交通 read model/统计，不依赖 Flask，不改变数据来源、公式或推荐参与方式。
- 旧路由保留 `/api/transit/*`、`code/data/summary` 结构；`_bus_route_stats` 仅作为兼容调用名保留。

## 影响

正向影响：交通 endpoint 可脱离 Flask 单测，统计逻辑与可达性输入边界明确，后续 repository/刷新治理更容易接入。

代价：交通数据仍在启动时由 legacy loader 载入，样本仍不是实时路况，跨进程 cache/新鲜度和推荐急症整体排序仍未解决。

## 回滚

恢复旧数据读取/统计逻辑即可，不涉及原始数据或模型。
