# 计划：抽取医院推荐 feature 边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成

## 目标

完成 P2-S3 第二小步：将医院推荐的能力匹配、等级归一化、可用性、质量、连续照护、特殊人群适配、历史 `fairness` 分数、风险惩罚和解释生成抽取到无 Web/数据读取依赖的 feature 模块，为后续 candidate/score/rerank 组合拆分建立可测试边界。

## 非目标

- 不修改医院/医生数据、交通样本、推荐权重、排序顺序、风险阈值或对外字段。
- 不迁移交通 repository、距离计算、完整 `recommend` 或 `enhanced_recommend_doctors`。
- 不把内部 `fairness` 改写成对外公平性承诺；本切片只保留历史计算名称以确保快照稳定。
- 不改变 Safety Gate、分诊、疾病模型或 legacy/v1 API。

## 当前基线

- 医院 feature 计算和解释函数仍集中在 `app.py`，被医院推荐和医生排序共同调用。
- 推荐稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- P2-S3 第一小步已抽取共享 scoring 纯函数，旧私有名称仍由兼容导入提供。

## 方案与边界

- 新增 `backend/app/domain/recommendation/features.py`，只接受显式医院字典、病情文本、分诊等级和分数，不导入 Flask、Region、repository、模型或全局数据。
- `app.py` 通过显式兼容导入使用 feature 函数，交通可达性与距离仍留在 legacy，避免跨越数据访问边界。
- 以 feature 单测、全量 API smoke 和 characterization snapshot 阻断静默排序变化。

## 原子步骤

- [x] 建立医院 feature 模块并接入 legacy 兼容导入。
- [x] 新增 feature 正例/负例和解释边界测试。
- [x] 运行全量测试、推荐/API smoke、快照、静态检查和数据质量检查。
- [x] 更新架构、评分卡、风险、进度、历史和 review。

## 验收标准

- 推荐稳定快照哈希不变，legacy/v1 API 字段和排序不变。
- feature 模块没有 Web、数据加载或模型依赖。
- feature 计算没有引入新的医学承诺，也不改变 `fairness` 的对外语义。

## 验证命令与结果

实施结果：后续复核发现 feature 直接正/反例测试未实际落地，已补充 `tests/test_recommendation_features.py`；与本轮 rerank 切片测试合并后全量 34 个 pytest 通过。API smoke 11 项通过；推荐 characterization snapshot 哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`；`py_compile`、Node check、数据质量和 `git diff --check` 通过。未修改推荐权重、数据文件、医学规则或 API 字段。

## 回滚

回退本切片即可恢复 feature 函数在 `app.py` 中的位置，不涉及数据、模型、规则或 API。
