# 质量门禁

质量门禁按变更等级增加，不因任务很小或“只是重构”而跳过必要的行为验证。

## 通用门禁

- [ ] 目标、非目标、验收标准和变更等级已记录。
- [ ] 未覆盖用户已有改动，未提交秘密或真实敏感信息。
- [ ] 相关文档、ADR、风险和进度已同步。
- [ ] `git diff` 和 `git status` 已检查，生成物和缓存符合 `.gitignore`。
- [ ] runtime/dev/data-tools 依赖分层明确；CI workflow 与本地门禁命令保持一致。

## 后端门禁

- [ ] 修改后的 Python 文件通过 `python3 -m py_compile`。
- [ ] Flask 应用可以导入，关键 GET/POST 路径至少有 smoke test。
- [ ] 成功、空输入、非法输入、缺少数据、404 和内部降级路径已检查。
- [ ] API 响应字段、状态码和错误消息的变更已记录。

## 医学/模型门禁（L3）

- [ ] 正常症状、症状不足、已知疾病、红旗症状和低置信度样例已验证。
- [ ] 模型不可用、模型文件损坏或字段缺失时有安全降级。
- [ ] 推荐解释没有把推断写成事实，没有移除人工复核和免责声明。
- [ ] 数据集、模型版本、训练报告和指标有来源与时间。
- [ ] 需要时由用户指定的医学/业务审核者确认，而不是由 agent 自行假设。

## 前端门禁

- [ ] `npm run typecheck`、`npm run test`、`npm run build` 通过；修改测试脚本时运行 `node --check frontend/test/frontend-boundaries.test.mjs`。
- [ ] 加载态、空态、错误态、移动端/窄屏和红旗提示已检查。
- [ ] API 错误不会被静默吞掉或渲染成成功结果。
- [ ] UI 变化按 `imprint` skill 更新一致性记录；第一次建立基线先 audit、再确认。

## 数据门禁

- [ ] JSON/CSV 可解析，必需字段和数量变化已检查。
- [ ] `data_validation` JSON/Markdown 报告已生成；异常已登记，未被自动修复或当作放行结论。
- [ ] 数据来源、更新时间、许可证/权限、脱敏状态和生成命令已记录。
- [ ] 不会静默覆盖原始数据；生成物和正式数据有明确边界。

## CI 门禁

- [ ] `.github/workflows/quality.yml` 在 push/pull request 上运行 Python 编译、pytest、模型 smoke、Safety Evaluation baseline、数据质量和稳定快照检查。
- [ ] `.github/workflows/quality.yml` 在 push/pull request 上运行 frontend `npm ci`、typecheck、boundary tests、build、Playwright Chromium smoke 和截图 artifact。
- [ ] 质量报告允许已登记异常在非 strict 模式下被记录，但生成报告或表征快照发生未解释漂移时 CI 失败。

## 当前重构基线

当前本地基线为 167 个 pytest、17 个 frontend boundary tests 和 20 个 Playwright 用例；已运行 canonical v1 API、Safety Evaluation（142 cases，Recall 1.0 / FN 0 / Over-triage 0）、Grouped Near-Duplicate CV、Python 编译、frontend typecheck/build、数据质量扫描和稳定快照。数据扫描的 186 个异常仍为登记项，不作为放行结论；canonical snapshot 已同步 `excluded_evidence` / `routing_preferences` / `triage_scenario` / `visit_intent`。
