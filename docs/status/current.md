# 当前项目状态

更新时间：2026-09-15（初赛提交差距审计）

## 总体状态

- 状态：**P4 比赛演示体验打磨完成**（在 P3 产品化基础上强化第一眼演示质感）
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- 产品定位：AI Care Routing；Safety 永远先于个性化

## P4 Competition Demo Experience Polish（本轮）

### 首页

- Care Path 升级为「活系统」：支持 `idle / analysing / ready` 三态；提交后节点依次亮起，CTA 进入 loading，footer 与说明同步反馈
- 提交路径：短动画（约 720ms + 280ms）后进入 Triage，`prefers-reduced-motion` 直接跳过
- 状态色统一：neutral / info / success

### Triage 决策工作台

- 新增 `ProgressiveStatus` 渐进披露：读取描述 → 安全门 → 就医方向 / 补充信息 → 城市资源
- 步骤条完成态显示对勾（`is-complete`）
- **结果结论前置**：资源偏好与位置选择移到结果下方；首屏直接看到安全结论与科室方向
- 移动端：工作区 `order:1`，当前理解 `order:2`，保证 390px 首屏可见结论

### Resources / Map

- 从 Triage 进入时展示 Context Bar（方向 / 区域 / 偏好 / 安全状态）
- **公开科室匹配**：若带 `direction`，公开 `departments` 含该方向的医院/医生卡片前置并打标；说明「不改变服务端推荐排序」
- Map：marker 选中自动滚动列表项；EMERGENCY 上下文默认筛选急诊字段；底图失败可「重试底图」
- 列表选中态左侧强调条；空状态提供「清除筛选条件」CTA

### 全局

- 页面切换：`page-view` opacity + translateY 6px / 200ms，reduced-motion 关闭
- Footer 单行品牌 + 链接 + 安全说明（约 85px）；&lt;1100px 隐藏 Header region-mark
- 首页大标题桌面强制两行，避免「路径。」孤字
- Care Path / ProgressiveStatus / Context Bar / 步骤完成态共享同一套状态色
- Bundle：CSS ~92.3KB gzip ~14.1KB；JS ~347.2KB gzip ~103.1KB

## P3 基础（仍有效）

- 视觉系统：冷灰中性底 `#f3f5f6`、深墨 `#0b1418`、医疗青绿 `#0b6e6a`
- Care Path 轻量 CSS 3D；移动端关闭 3D
- Trust 技术细节默认折叠；Map 列表与 marker hover/focus 双向联动
- 不恢复 magazine / Dashboard / Demo Login / Chatbot

## 当前基线

| 领域 | 事实 |
| --- | --- |
| 测试 | pytest **169**；frontend boundary tests **17**；Playwright **20/20** |
| Safety | **142** cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency FN `0` |
| 前端构建 | CSS ~92.3KB gzip ~14.1KB；JS ~347.2KB gzip ~103.1KB |
| 医生 API | 服务端分页与筛选（P2 保持） |

## 验证记录（本轮）

- `frontend`：typecheck / test 17 / build / e2e 20 通过
- `.venv/bin/python -m pytest`：169 passed
- `.venv/bin/python -m evaluation.safety.evaluate_safety`：142 cases；FN 0；Over-triage 0
- 多断点人工检查：1440 / 1280 / 768 / 390；普通 / 急诊 / 上下文条 / 首页分析态

## 推荐 30–60 秒演示路径

1. 首页输入症状 → Care Path 亮起 → 进入 Triage
2. 首屏看到安全状态 + 皮肤科方向
3. 跳过追问 → 医院卡片 → 打开地图（Context Bar）
4. 可选：急诊红旗 → 120 CTA + 地图急诊筛选

## 未改变的风险

- Safety 固定样例 ≠ 临床覆盖（`R-001`）
- 来源/许可不完整（`R-002`）；照片仍非 `SOURCE_VERIFIED`
- 账号/云同步/实时急诊/实时公交仍明确不做

## 竞赛提交（2026-09-15 审计）

对照官方赛道规范，**工程/Safety 基线可演示，但初赛主材料未按规范产出**。完整 P0/P1/P2 见 `docs/competition/2026-ai-medical/SUBMISSION_GAP.md`，执行阶段见 `SUBMISSION_WORKFLOW.md`。

当前 P0 摘要：技术方案 PDF、演示视频、提交五件套、答辩 PPT（8/25 旧稿过期且含无来源大数字）、匿名门禁、LICENSE、README/MODEL_CARD/SCORECARD 数字漂移。初赛截止 2026-10-15 20:00。

## 下一步

- 按 `SUBMISSION_WORKFLOW.md` S0→S9 推进初赛材料；先对齐数字与叙事，再写技术方案
- 可选：Resources 按 direction 高亮相关科室 chip（仅展示已有字段）
- 继续观察远端 CI；按需补真实来源核验
- 涉及医学或生产能力按 L3/L4 另立计划

