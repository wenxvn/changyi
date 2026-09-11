# 2026-09-11 目录索引与统计 Read Model 进度

## 本次完成

- `/api/departments`、`/api/districts` 和 `/api/stats` 已通过 `ResourceCatalogApplicationService` 生成数据。
- 保留原有排序、区域映射顺序、统计字段、固定 top departments 和 HTTP response shape。
- service unit 覆盖索引派生和医生/医院统计。

## 验证

- Python compile：通过。
- 全量 pytest：`106/106` 通过。
- legacy route smoke、characterization snapshot 和 Safety Evaluation：基线保持。

## 未完成与下一步

医院逐字段 provenance、正式资源发布、完整 legacy route parity、统计/数据刷新治理、正式附近急诊路径和远端 CI 仍开放。

## 回滚

恢复旧 routes 的集合遍历和统计代码，移除本切片 service 方法、测试和记录即可。
