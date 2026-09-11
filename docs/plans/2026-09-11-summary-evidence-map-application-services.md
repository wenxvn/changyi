# 常医后端重构计划：摘要、证据与地图应用服务接缝

状态：已完成  
日期：2026-09-11  
变更等级：L2（只读投影与路由编排拆分；保持接口行为）

## 目标

把 v1 的摘要、Trust Center 证据和地图投影从 `app.py` 的路由函数中移到显式 application service，保留现有数据来源、免责声明、错误码、响应 envelope 和坐标计算行为。

## 非目标

- 不修改医学规则、Safety Evaluation、推荐排序、地图急诊语义或数据口径。
- 不新增实时地图、附近急诊导航、逐字段 provenance、账号历史、认证或远程数据。
- 不在本切片切换 legacy 默认入口、删除兼容 adapter 或引入新的运行时依赖。

## 验收

- `/api/v1/summary`、`/api/v1/evidence`、`/api/v1/map` 的路由只保留请求解析、错误适配和 v1 envelope。
- 三个 service 可通过注入 suppliers 单元测试，缺失数据与坐标边界保持现状。
- 全量 pytest、前端检查、API smoke、快照、Safety Evaluation 和 diff 检查通过。

## 回滚

恢复路由对现有 builder/内联摘要逻辑的调用即可；不改变 URL、数据文件或前端入口。

## 实施结果

- 新增 `SummaryApplicationService`、`EvidenceApplicationService` 和 `MapViewApplicationService`，分别接收区域、目录、交通和评估依赖。
- `/api/v1/summary`、`/api/v1/evidence`、`/api/v1/map` 已改为 service 委托；HTTP 校验、v1 envelope、免责声明、坐标错误码和地图投影保持。
- 新增 4 个 service unit tests；全量 pytest 为 `114/114`，并完成 Python 语法检查与 `git diff --check`。
