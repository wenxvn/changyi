# 当前项目状态

更新时间：2026-09-12

## 总体状态

- 状态：**Legacy Migration Complete**（P1 Final Closeout）
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- Safety Gate 业务语义未改动
- 后续开发不再以旧版功能迁移为主线；新需求进入 P2 Product Intelligence / Resource Routing

## P1 Final Closeout

- 仓库卫生：删除根目录 Agent Prompt `P1 Product Completion + Evidence Hardening。md`；不再把任务书/prompt 产物提交进仓库。
- 医生照片：恢复儿童医院 `czsetyy` 与老年病医院 `czdqyy` 旧照片映射；h11 共 201 条 `photo_file` 精确挂接，h6 共 74 条（73 精确姓名 + 1 条 `（兼）` 人工确认）；provenance 写入 `data/resource_provenance/doctor_photos.json`。
- 医院区域：Region Pack 医院目录增加 `district` 字段（公开地址/名称 token 匹配；无法可靠判断为 `null`）。
- 资源筛选：医院 Tab＝等级/类型/区域/急诊字段；医生 Tab＝医院/科室/职称；关键词与重置共用；URL 保留筛选与 `?hospital=` / `?doctor=` 详情。
- Trust Center：新增 Strict Near-duplicate Isolation 面板（24 样本 / 8/41 类 / 跨 split 近重复 0 / seed 42 / 阈值 0.8），明确不可与随机切分横向等价比较。
- 交通质量：bus/taxi/bike 拆成 per-dataset quality；`data/transit/metadata.json` 登记来源/许可缺口；全部 `PROVISIONAL` 且 `rankable=false`。
- 语音 / 专家偏好 / 地图 / Logo 维持既有安全模式，不再扩展。

## 当前基线

| 领域 | 事实 |
| --- | --- |
| Flask 入口 | `app.py` 兼容启动层；`backend/app/composition.py` 为组合根 |
| 正式前端 | `frontend/src/` React/TypeScript；`frontend/dist/` 由 Flask 提供 |
| 正式 API | `/api/v1/health`、`ready`、`regions`、`triage`、`triage/followups`、`recommendations`、`hospitals`、`doctors`、`summary`、`evidence`、`map` |
| 数据 | active Region Pack `320400`；11 份医生 JSON，运行时加载 2,100 条公开资料 |
| 医生照片 | h6 74/74、h11 201/201 已挂本地公开照片；UNVERIFIED 不写入 `photo_url` |
| 测试 | pytest 118；前端 boundary tests；Playwright 20/20（桌面/平板/移动） |
| Safety | 38 cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency False Negative `0` |
| 模型证据 | random / exact fingerprint / strict near-duplicate same-label / near-duplicate global；近重复审计 605 对（Jaccard≥0.8），跨 split 0 |
| 交通 | bus/taxi/bike 当前 `PROVISIONAL`，`rankable=false`，不参与正式排序 |
| 医院目录 | `data/regions/320400/hospitals/catalog.json`；含 `district`；目录状态 `provisional` |
| 地图底图 | OpenStreetMap 官方瓦片；无 API Key |

## 验证记录

- `.venv/bin/python -m pytest`：118 passed。
- `.venv/bin/python -m evaluation.safety.evaluate_safety`：38 cases；Recall `1.0`；Under-triage `0.0`；Over-triage `0.0`；Emergency False Negative `0`。
- `.venv/bin/python -m evaluation.model.evaluate_grouped --write`：四种切分已写入 `evaluation/model/`。
- `.venv/bin/python -m data_validation.validate_datasets --data-root data --output-dir data_validation`：30 文件、187 问题，未自动修复。
- `frontend`：`npm run typecheck`、`npm run test`、`npm run build`、`npm run e2e`（20/20）通过。

## 未改变的风险

- Safety 固定样例不等于临床覆盖；仍属 `R-001`。
- 医院/医生来源与许可仍不完整（`R-002`）；医生照片多为 `LEGACY_EXACT_MATCH`，非 `SOURCE_VERIFIED`。
- 数据质量 187 个异常未修复（`R-011`）；交通未过质量门。
- 严格近重复隔离覆盖 8/41 类，指标显著低于宽松切分，用于暴露泛化风险而非维持高分。
- 演示认证、CORS、隐私、审计和部署不具备生产安全属性（`R-003`、`R-007`、`R-013`）。

## 下一步

进入 P2：本地收藏/关注列表、交通数据来源与许可证补全后再决定是否 rankable、更多安全表达覆盖、正式附近急诊路径。涉及医学或生产能力时按 L3/L4 另立计划。
