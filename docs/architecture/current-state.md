# 当前架构与重构边界

更新时间：2026-09-10

## 当前形态

```text
浏览器
  └─ templates/index.html
      └─ static/js/app.js ── fetch /api/* ── app.py
                                              ├─ 内置医院/兼容目录（pending provenance）
                                              ├─ data/doctors_h*.json
                                              ├─ data/*transit*.json
                                              └─ data/symptom_disease_model/*
```

当前已增加一层可回滚的基础设施，但尚未删除单体路径：

```text
app.py（legacy shell + adapters）
  ├─ backend.app.create_app（配置、CORS、v1 blueprint）
  ├─ backend.app.infrastructure.data.JsonDataLoader
  ├─ backend.app.infrastructure.regions.RegionRegistry
  ├─ backend.app.infrastructure.repositories（医生/交通；医院 pending adapter）
  ├─ backend.app.domain.medical_input（归一化/否定纯函数）
  ├─ backend.app.domain.triage.safety_gate（状态契约/安全交接）
  ├─ backend.app.domain.recommendation.scoring（排序与医院/医生 score 纯函数）
  ├─ backend.app.domain.recommendation.features（医院 feature 纯函数）
  ├─ backend.app.domain.recommendation.pipeline（医院候选 rerank 纯函数）
  ├─ backend.app.domain.recommendation.resource_policy（医生资源策略纯函数）
  ├─ backend.app.domain.recommendation.candidate（候选遍历、结果/解释纯函数）
  ├─ backend.app.domain.recommendation.candidates（医生 candidate 过滤、医院命中和急症资格纯函数）
  └─ backend.app.domain.recommendation.traffic（交通 feature/可达性纯函数）
```

前端脚本同时承担路由导航、登录演示、状态缓存、表单采集、推荐请求、卡片渲染、地图、交通图层、助手对话和测试反馈。后端文件同时包含常量、数据加载、模型适配、症状规则、分诊、推荐评分、交通可达性和 HTTP 路由。

## 后端职责现状

- **数据加载**：医院常量、真实医生 JSON、公交/出租车/骑行 JSON、模型文件。
- **医学辅助**：口语症状归一化、已知疾病识别、症状到疾病类别预测、追问、红旗和分诊分析。
- **推荐**：科室匹配、医院/医生资源评分、距离、交通可达性、公平性和推荐解释。
- **接口层**：医院、医生、推荐、分诊、追问、反馈、统计、交通和助手接口。
- **演示启动**：`app.run(... port=5002)`。
- **版本化接口**：全部 `/api/v1` 外壳由 blueprint 提供；triage、followups、recommendations、医院/医生通过 `backend.app.api.v1.legacy_adapter` 延迟复用组合逻辑，完整 legacy route factory parity 尚未完成。
- **输入 domain**：`backend.app.domain.medical_input` 已承载现有口语归一化和否定窗口纯函数；已知疾病、红旗和分诊仍由 legacy 组合逻辑提供，等待后续 Safety Gate 切片。
- **Safety Gate domain**：`backend.app.domain.triage.safety_gate` 已承载四态枚举和基于 legacy 输出的安全交接 decision；`backend.app.domain.triage.publication` 已承载 Safety-first 的疾病候选/模型/追问脱敏；红旗规则本身仍在 legacy 组合逻辑中，评估集已把现有缺口显式列为 review required。
- **v1 安全发布边界**：`/api/v1` triage/recommendations 在 `EMERGENCY` 或 `INSUFFICIENT_INFORMATION` 时对疾病候选做 abstain；急症不公开普通 follow-up，保留红旗、急诊动作和免责声明。legacy `/api/*` 暂保留原输出，等待后续 adapter parity 切片。
- **推荐 domain**：`backend.app.domain.recommendation.scoring` 已承载 clamp、文本、科室关系、医生职称、内部资源分层、医院/医生 score 组合；`resource_policy` 已承载医生资源策略、专家偏好修正和错配惩罚；`candidate` 已承载医院候选遍历 orchestration、急症医生兜底候选遍历、单候选 feature/score/explain/result 组合、急症兜底评分、普通医生和急症兜底候选的解释/结果对象组装；`candidates` 已承载医生 candidate 过滤、医院科室命中/强项回退和急症医院资格；`traffic` 已承载交通摘要、可达性 score、样本行索引和四类样本计算；`backend.app.infrastructure.repositories.transit_repository.LazyTrafficAccessCache` 已承载交通 map 的懒加载生命周期；交通数据加载和急症整体排序仍在 `app.py`，通过快照渐进迁移。
- **医院 feature domain**：`backend.app.domain.recommendation.features` 已承载医院能力、等级、可用性、质量、连续照护、特殊人群适配、风险惩罚和解释纯函数；交通/距离与完整排序组合仍在 legacy。
- **医院 rerank domain**：`backend.app.domain.recommendation.pipeline` 已承载已评分医院候选的基础排序、区域多样性和普通场景三甲数量约束；候选生成、交通/距离和 score 组合仍在 legacy，急症旁路不应用普通约束。

## 前端职责现状

- 页面由 `index.html` 提供骨架，主要内容运行时由 JS 生成。
- `app.js` 使用全局 `window.*` 状态，包含多个页面和大量渲染器。
- `style.css` 已有 CSS 变量，但也存在较多硬编码颜色和组件样式。
- UI consistency 基线已通过 `imprint audit` 建立在 `ui-registry.md`；完整 viewport/console 矩阵仍未完成。

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
- 当前已有 86 个基础、输入边界、模型 smoke、Safety Gate、安全发布、评估集、API contract 和推荐 scoring/feature/rerank/resource-policy/candidate/traffic/cache 测试，以及稳定快照；CI workflow 已建立，远端首次运行待推送后确认。
- 前端全局状态较多，先抽 API client 和页面级状态边界，不宜立即引入大型框架。
- 交通数据参与可达性展示和部分评分，拆分时必须验证“展示数据”和“推荐排序数据”的边界。
