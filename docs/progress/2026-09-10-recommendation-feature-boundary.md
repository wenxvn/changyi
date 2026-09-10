# 2026-09-10 医院推荐 feature 边界

## 目标

完成 P2-S3 第二小步：抽取医院推荐的显式 feature 计算和解释生成，保持完整排序行为不变。

## 已完成

- 新增 `backend/app/domain/recommendation/features.py`。
- 抽取医院能力匹配、等级归一化、可用性、质量、连续照护、特殊人群适配、历史 `fairness` 分数、风险惩罚和解释生成。
- `app.py` 通过兼容导入继续提供旧私有名称；交通、距离、repository 和完整排序组合仍在 legacy。
- 新增 feature 正例/负例测试，未修改推荐权重、数据或 API 字段。

## 验证

- 已补充 feature 正例/负例直接测试；与后续 rerank 测试合并后全量 pytest：34/34 通过。
- API smoke：11/11 通过。
- 推荐 characterization snapshot 哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- `py_compile`、`node --check`、数据质量和 `git diff --check` 通过。

## 未完成与下一步

医院/医生 candidate 生成、完整 score 组合、风险/多样性 rerank、交通 feature 和 explanation pipeline 仍未完全拆出；`fairness` 对外语义仍需审查。

## 回滚

回退本切片即可恢复 feature 函数在 `app.py` 中的位置，不涉及数据、模型、医学规则或 API。
