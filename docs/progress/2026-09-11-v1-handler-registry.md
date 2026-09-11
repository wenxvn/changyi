# 2026-09-11 v1 Handler Registry 进度

## 本次完成

- v1 blueprint 的兼容 handler 已由根级 composition 显式注册到 Flask extension。
- `legacy_adapter` 有 context 时优先使用 registry，无 context/未注册时保留旧 lazy import fallback。
- 增加 registry contract test，确认 triage/map handler 解析到已注册函数。

## 验证

- Python compile：通过。
- 全量 pytest：`109/109` 通过。
- v1 API smoke、characterization snapshot 和 Safety Evaluation：基线保持。

## 未完成与下一步

完整 factory 独立 composition、剩余 legacy route parity、正式急诊路径、逐字段 provenance、E2E/视觉矩阵和远端 CI 仍开放。

## 回滚

恢复 `legacy_adapter` 直接 import `app` 并移除 registry 注册与测试即可。
