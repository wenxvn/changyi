# 常医智导前端质量门禁计划

状态：已完成（静态 workflow 接入）  
日期：2026-09-10  
变更等级：L2（CI 配置和前端验证命令；不改变运行时业务）

## 目标

将并行 `frontend/` 的 TypeScript 类型检查、边界测试和生产构建纳入既有 GitHub Actions `quality` workflow，使每次 push/pull request 都能发现前端契约边界、编译和打包回归。

## 非目标

- 不切换 legacy 默认入口，不新增部署、发布或第三方服务。
- 不将本地浏览器视觉检查伪装成 CI E2E；Playwright、截图 baseline、键盘/对比度仍另立门禁。
- 不修改医学规则、推荐权重、模型文件、数据质量报告或前端业务行为。

## 实施

- 新增独立 `frontend` job，使用 Node 22、`npm ci` 和 `frontend/package-lock.json` 缓存。
- 按 `typecheck → test → build` 顺序执行，与本地 `frontend/package.json` scripts 一致。
- 保留现有 Python job 的矩阵、Safety Evaluation、数据质量和稳定快照流程。

## 验收与回滚

本地 `npm run typecheck`、`npm run test`、`npm run build` 已通过；workflow YAML 已静态检查。远端首次运行需要推送后确认。若 CI 环境失败，可独立回退新增 `frontend` job，不影响 Python/legacy 质量门禁。
