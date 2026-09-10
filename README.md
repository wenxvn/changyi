# 常州市智能医疗推荐系统

这是一个面向常州市医疗资源的演示型智能推荐与分诊辅助系统。系统整合医院、医生、科室、交通可达性、症状模型和前端可视化，用于产品演示、数据建模和分诊辅助研究，不能替代医生诊断或临床决策。

## 先读什么

1. [协作与变更规则](AGENTS.md)
2. [工作流入口](docs/README.md)
3. [当前状态](docs/status/current.md)
4. [当前架构](docs/architecture/current-state.md)
5. [重构路线图](docs/plans/refactor-roadmap.md)
6. [风险登记表](docs/risks/register.md)
7. [2026 AI+医学竞赛工作区](docs/competition/2026-ai-medical/README.md)

## 当前实现

- 后端：Flask，主要入口为 `app.py`。
- API：旧 `/api/*` 兼容入口与 `/api/v1/*` 版本化外壳并存；v1 当前通过 legacy adapter 复用业务逻辑。
- 前端：服务端模板 `templates/index.html`、单体脚本 `static/js/app.js`、样式 `static/css/style.css`。
- 数据：`data/` 中 11 份医生 JSON、交通样本、模型和 `static/images/` 本地资源；当前 active Region Pack 仅为 `320400 · 常州市`。
- 模型：`data/symptom_disease_model/` 中的症状到疾病类别模型。
- 质量：运行 `python3 -m data_validation.validate_datasets --data-root data --output-dir data_validation` 可生成数据质量 JSON/Markdown 报告；异常只报告，不自动修复。
- 辅助 skills：`skills/architect`、`skills/imprint`、`skills/recover`、`skills/remember`、`skills/review`。

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

默认服务地址为 `http://127.0.0.1:5002`。当前登录页是演示登录，不代表已经实现了生产级身份认证。

开发测试和数据工具依赖分开安装：

```bash
pip install -r requirements-dev.txt    # pytest + runtime
pip install -r requirements-data.txt   # Pillow + runtime，构建数据图标时使用
python -m pytest
node --check static/js/app.js
python -m data_validation.validate_datasets --data-root data --output-dir data_validation
python -m evaluation.safety.evaluate_safety
```

GitHub Actions 质量门禁位于 `.github/workflows/quality.yml`，会复核 Python、pytest、模型 smoke、Safety Evaluation baseline、数据报告、稳定快照和浏览器脚本语法。

## 重要提醒

重构从“保留现有行为、建立基线、逐步拆分”开始，不进行没有记录的整体重写。任何涉及分诊、疾病预测、推荐排序、真实数据来源、患者隐私或安全控制的变化，都必须先更新相应计划、决策和风险记录，并通过质量门禁。
