# 计划：抽取医院 candidate 结果组装边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成
- 关联 ADR：`docs/decisions/0004-recommendation-domain-boundaries.md`

## 目标

将医院推荐候选的稳定结果对象组装移入纯函数，继续缩小 `recommend` 的 legacy 组合职责；医院遍历、距离、交通样本查找和 feature 计算保持原位。

## 非目标

- 不改变医院候选集合、距离公式、交通数据、feature、score、rerank、解释文案或 API 字段。
- 不迁移医院目录、交通 map/cache、API route、医学规则或 Safety Gate。
- 不将候选分数或解释包装成医院官方承诺。

## 当前基线

- `recommend` 在 `app.py` 内联组装医院候选字典，包含 score、feature snapshot、交通字段、模型版本和 explanations。
- 稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 方案与边界

- 在 `backend/app/domain/recommendation/candidate.py` 增加 `build_hospital_recommendation_result`。
- builder 只接受显式医院对象、距离、已计算分数、feature、权重、模型版本和解释列表，不读取全局数据。
- `app.py` 继续负责候选生成和 rerank；只委托结果字典组装。

## 原子步骤

- [x] 建立医院 candidate result builder 并接入 legacy `recommend`。
- [x] 新增医院结果字段、精度和解释保留测试。
- [x] 运行全量测试、API smoke、快照、静态检查和数据质量检查。
- [x] 更新架构、评分卡、风险、进度、历史和 review。

## 验收标准

- 推荐稳定快照哈希不变，legacy/v1 字段和排序不变。
- candidate builder 不依赖 Web、数据加载、模型或全局数据。
- 医院来源、交通样本和解释的事实边界保持现有免责声明与记录。

## 回滚

回退本切片即可恢复医院 candidate 结果组装在 `app.py` 内联执行，不涉及数据、模型、规则或 API。

## 验证结果

- 全量 pytest：58/58 通过。
- API 主 smoke：11/11 通过；另加空输入 400 与未知路径 404 边界检查 2/2 通过。
- Safety Evaluation Set：16 个 case，Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`；既有 `review_required` 缺口保持不变。
- Python compile、Node check、characterization snapshot、数据质量和 `git diff --check` 通过；快照 SHA-256 仍为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- 医院对象、feature、交通摘要、模型版本、解释列表和分数精度保持原字段结构。
