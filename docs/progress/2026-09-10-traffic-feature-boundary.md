# 2026-09-10 交通 feature 与可达性 score 边界

## 目标

抽取医院交通摘要和可达性 score，明确交通展示字段与排序字段的边界。

## 已完成

- 新增 `backend/app/domain/recommendation/traffic.py`。
- `app.py` 保留交通样本 map/cache 和医院 ID 查找，仅调用纯 payload/score helper。
- 公交/出租车仍按原场景参与普通/初诊排序；骑行只作为展示字段；急症/较重仍按距离优先。

## 验证

- 全量 pytest：56/56 通过。
- API smoke：13/13 通过；Safety Evaluation Set：16 个 case，既有 baseline 保持。
- 推荐 characterization snapshot 哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`；Python compile、Node check、数据质量和 `git diff --check` 通过。

## 未完成与下一步

交通样本加载/map/cache、医院 candidate 组装和急症兜底 explain 仍在 legacy。

## 回滚

回退本切片即可恢复交通摘要和可达性 score 在 `app.py` 内联执行。
