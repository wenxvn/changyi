# 当前架构与重构边界

更新时间：2026-09-09

## 当前形态

```text
浏览器
  └─ templates/index.html
      └─ static/js/app.js ── fetch /api/* ── app.py
                                              ├─ 内置医院/兼容目录（pending provenance）
                                              ├─ data/doctors_h*.json
                                              ├─ data/*transit*.json
                                              └─ data/symptom_disease_model/*

当前已增加一层可回滚的基础设施，但尚未删除单体路径：

```text
app.py（legacy shell + adapters）
  ├─ backend.app.create_app（配置、CORS、v1 blueprint）
  ├─ backend.app.infrastructure.data.JsonDataLoader
  ├─ backend.app.infrastructure.regions.RegionRegistry
  └─ backend.app.infrastructure.repositories（医生/交通；医院 pending adapter）
```
```

前端脚本同时承担路由导航、登录演示、状态缓存、表单采集、推荐请求、卡片渲染、地图、交通图层、助手对话和测试反馈。后端文件同时包含常量、数据加载、模型适配、症状规则、分诊、推荐评分、交通可达性和 HTTP 路由。

## 后端职责现状

- **数据加载**：医院常量、真实医生 JSON、公交/出租车/骑行 JSON、模型文件。
- **医学辅助**：口语症状归一化、已知疾病识别、症状到疾病类别预测、追问、红旗和分诊分析。
- **推荐**：科室匹配、医院/医生资源评分、距离、交通可达性、公平性和推荐解释。
- **接口层**：医院、医生、推荐、分诊、追问、反馈、统计、交通和助手接口。
- **演示启动**：`app.run(... port=5002)`。
- **版本化接口**：全部 `/api/v1` 外壳由 blueprint 提供；triage、followups、recommendations、医院/医生暂通过延迟 legacy adapter 复用组合逻辑，完整 legacy route factory parity 尚未完成。

## 前端职责现状

- 页面由 `index.html` 提供骨架，主要内容运行时由 JS 生成。
- `app.js` 使用全局 `window.*` 状态，包含多个页面和大量渲染器。
- `style.css` 已有 CSS 变量，但也存在较多硬编码颜色和组件样式。
- UI consistency 基线尚未通过 `imprint audit` 正式建立。

## 目标边界（暂定）

重构应逐步形成以下边界，但不要求一次完成：

```text
routes / HTTP adapters
  └─ application services
      ├─ triage / symptom service
      ├─ recommendation service
      ├─ data access / repositories
      └─ model adapters
          └─ local JSON/CSV/model artifacts

frontend shell
  ├─ API client
  ├─ page/state controllers
  ├─ reusable renderers/components
  └─ design tokens + ui-registry
```

## 不可直接跨越的边界

- 路由不应拥有新的复杂评分、文件读取或模型实现。
- 前端不得自行复制医学规则或推荐权重；展示可以做轻量格式化，但事实以 API 为准。
- 数据脚本不得静默覆盖正式数据；生成文件必须有明确输出目录和元数据。
- 训练/评估代码不得自动替换线上（或演示默认）模型，必须有模型版本和回滚指针。

## 首轮重构观察项

- `app.py` 中存在硬编码常量和动态加载混合，适合先做“只搬运不改行为”的分层。
- 当前已有基础测试和稳定字段快照，先扩展接口/纯函数表征与模型不可用样例，比直接拆文件更安全。
- 当前已有 9 个基础/数据边界测试、稳定快照和临时依赖环境 API smoke；CI 和模型 smoke 尚未完成。
- 前端全局状态较多，先抽 API client 和页面级状态边界，不宜立即引入大型框架。
- 交通数据参与可达性展示和部分评分，拆分时必须验证“展示数据”和“推荐排序数据”的边界。
