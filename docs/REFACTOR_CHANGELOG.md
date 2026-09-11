# 重构变更记录

## 2026-09-09 — 基线与边界

建立项目规则、数据/模型/Safety 评估基线、Region Pack、loader/repository、v1 envelope 和稳定 characterization。

## 2026-09-10 — Domain 与前端迁移

完成医学输入、Safety-first publication、推荐 domain 和交通 seam；建立 React/TypeScript/Vite、API client、tokens、首页、核心分诊流程和资源/地图/Trust 页面。

## 2026-09-11 — Application services 与正式收口

完成 triage、recommendation、resource catalog、summary/evidence/map/region read service；完成 Profile/History、可访问性和键盘语义；React build 切换为 Flask 默认入口；v1 blueprint 改用直接注册 handler；删除 legacy routes、legacy UI、未使用的 assistant/carousel/background 资产、dead wrappers、反馈 JSONL、backup assets、根 fallback doctors 和 cloudflared 二进制。

## 2026-09-11 — P0 产品硬化

- 修复已记录的口语呼吸困难、压榨样胸痛/冷汗安全回归；笼统输入进入 `INSUFFICIENT_INFORMATION`，并保留否定表达边界。
- 安全样例扩展至 38 个：Red Flag Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency False Negative `0`。
- 恢复医院/地图资料中的高德导航 URI；清理普通页面工程化文案，技术证据收进 Trust Center 的折叠详情；补充 15 个前端边界测试和 5 个 Playwright smoke tests。

## 2026-09-11 — P0 正确性与产品闭环

- 位置契约改为显式 `unknown`/`district`/`geolocation`；未知位置不再默认天宁区，距离、交通和公平性在数据不可用时不参与排序。
- Follow-up 改为结构化 `question_id` + `value/text_answer`，原始症状与系统问题分离；结构化红旗答案由 Safety Gate 优先处理。
- 医院目录从组合根迁移到 active Region Pack，公开事实、临时派生能力和未支持字段分离；移除参与运行时排序的伪造床位、门诊量和评级，缺失容量权重自动关闭。
- 新增 random baseline 与 exact symptom fingerprint grouped split 评估、split manifest、近重复审计和 CI drift gate；Trust Center 展示模型切分与医院目录证据。
- 恢复 OpenStreetMap/CARTO 地理地图、医院/医生详情关系、医院列表和地图 marker 选择、AMap 导航及移动布局；新增位置/Follow-up/数据/地图回归测试。

## 基线说明

- P0 后 Safety Evaluation：38 cases，Red Flag Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency False Negative `0`；固定样例回归不代表临床验证。
- 数据质量：扫描 28 个文件，登记 187 个异常；本轮未修复。
- 推荐/分诊结果：canonical v1 characterization 保留，旧 `/api/*` route harness 已删除。
- P0 后 canonical snapshot SHA-256：`2b0637630eb52013c9cba3a5cc20f1a536602d2cf7bbf4e91170d638f0754d59`。
