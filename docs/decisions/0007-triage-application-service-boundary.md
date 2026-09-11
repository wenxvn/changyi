# ADR-0007：以注入式 Application Service 编排 v1 Triage

状态：已接受  
日期：2026-09-11  
范围：`backend/app/application/triage.py` 与 v1 triage/follow-up 适配器

## 背景

当前 `app.py` 同时承载 Flask request 解析、v1 envelope、legacy triage 调用和 Safety-first 发布编排。继续在路由函数中叠加逻辑会让 API 边界难以测试，也容易在未来拆分时复制医学规则。

## 决策

- 新增 application service，只负责把现有函数按既定顺序编排成 triage 和 follow-up payload。
- service 通过构造函数注入分析、Safety Gate、publication、模型预测和 htriage 公开字段函数，避免 import legacy `app.py`，也不拥有医学规则。
- `app.py` 继续作为兼容 composition root：组装依赖、解析 `RecommendationRequest`、生成 v1 response envelope；旧函数名保留为薄 wrapper，便于回滚和旧调用方兼容。
- Emergency、信息不足、模型不可用和人工复核策略完全由既有函数决定；本 ADR 不是医学策略变更。

## 影响

正向影响：service 可被无 Flask 的 unit test 独立验证，路由责任变薄，后续 legacy route parity 有清晰接缝。代价：短期仍保留 `app.py` 薄兼容 wrapper 和注入式组装，完整旧路由收敛仍未完成。

## 未决事项

推荐 endpoint、结构化 follow-up answer API、交通刷新策略和完整 legacy route parity 仍需单独切片；不得借本 ADR 直接改变其业务语义。
