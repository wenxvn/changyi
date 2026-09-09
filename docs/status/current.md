# 当前项目状态

更新时间：2026-09-09

## 总体状态

- 状态：进行中，首轮基础设施切片待复核
- 当前阶段：竞赛迁移 Phase 0/1（Audit、Region Pack、数据边界、v1 兼容外壳）
- 当前分支：`main`
- 基线提交：`838d4db`（当前工作树基线）
- 本次工作流文件：已创建，当前变更尚未提交

## 已完成

- Git 仓库已初始化并推送到远端 `main`。
- 建立根级协作规则、项目章程、当前架构说明、ADR、历史、进度、风险和质量门禁。
- 读取并纳入项目已有的 `architect`、`imprint`、`recover`、`remember`、`review` skills。
- 明确医疗辅助、数据治理、渐进式拆分和会话交接边界。
- 建立竞赛工作区：产品、目标架构、数据溯源、模型/安全卡、评估、评分、演示、发布和迁移计划。
- 建立 `320400` active Region Pack；未来城市仅登记为未连接状态。
- 建立 `JsonDataLoader`、RegionRegistry、医生/交通 repositories 和应用配置工厂。
- 将旧推荐入口的组合逻辑收敛到一个 helper，并新增 `/api/v1` triage、followups、recommendations、hospitals、doctors 外壳。
- 建立 `data_validation`，输出带 SHA-256 和异常明细的 JSON/Markdown 质量报告。
- 将医院解析脚本改为显式输入/输出 CLI，移除 Windows 绝对路径依赖。

## 当前基线

| 领域 | 当前情况 | 证据 |
| --- | --- | --- |
| 后端 | Flask 单体，约 3,172 行 | `app.py` |
| 前端 | 单体 JS，约 4,351 行 | `static/js/app.js` |
| 样式 | 单体 CSS，约 7,174 行 | `static/css/style.css` |
| 数据 | 本地 JSON/CSV/模型和图片；11 份医生 JSON、2,100 条 | `data/`、`static/images/` |
| 依赖 | Flask、Flask-CORS | `requirements.txt` |
| 测试 | 9 个 stdlib 基础/数据边界测试；API smoke 已单独运行 | `tests/test_foundation.py` |
| CI | 暂无 | 仓库扫描结果 |
| 认证 | 演示登录，非生产认证 | `templates/index.html`、`static/js/app.js` |
| UI 规范 | 已完成静态/一次 desktop `imprint audit`；基线已确认并写入 `ui-registry.md`，已完成首个 token/手动轮播切片 | `ui-registry.md`、`docs/competition/2026-ai-medical/UI_AUDIT_BASELINE.md` |

## 当前未解决问题

- API 和关键纯函数已有可重复的字段快照，但模型不可用、低置信度和更多红旗反例仍需扩展。
- 推荐、分诊、症状模型和交通可达性逻辑仍在同一后端文件内交织。
- 前端依赖全局 `window.*` 状态，页面控制、API 请求和渲染耦合较高。
- 数据来源、许可证、更新时间和版本口径需要进一步补全。
- 生产级认证、授权、审计、隐私和部署安全尚未实现。
- 数据质量报告当前有 187 个异常，主要为公交疑似占位年份、6 条时间先后异常和 h6 计数不一致；未自动修复。
- 医院目录仍是 `app.py` 常量，逐字段 provenance 尚未完成；v1 医院读取接口明确标记为 pending。
- v1 路由已由 blueprint 统一注册，独立 factory 与 `app.py` 兼容入口均可访问；其业务实现仍通过延迟 legacy adapter，完整 legacy route 注册仍待后续拆分。
- UI 已完成一次 localhost desktop 运行态 audit：页面可加载、智能推荐和急症流程可见；完整 viewport 矩阵、独立 console 报告和静态资源 404 修复仍待后续切片。

## 本次验证

- 文档路径检查：通过。
- Python 语法编译：通过（`app.py`、脚本和症状模型模块）。
- JavaScript 语法检查：通过（`node --check static/js/app.js`）。
- Flask smoke test：系统 Python 仍缺少 Flask；使用 `uv run --with flask --with flask-cors` 临时环境通过 health/ready/regions、v1 triage/recommendations、旧推荐入口、400 和 404 边界。
- 最终 API smoke：9 项通过；急症样例的 v1 `triage_status=EMERGENCY`，且响应 envelope 字段稳定。
- 表征快照：连续运行两次 SHA-256 均为 `f25776076ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- 数据质量：`python3 -m data_validation.validate_datasets --data-root data --output-dir data_validation`，扫描 27 个文件、发现 187 个异常；报告已生成，未以 strict 作为放行门。

## 下一步

1. 扩展 P0-S2 纯函数/接口 snapshot，补模型不可用、低置信度和更多红旗反例。
2. 完成 P0-S4 的 viewport/console/full network audit，并按 `ui-registry.md` 继续小步视觉迁移。
3. 把 v1 triage/recommendation 组合逻辑移入 application/domain，保留旧路由 adapter。
4. 为医院目录补逐字段来源/许可/时间/脱敏元数据，再考虑激活正式资源。
5. 建立 pytest/CI/schema/model smoke 层，完成三层 review 后再继续前端改造。

## 阻塞与需要确认

当前没有必须阻塞实施的问题。以下事项会在对应阶段需要用户或领域审核者确认：

- 哪些医院/医生数据可以正式发布，哪些只能用于演示。
- 红旗症状和分诊等级的医学审核口径。
- 是否需要生产化认证、数据库和外部部署。
