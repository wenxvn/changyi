# 当前项目状态

更新时间：2026-09-12（P1 Final Evidence & Trust Closeout）

## 总体状态

- 状态：**P1 Closeout Complete**，可进入 P2 Care Routing Intelligence
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- Safety Gate 业务语义仅在新增红旗表达覆盖范围内做了最小扩展；未引入 LLM triage
- 产品定位保持 AI Care Routing，不是诊断系统

## P1 Closeout 要点

- **h6 数据一致性**：`doctors_h6.json` 的 `total_doctors` 由 82 对齐为 74（照片、provenance、unique name 均为 74）；`COUNT_MISMATCH=0`。
- **Safety Evaluation**：38 → **135** cases；覆盖口语红旗、错别字/噪音、否定/双重否定、时间信息、信息不足、矛盾信息、特殊人群。Red Flag Recall `1.0`、Under-triage `0.0`、Emergency FN `0`、Over-triage `0.0312`（question-form 过触发，已登记 `question-stroke-signs`）。
- **Grouped Near-Duplicate CV**：5-fold；同一 same-label component 不跨 train/validation；跨 split 近重复最大对数 `0`；跨折覆盖 41/41 类；mean Top-1 ≈ `0.084`。Trust Center 已展示，标注 offline prototype / not clinical validation。
- **Academic patient-fit**：`ENHANCED_WEIGHTS.academic = 0.00`（surgery/common/complex/first_visit）；SCI/基金/专利仅展示；回归测试证明仅改 academic 不改变 patient-fit 分数与 resource tier。
- **Provenance**：医生照片 provenance 升到 v2（区分 `public_url` / `original_source_url`，`original_image_url` 保持 null，不伪造 `SOURCE_VERIFIED`）；医院目录增加字段级 provenance；交通继续 `PROVISIONAL` 且 `rankable=false`。
- **数据质量**：30 datasets，**186** issues（`PLACEHOLDER_TIMESTAMP=180`，`TIME_ORDER=6`），只登记不自动修复。

## 当前基线

| 领域 | 事实 |
| --- | --- |
| Flask 入口 | `app.py` 兼容启动层；`backend/app/composition.py` 为组合根 |
| 正式前端 | `frontend/src/` React/TypeScript；`frontend/dist/` 由 Flask 提供 |
| 正式 API | `/api/v1/health`、`ready`、`regions`、`triage`、`triage/followups`、`recommendations`、`hospitals`、`doctors`、`summary`、`evidence`、`map` |
| 数据 | active Region Pack `320400`；11 份医生 JSON，运行时加载 2,100 条公开资料 |
| 医生照片 | h6 74/74、h11 201/201；provenance v2；UNVERIFIED 不写入 `photo_url` |
| 测试 | pytest **130**；frontend boundary tests 16；Playwright 20/20 |
| Safety | **135** cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0312`、Emergency FN `0` |
| 模型证据 | random / exact fingerprint / strict near-duplicate single split / **Grouped Near-Duplicate CV (5-fold)** |
| Academic 排序 | patient-fit 权重 `0.00`；展示 ≠ 推荐依据 |
| 交通 | bus/taxi/bike `PROVISIONAL`，`rankable=false` |
| 医院目录 | `data/regions/320400/hospitals/catalog.json`；含 `district` 与字段级 provenance；目录状态 `provisional` |

## 验证记录

- `.venv/bin/python -m pytest`：130 passed。
- `.venv/bin/python -m evaluation.safety.evaluate_safety`：135 cases；Recall `1.0`；Under-triage `0.0`；Over-triage `0.0312`；Emergency FN `0`。
- `.venv/bin/python -m evaluation.model.evaluate_grouped --write`：四种单次切分 + Grouped CV 已写入 `evaluation/model/`。
- `.venv/bin/python -m data_validation.validate_datasets --data-root data --output-dir data_validation`：30 文件、186 问题，未自动修复。
- `frontend`：`npm run typecheck`、`npm run test`、`npm run build` 通过。

## 未改变的风险

- Safety 固定样例不等于临床覆盖；仍属 `R-001`。Over-triage 已从 0 升至 0.0312，属可接受但需持续复核。
- 医院/医生来源与许可仍不完整（`R-002`）；医生照片仍为 `LEGACY_EXACT_MATCH` / `MANUAL_CONFIRMED`，非 `SOURCE_VERIFIED`。
- 数据质量 186 个异常未修复（`R-011`）；交通未过质量门。
- Grouped CV mean Top-1 很低，用于暴露泛化风险，不是“真实准确率只有 8%”的临床结论。
- 演示认证、CORS、隐私、审计和部署不具备生产安全属性（`R-003`、`R-007`、`R-013`）。

## 下一步

进入 P2 Care Routing Intelligence：服务端医生搜索/分页、Visit Intent、Resource Routing Preferences、本地收藏、provenance-aware import pipeline、推荐解释与 Accessibility。涉及医学或生产能力时按 L3/L4 另立计划。
