# 2026-09-10 CI 与分层依赖切片

## 目标

完成 P1-S5：建立 runtime/dev/data-tools 依赖层和可复现的本地/GitHub Actions 质量门禁，不改变医学业务行为。

## 已完成

- 新增 `requirements-dev.txt`，只增加 pytest；保留 `requirements.txt` 为 runtime，`requirements-data.txt` 为数据工具层。
- 新增 `pyproject.toml` pytest discovery 配置。
- 新增 `tests/test_model_smoke.py`，覆盖本地模型可加载、输入不足和模型缺失降级。
- 新增 `.github/workflows/quality.yml`，覆盖 Python 编译、pytest、JS 语法、数据质量报告和稳定快照漂移检查。
- 更新 README、章程、当前架构、质量门禁、评分卡、风险和迁移记录。

## 验证

- `uv run --with-requirements requirements-dev.txt python -m pytest`：12/12 通过。
- `python3 -m py_compile ...`：修改后的 Python 模块通过。
- `node --check static/js/app.js`：通过。
- `python3 -m data_validation.validate_datasets --data-root data --output-dir data_validation`：扫描 27 个文件、187 个已登记异常；未修复原始数据。
- `run_snapshot.py` 连续运行两次：SHA-256 均为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- `git diff --check`：通过。

## 未完成与下一步

- GitHub Actions 远端首次运行需在本切片提交并推送后确认。
- 数据质量异常、完整 viewport/console audit、医院逐字段 provenance、完整 legacy parity 和 P2 医学边界拆分仍未完成。

## 回滚

删除本切片新增的依赖、测试、workflow 和文档，或回退本切片提交；不需要改动原始数据、模型文件或分诊规则。
