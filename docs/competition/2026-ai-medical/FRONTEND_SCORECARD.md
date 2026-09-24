# Frontend Scorecard — 常医智导

评分范围：1–5；只记录已实现或已验证的范围，未实现项不得用视觉推测代替证据。
本切片：Algorithm-visible UX（2026-09-16）。

## 当前切片评分

| 维度 | 分数 | 证据 | 待改进 |
| --- | ---: | --- | --- |
| First impression | 4 | 首页保留价值主张与症状主 CTA；CarePath 改为静态算法链路示意（无假计时）；三个「示例」快捷入口透明标注 | 完整 1440/1280/768/390 截图矩阵仍可再补 |
| Product clarity | 4 | Journey 对齐 Safety Gate → Direct Department → Selective Abstention → Adaptive Inquiry → Multi-objective Routing；结果页区分拒答/追问/资源路由 | 可选算法字段全面点亮后可再加强 |
| Visual hierarchy | 4 | 急诊横幅优先；普通排行不进入 Emergency；信息不足突出「暂不强行给出科室方向」 | 密度可按实机再微调 |
| Interaction | 4 | 示例入口、追问回答后 `path-updated`、偏好修改触发真实资源重排与 `hospital-why`、loading/error/empty/retry、键盘与 reduced motion | 语音仍依赖浏览器支持 |
| Safety UX | 4 | Emergency：`拨打 120` 最大优先；「目录存在急诊字段 ≠ 当前可接诊」；普通推荐短路；信息不足不硬给科室 | 正式实时急诊仍明确不做 |
| Mobile | 3 | 示例 chips 与主 CTA 在 390/768 有布局规则；既有 mobile spec 保留 | 需实机截图矩阵复核新组件 |
| Accessibility | 3 | 语义 landmark、focus-visible、aria-live 进度、示例 group 可访问名 | 对比度与完整键盘路径待专项审查 |
| Performance | 4 | 首页无装饰计时循环；分析阶段由请求状态驱动；构建后体积待记录 | 网络 waterfall 待记录 |
| Evidence | 4 | 解释字段只读 API `explanations`/`reasons`/`red_flag_tags`；可选 `abstain_reason`/`uncertainty_level` 有则展示、无则不伪造 | 依赖算法侧持续补齐 selective 字段 |
| Demo reliability | 4 | 新增 algorithm-visible E2E：普通/模糊/Emergency + triage 503 + recommendations 失败降级 | 远端 CI 首跑结果待登记 |

当前平均：`3.8 / 5`（Algorithm-visible 主链路已可演示；Mobile/A11y 矩阵与 CI 仍缺口）。

## 评分规则

- 只能依据运行态、测试或可追溯文档评分。
- 任意 Emergency 首屏安全信息被遮挡、弱化或被普通推荐覆盖时，Safety UX 最高为 1。
- API 错误静默渲染成功、硬编码数据冒充运行指标或前端复制医学规则时，Demo reliability / Evidence 不得通过。
- 主要页面平均分达到 `≥4.0` 且核心 E2E、mobile、visual、accessibility 门禁通过后，才允许标记 competition-ready。

## 本轮证据入口

- 产品说明：`docs/competition/2026-ai-medical/ALGORITHM_VISIBLE_UX.md`
- E2E：`frontend/e2e/algorithm-visible.spec.mjs`、`product-smoke.spec.mjs`、`mobile.spec.mjs`、`accessibility.spec.mjs`
- 契约测试：`frontend/test/frontend-boundaries.test.mjs`、`product-copy-audit.test.mjs`

## 后续复核

每完成一个 Homepage、Triage、Result、Resources、Map、Trust、Profile/History 切片，更新对应分数、证据、截图路径、已知问题和下一步；不以设计稿代替浏览器验证。
