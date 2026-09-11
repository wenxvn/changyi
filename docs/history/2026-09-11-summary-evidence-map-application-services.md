# 历史记录：摘要、证据与地图应用服务接缝

日期：2026-09-11

## 事件

在保持 `/api/v1/summary`、`/api/v1/evidence`、`/api/v1/map` 契约的前提下，新增三个只读 application service，并将 Flask 路由改为薄适配层。区域、目录、交通、离线评估报告、坐标校验和安全免责声明仍使用原来源。

## 结果

- 新增 4 个 application service 单元测试。
- 全量 pytest 从本切片前的 110 增至 114，全部通过。
- Python 语法检查和 `git diff --check` 通过。

## 保留事项

实时急诊可用性、正式导航、逐字段 provenance、完整 route parity 和独立 factory 未在本事件中处理。
