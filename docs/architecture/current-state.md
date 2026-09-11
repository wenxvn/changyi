# 当前架构

更新时间：2026-09-11
状态：正式重构基线

## 运行链路

```text
Browser
  ├─ Flask / → frontend/dist/index.html
  ├─ Flask /<route> → 同一 React shell（SPA refresh fallback）
  └─ /api/v1/*
       ↓
     backend/app/api/v1/routes.py
       ↓
     backend/app/composition.py handlers
       ↓
     application services
       ↓
     domain functions / Safety-first publication / recommendation pipeline
       ↓
     repositories, RegionRegistry, JsonDataLoader, model adapters
       ↓
     data/、evaluation/ 和本地模型文件
```

## 模块职责

- `app.py`：`python app.py` 启动兼容和历史导入表面，不承载业务逻辑。
- `backend/app/__init__.py`：Flask factory、配置、CORS、Region Read service 和 v1 blueprint 注册。
- `backend/app/composition.py`：当前单一 Flask 组合根，组装本地数据、模型 adapter、既有纯逻辑、application services 和 v1 handler；其内部 legacy 规则仅作为冻结行为的组合实现，后续医学迁移必须另立 L3 计划。
- `backend/app/api/v1/routes.py`：HTTP 参数、envelope、状态码和 handler lookup；不读取文件、不实现医学规则。
- `backend/app/application/`：`TriageApplicationService`、`RecommendationApplicationService`、`ResourceCatalogApplicationService`、`SummaryApplicationService`、`EvidenceApplicationService`、`MapViewApplicationService` 和 `RegionReadApplicationService`。
- `backend/app/domain/`：医学输入、安全状态/发布、推荐 score/features/candidate/pipeline/resource policy/traffic 等可测试逻辑；本轮不改变其业务语义。
- `backend/app/infrastructure/`：数据加载、区域注册、医生/交通仓库和症状疾病模型 adapter。
- `frontend/src/`：React 页面、组件、API client、类型、状态和 token；不复制医学规则、疾病模型或推荐排序。

## 正式 API

正式接口只保留 `/api/v1`：

`health`、`ready`、`regions`、`triage`、`triage/followups`、`recommendations`、`hospitals`、`hospitals/<id>`、`doctors`、`doctors/<id>`、`summary`、`evidence`、`map`。

Emergency 和信息不足由后端 Safety-first publication 脱敏发布；前端不请求或展示普通推荐作为急症替代。地图是坐标位置示意，直线距离不是导航、到院时间或实时急诊可用性。

## 数据与回滚

- active Region Pack：`320400`；医院目录仍显式标记 `migration_pending`。
- 医生公开资料来自 `data/doctors_h*.json`；交通是脱敏样本，不代表实时路况。
- 模型和排序版本由配置字段公开；模型不可用必须走现有降级契约。
- React cutover 通过 Flask-served build 完成；若 build 缺失，根路由返回明确 `503`，不会回退到旧前端。
- 每个切片可独立回滚；不使用 reset、force push 或覆盖用户文件。

## 明确不在本基线

正式附近急诊导航、实时可用性、结构化 follow-up answer API、逐字段正式 provenance、医学规则修复、账号/数据库/生产认证和新产品能力统一记录在 `docs/POST_REFACTOR_BACKLOG.md`。
