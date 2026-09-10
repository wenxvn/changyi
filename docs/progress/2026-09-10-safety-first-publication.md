# 2026-09-10 v1 Safety-first 公共输出

## 目标

把 Safety Gate decision 接入 `/api/v1` 的公共发布边界：急症或信息不足时不公开疾病候选/模型概率，急症不继续展示普通追问，同时保留安全提示和资源方向。

## 已完成

- 新增 v1 publication helper，对 triage、htriage 和 disease prediction 做安全优先的浅拷贝脱敏。
- `/api/v1/triage` 与 `/api/v1/recommendations` 已接入；legacy `/api/*` 保持原输出以便后续 parity 比较。
- 急症输出保留红旗标签、急诊照护等级、免责声明和医院推荐，疾病预测标记 `abstained`，普通 follow-up 置为 deferred。
- 信息不足输出保留补充信息问题，不把当前 legacy `不舒服` 的普通倾向误记为修复。

## 验证

- 全量 pytest：23/23 通过。
- v1 急症 triage/recommendations 公共输出测试通过，疾病候选数组和预测列表为空。
- Safety Evaluation：Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`；输出保护没有被计作规则召回提升。
- legacy characterization snapshot 哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- `py_compile`、Node check、数据质量和 `git diff --check` 通过。

## 未完成与下一步

legacy `/api/*` 仍保留原候选输出，待 API adapter parity 时统一发布边界；`喘不上来` 的红旗漏检和 `不舒服` 的信息不足降级仍须医学审核后另立 L3 规则修复。

## 回滚

回退本切片即可恢复 v1 原始候选发布；不涉及数据、模型、红旗规则、推荐权重或 legacy API。
