# 重构暂停交接记录

日期：2026-09-11  
状态：本轮已暂停，等待下一份用户提示词  
关联状态：[docs/status/current.md](../status/current.md)  
关联记忆：[memory.md](../../memory.md)

## 本轮已完成

- 已完成低风险、行为保持式的 Triage、Recommendation、Resource Catalog、Prediction、Transit、Distance Rerank、Summary、Evidence、MapView 和 Region Read application service 接缝。
- 已完成症状疾病模型 adapter、v1 handler registry、legacy 资源/分诊 route adapter、F11 本地脱敏 Profile/History、F12 accessibility/keyboard semantics、legacy favicon/Leaflet layers 静态资源收口和 frontend CI 首版。
- legacy `/` 仍为默认入口；未切换新前端、未修改医学规则/推荐权重/模型文件、未提交或推送。

## 当前未重构或未完成的问题

### 后端边界

- `app.py` 仍是 legacy composition root，医学输入/已知疾病/红旗规则/追问组合、部分推荐候选组合与急症整体排序、交通数据加载/刷新策略仍在同一文件。
- `/api/test-feedback` 与 `/api/test-record` 仍将测试数据写入本地 JSONL；涉及隐私、日志和生产安全边界，未在本轮扩展。
- legacy API route parity 仍不完整；剩余兼容路由需要继续以 characterization/API contract 小步拆分，不能直接替换入口。
- 独立 application factory、真实 repository 组合和完整依赖注入仍未完成；当前 registry/service 是渐进接缝，不是生产容器。

### 医学、数据与地图

- Safety Evaluation 仍为 16 cases：Red Flag Recall `0.9231`、Under-triage `0.0769`、Emergency False Negative `1`；红旗/信息不足缺口必须另立 L3 计划并经医学审核。
- 地图仍是医院位置示意，未实现正式附近急诊路径、实时急诊可用性或导航；`emergency` 字段不得解释为实时能力。
- 医院/医生仍缺逐字段来源、许可证、更新时间和正式发布范围；医院目录继续保持 `migration_pending`。
- 数据质量报告仍登记 187 个异常，主要是公交疑似占位年份、时间先后异常和 h6 计数不一致；未自动修复。
- Profile/History 仅允许本地、opt-in、最多 8 条脱敏状态摘要，不能扩展为账号、云同步、病历或真实患者数据。

### 前端与质量门禁

- legacy `static/js/app.js`、`static/css/style.css` 仍为大单体；新 React 前端已并行建立，但尚未完成 legacy route/Safety parity 或默认入口 cutover。
- 尚未接入 Playwright/E2E、截图视觉 baseline、完整 keyboard/contrast/reduced-motion 矩阵；frontend CI 已加入但远端首次 job 尚待推送后确认。
- marker 默认图标等其余静态资源仍未完成全量审计。

## 可复现基线

- `.venv/bin/python -m pytest -q`：`116 passed`。
- 前端：typecheck、9/9 Node boundary tests、Vite build 通过（gzip JS 87.4 kB、CSS 13.1 kB）。
- Safety Evaluation：上述基线保持；characterization snapshot SHA-256 为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- `git diff --check`、Python 语法检查和 v1/legacy 关键 API smoke 通过。

## 下一次工作约束

先读取 `AGENTS.md`、`docs/status/current.md`、本文件、`memory.md` 以及相关 plan/review/ADR。除非新提示词另有授权，继续保持 legacy 默认入口、医学规则和推荐快照；涉及红旗、正式急诊、患者数据、认证或生产部署时，先按 L3/L4 风险流程建立计划和评审。
