# 2026-09-11：完成本地演示资料与脱敏历史首版

## 背景

F11 要求提供 Profile/History 体验，但仓库没有账号体系，且医疗输入属于敏感信息。直接保存完整会话会扩大隐私和误解为病历的风险。

## 处理

- 以 `docs/decisions/0006-local-demo-profile-history.md` 固化本地 demo 决策。
- 新增 `/profile` 页面，明确常州演示访客、区域包 `320400`、当前浏览器本地边界和非病历声明。
- 历史默认关闭；主动开启后仅保存状态级摘要，最多 8 条；提供关闭记录和二次确认清除。
- 将存储、解析、白名单和降级集中到 `frontend/src/state/demoProfile.ts`，页面不直接调用浏览器存储。
- Triage 只在分析完成/跳过追问时调用摘要记录，不改变请求、Safety 状态或普通推荐短路规则。

## 结果

前端 typecheck、7/7 boundary tests、production build、静态检查和 Profile desktop/390×844 运行态检查通过。未用真实医疗描述做浏览器写入测试；下一步仍是 E2E/视觉/无障碍门禁与正式急诊/来源治理。
