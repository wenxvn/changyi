# 当前项目状态

更新时间：2026-09-11

## 总体状态

- 状态：P0 正确性与产品闭环完成；本轮完成 P1 Product Completion + Evidence Hardening
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- Safety Gate 业务语义未改动

## 本轮 P1 收口

- 仓库卫生：删除根目录 Agent Prompt `1.md` 与 `qa-screenshots/`；截图改由 Playwright / CI artifact 保存，不再长期入库。
- 医生照片：新增统一 `DoctorAvatar`，在资源列表、医生详情、推荐医生卡片使用 `photo_url`，加载失败回退姓名首字。
- 医院 Logo：新增统一 `HospitalLogo`，在医院列表、医院详情、推荐医院卡片、地图预览使用已入库 icon；失败回退 Building 图标。
- 资源高级筛选：医院等级/类型；医生医院/科室/职称；与关键词组合；URL 可保留筛选与选中详情。
- 专家偏好：分诊结果区暴露 `system / wish_expert / no_expert` 三档，默认 system；不改变 Safety Gate。
- 模型证据：在 random 与 exact fingerprint 之外新增 Near-duplicate Group Split（同标签 component 为主，全局 component 作对照）；Trust Center 展示四种切分与跨 split 近重复计数。
- 交通质量门：`TransitQualityGate` 将公交/出租车/骑行数据分类；当前公交为 `PROVISIONAL` 且 `rankable=false`，可达性回退直线距离，站点信息仅作参考展示。
- 语音输入：浏览器 SpeechRecognition 仅做 Speech→Text 写入输入框，需用户确认后提交；不支持时明确提示。
- 浏览器 QA：Playwright 覆盖桌面 1440/1280、平板 768、移动 390，以及定位拒绝与语音 unsupported fallback。

## 当前基线

| 领域 | 事实 |
| --- | --- |
| Flask 入口 | `app.py` 兼容启动层；`backend/app/composition.py` 为组合根 |
| 正式前端 | `frontend/src/` React/TypeScript；`frontend/dist/` 由 Flask 提供 |
| 正式 API | `/api/v1/health`、`ready`、`regions`、`triage`、`triage/followups`、`recommendations`、`hospitals`、`doctors`、`summary`、`evidence`、`map` |
| 数据 | active Region Pack `320400`；11 份医生 JSON，运行时加载 2,100 条公开资料 |
| 测试 | pytest 含 transit quality gate；前端 boundary tests；Playwright 20 用例（桌面/平板/移动） |
| Safety | 38 cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency False Negative `0` |
| 模型证据 | random / exact fingerprint / near-duplicate same-label / near-duplicate global；近重复审计 605 对（Jaccard≥0.8） |
| 交通 | bus/taxi/bike 当前 `PROVISIONAL`，`rankable=false`，不参与正式排序 |
| 医院目录 | `data/regions/320400/hospitals/catalog.json`；目录状态 `provisional` |
| 地图底图 | OpenStreetMap 官方瓦片；无 API Key |

## 验证记录

- `.venv/bin/python -m pytest`：通过（含新增 transit quality gate）。
- `.venv/bin/python -m evaluation.safety.evaluate_safety`：38 cases；Recall `1.0`；Under-triage `0.0`；Over-triage `0.0`；Emergency False Negative `0`。
- `.venv/bin/python -m evaluation.model.evaluate_grouped --write`：四种切分已写入 `evaluation/model/`。
- `.venv/bin/python -m data_validation.validate_datasets --data-root data --output-dir data_validation`：28 文件、187 问题，未自动修复。
- `frontend`：`npm run typecheck`、`npm run test`、`npm run build`、`npm run e2e`（20/20）通过。

## 未改变的风险

- Safety 固定样例不等于临床覆盖；仍属 `R-001`。
- 医院/医生来源与许可仍不完整（`R-002`）。
- 数据质量 187 个异常未修复（`R-011`）；交通未过质量门。
- Near-duplicate Group Split 更严格，指标显著低于宽松切分，用于暴露泛化风险而非维持高分。
- 演示认证、CORS、隐私、审计和部署不具备生产安全属性（`R-003`、`R-007`、`R-013`）。

## 下一步

P2 可评估：本地收藏/关注列表、交通数据来源与许可证补全后再决定是否 rankable、更多安全表达覆盖。涉及医学或生产能力时按 L3/L4 另立计划。
