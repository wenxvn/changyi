# ADR-0015：统一目录索引与统计 Read Model

状态：已接受  
日期：2026-09-11  
范围：旧 `/api/departments`、`/api/districts`、`/api/stats` 与 `ResourceCatalogApplicationService`

## 背景

资源目录的医院/医生读路由已经使用 application service，但科室、区域和系统统计仍在 `app.py` 直接遍历全局集合。继续保留这类派生逻辑会让目录迁移出现多个入口。

## 决定

- 将科室列表、区域名称和医院/医生统计加入 `ResourceCatalogApplicationService`。
- service 只返回旧 data payload，不依赖 Flask、不更改统计口径；route 继续负责 HTTP envelope。
- 固定 top departments 作为显式兼容常量保留，待数据治理后再讨论是否版本化。

## 影响

正向影响：目录索引、详情和统计共享同一 application boundary，后续接入 repository 的改动面更小。

代价：统计仍基于启动时内存数据，医院字段口径和 provenance 仍待治理。

## 回滚

恢复旧 routes 的局部计算即可，不涉及模型或原始数据。
