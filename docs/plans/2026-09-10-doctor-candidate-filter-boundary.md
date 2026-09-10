# 计划：抽取医生 candidate 过滤边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成
- 关联 ADR：`docs/decisions/0004-recommendation-domain-boundaries.md`

## 目标

完成 P2-S3 医生 candidate 的下一小步：将查询词构建、科室关系过滤和无科室时的关键词召回抽取为不依赖 Web、数据仓库或模型的纯函数。

## 非目标

- 不改变医生/医院数据、候选召回条件、排序、score、资源策略、解释文案或急症兜底。
- 不改变医学规则、模型调用、API 字段或 Safety Gate。
- 不把关键词命中解释为医学诊断或医生官方专长承诺。

## 当前基线

- `enhanced_recommend_doctors` 在 `app.py` 内联构建查询词并过滤 `REAL_DOCTORS`。
- 稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 方案与边界

- 新增 `backend/app/domain/recommendation/candidates.py`，提供显式 `condition`、疾病-科室映射、htriage 摘要和医生对象输入的纯函数。
- `app.py` 继续负责加载数据、调用模型/分诊并遍历医生，只委托查询词构建和单医生 candidate 判断。
- 通过查询词正/反例、科室关系、无科室关键词召回、全量测试和快照验证行为保持。

## 原子步骤

- [x] 建立医生 candidate helper 并接入 legacy `enhanced_recommend_doctors`。
- [x] 新增查询词、科室过滤和关键词召回正/反例测试。
- [x] 运行全量测试、API smoke、快照、静态检查和数据质量检查。
- [x] 更新架构、评分卡、风险、进度、历史和 review。

## 验收标准

- 推荐稳定快照哈希不变，legacy/v1 字段和排序不变。
- candidate helper 不依赖 Web、数据加载、模型或全局数据。
- 查询词命中只作为候选召回信号，不新增医学事实或诊断承诺。

## 回滚

回退本切片即可恢复 candidate 过滤在 `app.py` 内联执行，不涉及数据、模型、规则或 API。

## 验证结果

- 全量 pytest：52/52 通过。
- 推荐 characterization snapshot 哈希仍为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`；Python compile、Node check 和 `git diff --check` 通过。
- 查询词合并、相关/不相关科室、无科室关键词召回测试通过；未改变医生数据、score、资源策略或 API 字段。
