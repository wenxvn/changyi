# 历史：Frontend Trust Center 首版

日期：2026-09-10

## 事件

在不改变 legacy `/`、旧 API、医学规则、模型文件和推荐快照的前提下，将并行前端 `/trust` 从 shell 空态推进为只读可信证据页，并新增 `/api/v1/evidence` 作为唯一数据边界。

## 事实

- 证据服务读取当前仓库已有的 `evaluation/safety`、`data/symptom_disease_model`、`data_validation` 和 `data/regions/320400/manifest.json`。
- 当前运行结果为 16 个 Safety Case、Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Emergency False Negative `1`；模型报告为 41 类、131 词表、Top-1 `0.972972...`、Top-3 `1.0`，页面均从 API 渲染。
- 当前数据质量报告登记 27 个数据集条目和 187 个问题；医院目录仍 `migration_pending`，医生资料仍 `public_source_mixed`。
- 评测、模型和数据均在页面上标注为原型阶段/离线证据，不作为临床验证或发布放行。

## 验证

后端 pytest 87 passed，前端边界测试 5/5，TypeScript/build/legacy JS 语法检查通过；浏览器 desktop 与 390×844 mobile 已检查真实加载和布局。

## 回滚

删除或回退本切片新增的 evidence service、v1 route、Trust 页面与对应文档即可；不需要回退已有资源、triage 或 legacy 代码。
