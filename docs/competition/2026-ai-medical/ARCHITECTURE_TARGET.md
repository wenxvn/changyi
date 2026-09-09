# 目标架构

## 目标形态

```text
app.py / create_app
  ├─ API v1 routes + request/response schemas
  ├─ application services
  │   ├─ triage / follow-up
  │   ├─ recommendation / resources
  │   └─ evidence / feedback
  ├─ domain
  │   ├─ symptom / triage / department
  │   ├─ recommendation / explainability
  │   └─ versioned rules and weights
  └─ infrastructure
      ├─ RegionRegistry / RegionContext
      ├─ HospitalRepository / DoctorRepository / TransitRepository
      ├─ data loaders / validators
      └─ model adapters
```

资源层：

```text
data/regions/320400/
  manifest.json
  hospitals/
  doctors/
  transit/
  metadata/
```

## 当前边界审计

现有 Flask 单体把常量、模型适配、医学规则、推荐排序、交通计算和路由混在 `app.py`；前端则把页面、状态、API 和 HTML 字符串混在 `static/js/app.js`。首轮不做大爆炸重写，而是先建立 loader、Region registry、schema、v1 兼容入口和行为测试。

## 迁移策略

采用 Strangler Pattern：旧路由继续可用，新 v1 路由调用同一条应用服务链；旧路由不能复制另一套医学或推荐规则。完成契约测试和行为比较后，才删除旧路径。

## 回滚

每个 Slice 独立提交；如果新边界导致行为回归，保留旧路径和兼容适配器，回滚到该 Slice 提交，不重置或清理用户改动。
