# 当前项目状态

更新时间：2026-09-12（P1 Closeout + P2 Care Routing Intelligence）

## 总体状态

- 状态：**P2 Care Routing Intelligence 基线完成**
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- 产品定位：AI Care Routing；Safety 永远先于个性化

## P1 Closeout（已完成）

- h6 `total_doctors` 82→74，`COUNT_MISMATCH=0`
- Safety Evaluation 38→**135** cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0312`、Emergency FN `0`
- Grouped Near-Duplicate CV（5-fold）已写入评估报告并展示在 Trust Center
- Academic patient-fit 权重 `0.00`
- 医生照片 provenance v2；医院字段级 provenance；交通仍 `PROVISIONAL`

## P2 Care Routing Intelligence（已完成）

- **Doctor search / pagination**：`GET /api/v1/doctors` 支持 `q` / `hospital_id` / `hospital_name` / `department` / `title` / `page` / `page_size`（默认 24，最大 100）；响应含 `items/page/page_size/total/has_more/facets`；非法参数返回 400。
- **Resources Doctor Tab**：服务端筛选 + 分页加载更多；筛选变化回到 page 1；保留 URL state 与 `?doctor=` 详情。
- **Visit Intent**：`first_visit` / `follow_up` / `review_results` / `procedure_consult` / `unsure`；仅映射 ranking scenario，不进入 Safety Gate，不降低 triage，不绕过 Emergency；UI 在 Safety Gate 之后。
- **Resource Routing Preferences**：跨区 / 距离 / 连续复诊；默认关闭；`Emergency + 就近优先 → 仍 Emergency`。
- **收藏医生**：localStorage 仅 `doctor_id + created_at`；默认不影响排序；仅开启 continuity 后提升收藏医生。
- **Provenance-aware import pipeline**：`data/raw` 只读快照 + quality gate（VERIFIED/PROVISIONAL/INVALID，displayable/rankable）；应用层不读 raw。
- **Recommendation explanations**：科室匹配 / 距离（有位置时）/ 区域偏好 / 急诊字段措辞更谨慎；`excluded_evidence` 明确学术与交通未参与排序。
- **Accessibility**：visit intent / 偏好 / 收藏 / 加载更多的 aria、focus-visible、live region 边界测试。

## 当前基线

| 领域 | 事实 |
| --- | --- |
| 测试 | pytest **143**；frontend boundary tests **17**；Playwright **20/20** |
| Safety | **135** cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0312`、Emergency FN `0` |
| 数据质量 | 31 datasets，**186** issues（PLACEHOLDER_TIMESTAMP / TIME_ORDER） |
| 模型证据 | random / exact fingerprint / strict near-duplicate single split / Grouped CV |
| 医生 API | 服务端分页与筛选 |
| 收藏 | 本地、最小字段、非病历 |

## 验证记录

- `.venv/bin/python -m pytest`：143 passed
- `.venv/bin/python -m evaluation.safety.evaluate_safety`：135 cases；FN 0
- `.venv/bin/python -m evaluation.model.evaluate_grouped --write`
- `.venv/bin/python -m data_validation.validate_datasets --data-root data --output-dir data_validation`：186 issues
- `frontend`：typecheck / test / build / e2e 通过

## 未改变的风险

- Safety 固定样例 ≠ 临床覆盖（`R-001`）；Over-triage 0.0312 已登记
- 来源/许可不完整（`R-002`）；照片仍非 `SOURCE_VERIFIED`
- 交通未过质量门，不参与排序
- Grouped CV 低指标用于暴露泛化风险，不是临床结论
- 账号/云同步/实时急诊/实时公交仍明确不做

## 下一步

继续观察远端 CI；按需补真实来源核验、更多 Safety 表达覆盖、交通 license 后再评估 rankable。涉及医学或生产能力按 L3/L4 另立计划。
