# 常医智导

常医智导是面向常州市医疗资源检索、分诊辅助和可解释推荐的演示型 Web 系统。它不能替代医生诊断、处方、急救人员或临床决策。

## 当前结构

- `frontend/`：React + TypeScript + Vite 正式前端；构建产物由 Flask 从 `frontend/dist/` 提供。
- `backend/app/api/v1/`：唯一正式业务 API，统一返回 `{ data, meta, error }` envelope。
- `backend/app/application/`：分诊、推荐、资源目录和只读投影服务。
- `backend/app/domain/`：输入、Safety Gate、推荐、交通等可测试纯逻辑。
- `backend/app/infrastructure/`：本地 JSON/CSV、Region Pack、仓库和模型 adapter。
- `backend/app/composition.py`：Flask 组合根；根目录 `app.py` 仅保留启动和导入兼容。
- `data/`、`evaluation/`、`data_validation/`、`tests/`、`scripts/`：数据、评估、质量、测试和维护脚本。

正式前端只调用 `/api/v1/*`；旧模板、旧单体 JavaScript/CSS、旧 `/api/*` 路由和本地测试反馈写入端点已经移除。

## 启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cd frontend && npm ci && npm run build && cd ..
python app.py
```

打开 `http://127.0.0.1:5002`。构建后的 React shell 支持 `/`、`/triage`、`/resources`、`/map`、`/trust` 和 `/profile` 刷新。

## 验证

```bash
.venv/bin/python -m pytest
.venv/bin/python -m evaluation.safety.evaluate_safety
.venv/bin/python -m data_validation.validate_datasets --data-root data --output-dir data_validation
cd frontend
npm run typecheck
npm run test
npm run build
```

质量门禁位于 `.github/workflows/quality.yml`。数据质量报告只登记问题，不自动修复 187 个已知异常；Safety Evaluation 当前基线为 16 cases、Red Flag Recall `0.9231`、Under-triage `0.0769`、Over-triage `0.0`、Emergency False Negative `1`，这些不是临床发布结论。

## 入口文档

- [协作规则](AGENTS.md)
- [当前状态](docs/status/current.md)
- [当前架构](docs/architecture/current-state.md)
- [风险登记](docs/risks/register.md)
- [质量门禁](docs/quality/quality-gates.md)
- [重构变更记录](docs/REFACTOR_CHANGELOG.md)
- [后续 backlog](docs/POST_REFACTOR_BACKLOG.md)
