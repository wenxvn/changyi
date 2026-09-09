# 2026-09-09 竞赛迁移基础切片

## 目标

完成首轮竞赛工作区、审计证据、Region Pack、数据边界和 v1 兼容外壳，不改变医学规则、模型文件或推荐权重；UI 仅按已确认基线完成低风险收敛。

## 已完成

- 新增 `docs/competition/2026-ai-medical/` 的竞赛文档与迁移计划。
- 新增 `backend/app/` 配置、应用工厂、RegionRegistry、JsonDataLoader 和医生/交通 repositories。
- 激活 `320400` 常州 Region Pack；南京、苏州、上海仅作为 future pack 登记。
- 旧 `/api/recommend` 与 `/api/recommend/enhanced` 共享推荐组合函数；v1 blueprint 统一提供 triage、追问、推荐、医院、医生外壳，并通过延迟 adapter 复用现有组合逻辑。
- 新增数据质量 CLI 和报告；当前 27 个文件、187 个异常均只报告不修复。
- 修复医院解析脚本的 Windows 绝对路径假设；图标脚本改为可选字体参数。
- 负责人确认 UI 基线建议；建立 `ui-registry.md`，完成语义 token 别名、统一 `:focus-visible` 和首页手动轮播切片。

## 验证

- `python3 -m py_compile`：修改后的 Python 模块通过。
- `node --check static/js/app.js`：通过。
- `python3 -m unittest tests.test_foundation`：9/9 通过。
- `uv run --with flask --with flask-cors ...`：health/ready/regions、v1 triage/recommendations、legacy recommend、400/404 smoke 通过。
- 最终 API smoke 9 项通过，急症样例返回 `triage_status=EMERGENCY`；稳定快照连续两次哈希一致。
- 数据报告已生成到 `data_validation/data_quality_report.json` 和 `.md`。

## 未完成与下一步

- P0-S2 已生成稳定字段 snapshot；P0-S4 已做一次 desktop 运行态 audit，基线已确认并完成首个 UI 收敛切片；完整 viewport/console 仍待完成。
- 医院目录逐字段 provenance、模型不可用/低置信度降级的自动化覆盖、CI 和完整 legacy route factory parity 未完成。
- 数据报告的 187 个异常不能作为正式发布放行；需按 R-002/R-005/R-009 继续治理。
- UI 已做一次 localhost desktop audit 并验证急症结果显著性；已知定位超时降级和 favicon/Leaflet 图片 404 保留在后续问题清单。
