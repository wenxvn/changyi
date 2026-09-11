# Review：Triage Application Service

日期：2026-09-11  
范围：`backend/app/application/triage.py`、`app.py` v1 triage/follow-up wrappers 和 service tests  
计划：[2026-09-11-triage-application-service.md](../plans/2026-09-11-triage-application-service.md)  
决策：[0007-triage-application-service-boundary.md](../decisions/0007-triage-application-service-boundary.md)

## 1. 计划对齐

结论：通过。

- triage/follow-up 编排已移入独立 service；Flask request/response 责任仍在 adapter。
- service 没有增加医学策略，兼容 wrapper、v1 envelope 和 legacy route 均保留。

## 2. 系统完整性

结论：通过。

- application service 通过注入依赖避免导入 `app.py`，不拥有红旗规则、模型加载、请求解析或前端逻辑。
- Emergency 与信息不足状态继续使用现有 Safety Gate/publication；unit 和 API contract 覆盖 abstain/投影边界。
- 依赖注入使调用顺序和安全发布可以在无 Flask 的测试中复核。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 阻断。

- [P1] Safety Evaluation 已知 under-triage、完整 route parity、推荐 service 和结构化 follow-up answer API 仍开放。
- [P1] 医学规则变化仍需单独 L3 计划、样例/反例和领域审核；本切片不替代审核。
- [P2] `app.py` 仍是 composition root，后续需避免 service 依赖反向回 import legacy。

## 总结

Triage Application Service 首版达到行为保持的重构目标，可作为继续收敛 v1 route adapter 的边界；不能单独宣称医学安全或生产 ready。
