# 常医后端重构计划：交通目录 Application Service 边界

状态：已完成  
日期：2026-09-11  
变更等级：L2（交通数据读模型编排；不改变推荐口径）

## 目标

将旧交通线路、站点、出租车、公共自行车、共享车辆和交通统计接口的 read-model 组装移入独立 application service，减少 `app.py` 中的数据集合遍历和统计逻辑。

## 非目标

- 不修改公交/出租车/骑行原始数据、字段、summary、统计公式、医院可达性计算或来源口径。
- 不把样本交通提升为实时路况，不改变推荐排序、缓存 TTL、急症路径或距离算法。
- 不引入外部地图、定位、导航、数据库或分页。

## 安全与数据验收边界

- 交通样本继续只作为现有展示/排序输入；不得在文案中承诺实时可达、到院时效或交通保障。
- 数据质量报告的异常继续只读登记，未通过质量门禁的数据不升级为正式医疗事实。
- 旧 endpoint response shape 和派生统计必须通过 snapshot/route smoke；本切片不改变医学规则。

## 实施步骤

1. 新增注入式 `TransitCatalogApplicationService`，承载五类数据 payload 和公交统计。
2. 将旧交通路由与 `_bus_route_stats` 改为 service 调用，保留原 HTTP envelope。
3. 增加 service tests，运行编译、全量回归、交通 endpoint smoke、快照、Safety Evaluation 和 diff 检查。

## 验收

- service 不依赖 Flask；路由不再直接遍历交通数据或计算统计。
- 五类交通数据与统计输出保持兼容；推荐 snapshot 和交通计算测试保持。

## 回滚

恢复旧交通 handler 和 `_bus_route_stats` 实现，移除 service、测试和记录即可；不修改交通数据或推荐模型。

## 实施结果

- 交通五类 read model 与派生统计已移入 `TransitCatalogApplicationService`；旧路由只负责 envelope。
- 新增 service unit；全量 pytest 为 `104/104`。
- characterization snapshot、交通纯函数和 Safety Evaluation 基线保持。
