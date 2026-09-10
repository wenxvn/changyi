# 计划：抽取医生结果解释与组装边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成
- 关联 ADR：`docs/decisions/0004-recommendation-domain-boundaries.md`

## 目标

完成 P2-S3 医生推荐的下一小步：将普通医生候选的解释生成和结果对象组装移入无 Web/数据读取依赖的纯函数，缩小 `enhanced_recommend_doctors` 的展示组合职责。

## 非目标

- 不改变医生候选过滤、医院查询、交通/距离、推荐权重、资源策略、错配惩罚或急症兜底召回。
- 不修改医学规则、Safety Gate、模型调用、API 字段名称或排序顺序。
- 不把内部 `fairness`、resource tier 或 explanation 推断包装成医疗事实或公平性承诺。

## 当前基线

- 普通医生候选的 `reasons`、`scores`、`capability_indices` 和结果字段仍在 `app.py` 内联组装。
- 稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 方案与边界

- 新增 `backend/app/domain/recommendation/candidate.py`，提供医生解释和普通候选结果 builder。
- builder 只接受医生对象、显式 feature/penalty/strategy 结果和模型版本；不读取全局数据。
- 急症兜底召回保持在 `app.py`，本切片仅覆盖普通候选循环的结果组装。

## 原子步骤

- [x] 建立医生 explanation/result builder 并接入 legacy `enhanced_recommend_doctors`。
- [x] 新增解释阈值、fallback、截断和结果字段测试。
- [x] 运行全量测试、API smoke、快照、静态检查和数据质量检查。
- [x] 更新架构、评分卡、风险、进度、历史和 review。

## 验收标准

- 推荐稳定快照哈希不变，legacy/v1 字段和排序不变。
- candidate 模块不依赖 Web、数据加载、模型或全局数据。
- 急症兜底、资源策略和免责声明路径保持原位置与语义。

## 回滚

回退本切片即可恢复医生结果解释和组装在 `app.py` 内联执行，不涉及数据、模型、规则或 API。

## 验证结果

- 全量 pytest：49/49 通过。
- API 主 smoke：11/11 通过；另加空输入 400 与未知路径 404 边界检查 2/2 通过。
- Safety Evaluation Set：16 个 case，Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`；既有 `review_required` 缺口保持不变。
- Python compile、Node check、characterization snapshot、数据质量和 `git diff --check` 通过；快照 SHA-256 仍为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- 急症兜底召回未迁移，仍由 legacy 分支使用原有字段和文案。
