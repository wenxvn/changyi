# Review：旧分诊路由收敛到 Triage Application Service

日期：2026-09-11  
范围：`backend/app/application/triage.py`、旧 triage/follow-up/assistant handlers、相关测试  
计划：[2026-09-11-legacy-triage-route-adapter.md](../plans/2026-09-11-legacy-triage-route-adapter.md)  
决策：[0011-legacy-triage-route-adapter.md](../decisions/0011-legacy-triage-route-adapter.md)

## 1. 计划对齐

结论：通过。三个旧分诊相关路由已复用 service，旧接口行为保持，v1 Safety-first 边界未被绕过。

## 2. 系统完整性

结论：通过。service 通过注入函数编排，不读取 Flask request，不实现新规则；旧路由仍负责输入校验和响应 envelope。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] Safety Evaluation 已知反例、医学审核、完整 legacy parity、结构化 follow-up API 和正式急诊路径仍开放。
- [P1] 旧接口仍是历史兼容输出，不应作为面向用户的 Safety-first 发布接口。
- [P2] 模型不可用/低置信度的更多 route-level 自动化覆盖仍可继续补充。

## 总结

本切片只完成分诊应用边界收敛，不宣称医学策略或生产安全发生改善。
