# 2026-09-10 v1 legacy adapter 边界进度

## 本次完成

- 新增 `backend/app/api/v1/legacy_adapter.py`，集中管理 legacy handler 的延迟解析与调用。
- v1 blueprint 不再内联 importlib 适配逻辑，仍通过同一 legacy 业务实现，避免规则复制和导入循环。
- 新增 v1 error envelope、未声明字段、坐标/Region、v1/legacy 急症状态、目录来源标记和 lazy handler 契约测试。

## 验证

- 目标测试：13/13 通过。
- 全量 pytest：74/74 通过。
- API smoke：13/13 通过（含 400/404 边界）。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

完整 legacy route parity、应用服务层、认证/生产安全、医院 provenance 和前端模块化仍未完成；本切片只整理适配器，不代表 v1 已与所有 legacy 路由完成等价迁移。

## 回滚

恢复 `backend/app/api/v1/routes.py` 的 `_legacy_handler` 实现并移除 adapter/契约测试/记录即可；不影响 legacy 业务实现。
