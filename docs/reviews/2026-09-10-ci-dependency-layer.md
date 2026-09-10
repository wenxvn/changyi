# Review：CI 与分层依赖门禁

- 日期：2026-09-10
- 关联计划：`docs/plans/2026-09-10-ci-dependency-layer.md`
- 变更等级：L2

## Layer 1 — 计划对齐

PASS

- 只建立依赖、测试和 CI 边界，没有修改医学规则、模型权重、推荐排序或原始数据。
- 本地命令与 GitHub Actions 步骤对应，回滚可以按新增文件/提交执行。

## Layer 2 — 系统完整性

PASS

- 12/12 pytest 通过，包含模型资产、输入不足和模型缺失降级 smoke。
- Python 编译、Node 语法、数据质量报告、稳定快照和 `git diff --check` 通过。
- 数据质量报告的 187 个异常仍被显式保留，没有通过 CI 绕过或自动修复。

## Layer 3 — 生产准备度

ISSUES FOUND

- GitHub Actions 远端首次运行尚未完成，当前只验证了本地等价命令。
- 项目仍不是生产系统；医院来源/许可、隐私最小化、认证部署、移动端矩阵和完整 legacy parity 仍开放。

## 问题清单

- `[Important]` 推送本切片后确认 workflow 在 Python 3.11/3.12 矩阵均通过；若失败，先修 CI 环境或依赖声明，不修改业务逻辑。
- `[Important]` 继续处理 R-001、R-002、R-004、R-011、R-012，不能用 CI 通过替代医学、数据或生产审核。

## 验证证据

- `requirements-dev.txt`、`pyproject.toml`、`tests/test_model_smoke.py`、`.github/workflows/quality.yml`。
- `docs/progress/2026-09-10-ci-dependency-layer.md` 和 `docs/status/current.md`。

## 结论

可以继续；先在远端确认 CI，再进入下一切片。
