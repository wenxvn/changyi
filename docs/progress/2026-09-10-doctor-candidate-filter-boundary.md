# 2026-09-10 医生 candidate 过滤边界

## 目标

抽取医生查询词构建、科室关系过滤和无科室关键词召回，保持医生候选集合不变。

## 已完成

- 新增 `backend/app/domain/recommendation/candidates.py`。
- `app.py` 继续负责模型/分诊摘要、数据加载和遍历，只调用纯 candidate helper。
- 覆盖文本拆分、疾病映射、htriage 摘要、相关/不相关科室和关键词 fallback。

## 验证

- 全量 pytest：52/52 通过。
- 推荐 characterization snapshot 哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- Python compile、Node check 和 `git diff --check` 通过；未修改医生数据、score、资源策略或 API 字段。

## 未完成与下一步

医院 candidate 组装、交通样本 map/cache、急症兜底 explain 和 API route adapter parity 仍未完全拆出。

## 回滚

回退本切片即可恢复医生 candidate 过滤在 `app.py` 内联执行。
