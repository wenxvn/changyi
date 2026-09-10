# 计划：建立 CI 与分层依赖门禁

- 日期：2026-09-10
- 变更等级：L2
- 状态：已完成

## 目标

落地迁移计划中的 P1-S5：把运行时、开发测试和数据工具依赖分层，并建立可在本地与 GitHub Actions 复现的质量门禁，为后续 application/domain 拆分提供可靠反馈。

## 非目标

- 不修改分诊、症状标准化、模型权重、推荐排序或医疗文案。
- 不修复或改写现有原始数据及 187 个已登记质量异常。
- 不引入数据库、微服务、生产认证或部署平台。
- 不把现有模型指标升级为医学准确率或生产可用性结论。

## 当前基线

- `requirements.txt` 只有 Flask 与 Flask-CORS。
- 已有 9 个 stdlib 基础/数据边界测试、稳定字段快照和数据质量 CLI，但没有正式 dev 依赖或 CI workflow。
- 模型降级代码存在，但没有独立的模型加载/输入不足 smoke 测试。
- 数据质量报告允许非 strict 模式报告异常；现有异常不作为本切片的放行失败条件。

## 方案与边界

- 保持 `requirements.txt` 为运行时层；新增 `requirements-dev.txt` 承载 pytest。
- 保持 `requirements-data.txt` 为数据工具层，并在文档中明确安装场景。
- 新增 `.github/workflows/quality.yml`，执行 Python 编译、pytest、模型 smoke、数据质量报告、表征快照和 JS 语法检查。
- CI 对报告/快照执行工作树 diff 检查，防止生成物漂移；质量报告中的已知异常仍由报告登记，不通过 `--strict` 阻塞本切片。
- 模型 smoke 只验证本地资产可加载、输入不足可返回辅助性降级和缺失模型可返回 `available=false`，不验证医学真值。

## 原子步骤

- [x] 新增开发依赖、pytest 配置和模型 smoke 测试。
- [x] 新增 GitHub Actions 质量 workflow，覆盖 Python/JS/数据/模型/快照门禁。
- [x] 更新 README、状态、路线图、质量门禁、进度、风险和复核记录。
- [x] 运行本地完整门禁并检查生成物、秘密和工作树。

## 验收标准

- `pytest` 可发现并通过现有测试与新增模型 smoke。
- `python3 -m py_compile` 覆盖所有修改后的 Python 模块；`node --check static/js/app.js` 通过。
- 数据质量报告仍可重生成，异常数量明确记录且原始数据无变化。
- 稳定快照连续运行结果一致。
- CI workflow 不依赖本机路径、不上传敏感数据、不自动修复数据。

## 验证命令与结果

完成结果：pytest 12/12、Python 编译、Node check、数据质量报告和快照检查均通过；workflow 已静态核对，远端运行待推送后确认。

## 风险、回滚和记录动作

- 风险：CI 环境依赖下载或 Python 版本差异导致环境失败；使用明确版本范围和矩阵，必要时只回滚 workflow，不改业务代码。
- 风险：模型/报告生成物漂移暴露现有基线问题；先记录差异，禁止在 CI 中覆盖或修复正式数据。
- 完成后更新 `docs/status/current.md`、`docs/progress/`、`docs/reviews/`、`docs/history/` 和 `docs/risks/register.md`。
