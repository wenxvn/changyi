# Algorithm-visible UX

更新时间：2026-09-16  
范围：前端产品交互（`frontend/src`）。不修改 Safety Gate、医学规则、模型训练或 `/api/v1` 契约。

## 核心 Journey

```text
症状输入（键盘 / 语音 / 示例）
  → Safety Gate 阶段可见
  → 系统理解（仅展示后端真实字段）
  → 就医方向路由（Direct Department）
  → 信息不足 / 低可信 → 选择性拒答（不硬给科室）
  → Adaptive Inquiry（有限关键追问）
  → 回答后重算 →「信息补充 → 路径更新」
  → 多目标资源路由（偏好可调，解释排序）
  → 地图 / 高德导航
```

阶段状态由真实请求生命周期与 `/api/v1` 返回驱动（`ProgressiveStatus`、`TriageResults`）。首页 CarePath 为静态链路示意，已移除 `setInterval`/装饰性假分析计时。

## 三个演示案例

| 入口 | 示例文案（透明标注「示例」） | 预期真实 API 结果走向 |
| --- | --- | --- |
| 普通路径 | 皮肤瘙痒一周，无呼吸困难/发烧 | ROUTINE → 科室方向 → 资源路由 → 导航 |
| 模糊 / 追问 | 最近总是头晕 | INSUFFICIENT 或 followup.needed → 拒答表述 + Adaptive Inquiry → 回答后路径更新 |
| 红旗 / 急诊 | 胸口压榨样疼痛、喘不过气、冒冷汗 | EMERGENCY → `拨打 120` 优先 → 急诊目录 + 地图闭环 |

实现：`ExampleSymptomChips` 仅预填 `condition` 并调用真实 `POST /api/v1/triage`，无硬编码结果。

## 算法状态 → UI

| 算法阶段 | UI | 数据来源 |
| --- | --- | --- |
| Safety Gate | ProgressiveStatus「Safety Gate」、Emergency 横幅、红旗标签 | `triage_status`、`triage.red_flag_tags`、`triage.reasons` |
| Direct Department | 「就医方向路由」、`matched_department` | `matched_department` |
| Selective Abstention | 「暂不强行给出科室方向」、`result-why` | `INSUFFICIENT_INFORMATION` / `followup.needed`；可选 `abstain_reason`、`uncertainty_level` |
| Adaptive Inquiry | `FollowupPrompt`（为何问、第 n 问、跳过） | `triage.followup` / `POST /api/v1/triage/followups` |
| 信息补充 → 路径更新 | `path-updated` 提示 + 阶段重算 | `followup_answers` 回传后重新 triage |
| Multi-objective Care Routing | 偏好面板、`hospital-why` 排序解释 | `explanations`、`ranking_notice`、`resource_strategy`、`feature_availability` |
| 地图 / 导航 | Map 页 + `AmapNavigationLink` | `POST /api/v1/map` + 高德 URI |

## API 字段依赖与 fallback

| 字段 | 用途 | 缺失时 fallback |
| --- | --- | --- |
| `triage_status` | 四态分流 | 不可用则请求错误，不伪造状态 |
| `matched_department` | 科室方向 | 显示「继续整理 / 暂不强行给出」 |
| `triage.red_flag_tags` / `reasons` | 风险信号与理由 | 隐藏区块，不编造 |
| `triage.followup.*` | 追问 | 无则不渲染追问 |
| `triage.abstain_reason` / `uncertainty_level` / `should_clarify` / `symptom_tags` | 拒答/不确定/标签（可选） | 不展示，**不自行计算医学置信度** |
| `recommended_hospitals[].explanations` | 排序解释 | 无则不显示「为什么排在前面」 |
| `ranking_notice` / `resource_strategy.notice` | 路由策略说明 | 无则用空态文案 |
| `feature_availability` | 距离/交通是否参与 | 未知则不声称参与排序 |
| map `emergency` | 急诊目录字段 | 固定声明 ≠ 实时可接诊 |

## E2E 覆盖

`frontend/e2e/algorithm-visible.spec.mjs`：

1. 示例入口透明且走真实 triage API  
2. 普通路径 → 资源解释 + 高德导航  
3. 模糊路径 → 拒答 / 追问 → `path-updated`  
4. Emergency → 120 优先、无普通排行  
5. triage API 503 / MODEL_UNAVAILABLE → 可见错误 + 重试  
6. recommendations 失败 → 保留分诊结果 + 资源重试  

既有 `product-smoke` / `mobile` / `accessibility` 保持覆盖基础路由与安全文案契约。
