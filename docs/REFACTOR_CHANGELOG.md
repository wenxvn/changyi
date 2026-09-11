# 重构变更记录

## 2026-09-09 — 基线与边界

建立项目规则、数据/模型/Safety 评估基线、Region Pack、loader/repository、v1 envelope 和稳定 characterization。

## 2026-09-10 — Domain 与前端迁移

完成医学输入、Safety-first publication、推荐 domain 和交通 seam；建立 React/TypeScript/Vite、API client、tokens、首页、核心分诊流程和资源/地图/Trust 页面。

## 2026-09-11 — Application services 与正式收口

完成 triage、recommendation、resource catalog、summary/evidence/map/region read service；完成 Profile/History、可访问性和键盘语义；React build 切换为 Flask 默认入口；v1 blueprint 改用直接注册 handler；删除 legacy routes、legacy UI、未使用的 assistant/carousel/background 资产、dead wrappers、反馈 JSONL、backup assets、根 fallback doctors 和 cloudflared 二进制。

## 基线说明

- Safety Evaluation：16 cases，Red Flag Recall `0.9231`、Under-triage `0.0769`、Over-triage `0.0`、Emergency False Negative `1`；保留为辅助系统基线，不代表临床验证。
- 数据质量：扫描 27 个文件，登记 187 个异常；本轮未修复。
- 推荐/分诊结果：canonical v1 characterization 保留，旧 `/api/*` route harness 已删除。
- canonical snapshot SHA-256：`435f0595c1801d2a591775563efca4947f5d1d51f7444fb6bdc074536111ab6a`。
