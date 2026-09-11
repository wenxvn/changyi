# 常医后端重构计划：Triage Application Service 边界

状态：已完成  
日期：2026-09-11  
变更等级：L3（分诊发布编排边界；仅行为保持，不修改医学规则、阈值、文案或排序）

## 目标

把 v1 triage/follow-up 的应用层编排从 `app.py` 路由兼容函数中移到独立 application service。service 只串联现有的 legacy triage、Safety Gate、Safety-first publication 和模型公开字段函数；Flask request、响应 envelope 和参数校验仍留在适配层。

## 非目标

- 不修改红旗关键词、分诊状态映射、追问规则、模型、推荐排序或医学文案。
- 不删除 legacy `/triage`、`/api/*` 或当前 v1 adapter；不改变 URL、状态码、字段或 envelope。
- 不在 service 中重新实现医学规则、前端判断或请求解析。

## 安全验收边界

- Emergency 与信息不足仍经过同一 Safety Gate 和 publication，疾病候选/模型输出的 abstain 行为保持不变。
- 既有 Safety Evaluation Set（16 case；当前 Red Flag Recall 0.9231、Under-triage 0.0769、Emergency False Negative 1）作为反例/基线，不因抽取而宣称放行。
- 低置信度、模型不可用、信息不足和人工复核字段继续由既有 legacy/domain 函数返回；本 slice 不改变降级策略。
- 必须通过 v1 triage/followup contract、Emergency 和信息不足测试、全量 pytest 与推荐快照。

## 实施步骤

1. 新增 `backend/app/application/triage.py`，定义注入式 triage payload/follow-up 编排 service。
2. 让 `app.py` 仅负责兼容依赖组装和 v1 request/response adapter，删除重复编排实现但保留兼容函数名。
3. 增加 service unit tests 和 v1 contract regression，确认 HTTP 输出不变。
4. 更新 architecture、migration/status、progress、history、review、risk 和 memory。
5. 运行 Python compile、pytest、Safety Evaluation、API smoke、快照和 `git diff --check`。

## 回滚

恢复 `app.py` 内部 `_v1_triage_payload`/follow-up 编排并移除 service 与测试即可；不影响旧入口、数据文件、模型和前端。
