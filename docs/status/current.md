# 当前项目状态

更新时间：2026-09-12（P3 Frontend Product Redesign）

## 总体状态

- 状态：**P3 前端产品化重做完成**（视觉系统 + 空白收敛 + 工程减法）
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- 产品定位：AI Care Routing；Safety 永远先于个性化

## P3 Frontend Product Redesign（本轮）

### 视觉系统

- `tokens.css` 重写：冷灰中性底 `#f3f5f6`、深墨 `#0b1418`、医疗青绿 `#0b6e6a`；去掉 serif 与杂志式大负字距
- 字体：PingFang SC / Noto Sans SC / Inter / system-ui；Display ~40–44px，letter-spacing `-0.02em`
- 容器统一 `1200px`；spacing 贯彻 `4/8/12/16/24/32/48/64/80`
- 按钮：primary/secondary/ghost/danger + hover/active(scale)/focus-visible/disabled + loading
- 卡片层级：主任务卡 > 信息卡 > 平面文本；阴影收敛为 product-like 轻阴影

### 空白消灭

- Home Hero 从 `min-height: 790px` 改为内容自适应；全页高度从约 5 屏压到约 3 屏
- 移除 `min-height: 650px` Trust 大块、`100vh` 空壳 section
- Triage 左栏加入「你会得到什么」列表，消灭空洞
- Journey 从全宽深色宣传块改为紧凑双栏产品步骤
- Trust strip 从全幅深色改为浅色紧凑条

### 页面结构

- **Home**：紧凑首屏（价值主张 + 输入 + Care Path）→ 方式 → 路径演示 → 城市资源 → 可信条 → CTA
- **Triage**：决策工作台；步骤条（描述症状→补充信息→安全方向→资源路径）；Current Understanding 侧栏；资源偏好折叠为 `<details>`
- **Resources / Map / Trust / Profile**：页头压缩；Trust 技术详情默认折叠；Map 列表与 marker hover 双向联动
- **Care Path**：轻量 CSS 3D perspective + 节点深度错位 + 路径流动虚线；移动端关闭 3D

### 工程减法

- 删除 `app.py.bak_algorithm_feedback_20260619`（151KB 旧备份）
- 删除根目录临时会话笔记与审计截图
- `.gitignore` 增加 `.playwright-mcp/`
- `globals.css` 从 5485 行重写为结构化 ~4600 行（含全部页面与响应式），去掉杂志样式与大空白规则
- `frontend/docs/design-system.md` 重写为当前产品规范

### 修复

- `DoctorAvatar` class 名对齐（`doctor-index-avatar`），修复手机端大图横向溢出
- 收藏按钮 `focus-visible` 与 `is-active` 状态补齐

### P3.1 体验打磨（同轮后续）

- **Triage 左栏**：Current Understanding 增加路径进度条、「接下来」行动清单与「浏览全部医疗资源」跳转
- **Resources 卡片**：急诊/医院/医生旗标、区域右对齐、科室 chip 收敛（+N）、操作区贴底
- **Trust**：模型切分 / Grouped CV / 近重复隔离默认折叠为「模型切分与近重复隔离」
- **Map**：marker 增加 `focus`/`blur` 与列表双向联动，键盘可达

## 当前基线

| 领域 | 事实 |
| --- | --- |
| 测试 | pytest **169**；frontend boundary tests **17**；Playwright **20/20** |
| Safety | **142** cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency FN `0` |
| 数据质量 | 31 datasets，**186** issues（PLACEHOLDER_TIMESTAMP / TIME_ORDER） |
| 前端构建 | CSS ~82KB gzip ~12.7KB；JS ~335KB gzip ~100KB |
| 医生 API | 服务端分页与筛选（P2 保持） |
| 收藏 | 本地、最小字段、非病历（P2 保持） |

## 验证记录（本轮）

- `frontend`：typecheck / test 17 / build / e2e 20 通过
- `.venv/bin/python -m pytest`：169 passed
- `.venv/bin/python -m evaluation.safety.evaluate_safety`：142 cases；FN 0；Over-triage 0
- 多断点人工检查：1440 / 1280 / 768 / 390

## 未改变的风险

- Safety 固定样例 ≠ 临床覆盖（`R-001`）
- 来源/许可不完整（`R-002`）；照片仍非 `SOURCE_VERIFIED`
- 交通未过质量门，不参与排序
- Grouped CV 低指标用于暴露泛化风险，不是临床结论；模型不得单独决定科室
- 账号/云同步/实时急诊/实时公交仍明确不做

## 下一步

- 可选：Triage 左栏在结果态填充更多上下文；Resources 卡片密度再调
- 继续观察远端 CI；按需补真实来源核验
- 涉及医学或生产能力按 L3/L4 另立计划
