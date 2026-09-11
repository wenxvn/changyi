# 常医后端重构计划：旧分诊路由收敛到 Triage Application Service

状态：已完成  
日期：2026-09-11  
变更等级：L3（医疗辅助路径的行为保持式边界收敛）

## 目标

让旧 `/api/triage`、`/api/followup` 和 `/api/assistant/process` 复用 `TriageApplicationService` 的编排方法，减少 `app.py` 中重复的分诊响应组装，为 v1/legacy route parity 建立同一 application seam。

## 非目标

- 不修改红旗规则、四态映射、追问策略、模型预测、医学文案、Safety Gate 或任何推荐逻辑。
- 不把旧接口自动升级为 v1 Safety-first publication；旧接口继续保持历史响应形状。
- 不实现结构化 follow-up answer API、正式附近急诊路径或医学规则修复。

## 安全验收边界

- 本切片只移动既有函数调用顺序，不改变 Emergency、信息不足、模型不可用或低置信度的原始返回。
- 16-case Safety Evaluation Set 的基线（Recall `0.9231`、Under-triage `0.0769`、Emergency False Negative `1`）必须保持；已知反例仍需医学审核，不因抽取而放行。
- v1 继续走既有 Safety-first service；旧 `/api/*` 继续保留旧输出，回滚时可独立恢复。

## 实施步骤

1. 在 triage service 增加旧 triage/follow-up/assistant payload 编排方法。
2. 将旧路由收敛为请求解析、空输入错误和 JSON envelope。
3. 增加 service unit 与 legacy route smoke，运行全量回归、快照和 Safety Evaluation。

## 验收

- 旧三个路由的字段、状态码、模型输出和答案拼接行为保持不变。
- service 不依赖 Flask request/response，`app.py` 不再在这些路由中直接编排 triage 结果。
- 通过 Python compile、pytest、API smoke、Safety Evaluation、快照和 diff 检查。

## 回滚

恢复旧路由内的编排代码并移除新增 service 方法、测试和记录；不修改模型、数据或 URL。

## 实施结果

- 三个旧路由均已接入 `TriageApplicationService`，旧接口仍不做 Safety-first 脱敏，保持兼容语义。
- 新增 service 覆盖 triage/follow-up/assistant 的单测；全量 pytest 为 `100/100`。
- 快照和 Safety Evaluation 基线未变化。
