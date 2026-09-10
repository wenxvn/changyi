# 2026-09-10 医院候选遍历边界历史

- 目标：将医院推荐的逐候选上下文准备从 Flask 入口拆出。
- 实施：新增 `build_hospital_candidates`，显式注入距离、可达性、交通访问和单候选组合回调；保留 rerank、数据加载和缓存边界。
- 结果：目标回归 35/35、全量 pytest 85/85、API smoke 13/13、Safety Eval、编译、数据校验、快照和 diff check 通过。
- 风险：交通样本仍为演示数据，`used_in_ranking` 只代表既有 ranking policy；不表示实时路况或接诊能力。
