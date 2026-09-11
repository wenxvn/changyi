# 2026-09-11：抽取 Triage Application Service

## 背景

v1 triage/follow-up 的 request 处理、业务编排和 envelope 兼容逻辑集中在 `app.py`，后续拆分容易在边界处复制医学逻辑。

## 处理

- 新增注入式 `TriageApplicationService`，只编排既有 legacy/domain 函数，不导入 Flask 或重新实现规则。
- 将 triage payload 和 follow-up projection 改为 service 调用，保留 `_v1_triage_payload` 等兼容 wrapper。
- 用 fake dependencies 独立验证 Emergency publication/abstain 顺序和 follow-up 字段投影。

## 结果

91/91 pytest 通过，v1/legacy Emergency、Safety-first 和推荐快照保持；完整推荐 service 和 legacy route parity 仍开放。
