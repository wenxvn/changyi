# 2026-09-10 推荐排序纯函数边界

## 目标

完成 P2-S3 第一小步：抽取推荐排序共享的纯函数，减少 `app.py` 的隐式耦合，为后续 candidate/feature/score/rerank/explain 分层建立单一边界。

## 已完成

- 新增 `backend/app/domain/recommendation/scoring.py`。
- 抽取 `clamp`、`as_text`、医生职称分数、内部资源分层和科室关系判断。
- `app.py` 通过兼容导入保留旧私有函数名称，医院/医生排序仍由原组合路径执行。
- 新增正例、负例和数值边界测试；未修改推荐权重、数据或 API 字段。

## 验证

- 全量 pytest：27/27 通过。
- 推荐 characterization snapshot 哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- API smoke：11/11 通过。
- `py_compile`、`node --check`、数据质量和 `git diff --check` 通过。

## 未完成与下一步

完整推荐组合仍在 `app.py`，包括医院/医生 candidate、feature 计算、score、风险惩罚、diversity rerank 和 explanation。下一步继续小步拆分，并重新检查 `fairness` 字段的实际语义后再决定对外命名。

## 回滚

回退本切片即可恢复纯函数在 `app.py` 中的位置，不涉及数据、医学规则、模型或 API。
