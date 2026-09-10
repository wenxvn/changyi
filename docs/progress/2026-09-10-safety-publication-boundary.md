# 2026-09-10 Safety-first 发布边界进度

## 本次完成

- 新增 `backend/app/domain/triage/publication.py`，承载疾病候选/模型输出/急症追问的 Safety-first 降级和公共 payload 发布纯函数。
- `app.py` 保留红旗规则、四态状态判定、htriage 字段映射和路由适配，只调用 publication domain。
- 急症继续隐藏疾病候选和普通追问，信息不足继续隐藏疾病候选并保留人工复核语义，普通状态保持原对象返回行为。

## 验证

- 目标测试：22/22 通过。
- 全量 pytest：68/68 通过。
- API smoke：13/13 通过（含 400/404 边界）。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

医院 candidate 遍历、交通样本生成/cache 生命周期、API route adapter parity、医院逐字段 provenance、前端模块化和 Safety Evaluation 已知 review_required 项仍未完成；本切片未修改医学规则或评估口径。

## 回滚

恢复 `app.py` 原有 Safety-first helper 实现并移除 `publication.py`、测试和记录即可；不影响 Safety Gate 状态枚举与既有规则。
