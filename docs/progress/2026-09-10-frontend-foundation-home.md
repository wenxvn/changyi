# 2026-09-10 Frontend Foundation / App Shell / Homepage

状态：已完成（首个前端迁移切片）  
变更等级：L2  
计划：[2026-09-10-frontend-migration-foundation-home.md](../plans/2026-09-10-frontend-migration-foundation-home.md)

## 目标

建立与 legacy 并行的新 `frontend/`，完成 Warm Precision 设计基础、无侧边栏 App Shell、首页叙事和最小 Triage Workspace 首步；首页指标必须来自只读 API，且不在浏览器复制医学判断。

## 已完成

- 创建 strict TypeScript + React + Vite 工程，集中 API client 统一处理 base URL、超时、取消、request id、错误和运行时响应校验。
- 增加 `/api/v1/summary` 只读摘要契约，返回 active Region Pack、城市资源指标、来源类别和迁移状态。
- 建立语义 token、响应式 App Shell、品牌标记、导航、页脚、Care Path Visual 和手动 AI Journey。
- 完成 Editorial Homepage：自然语言症状输入、城市智能层、Trust CTA、免责声明和明确的 API 错误/空态。
- 完成最小 Triage Workspace：只把文本提交到 `/api/v1/triage`，状态和科室信息完全来自后端返回。
- 更新架构、评分卡、计划、ADR、UI registry、当前状态和运行记录；legacy `/`、`/api/*`、`/api/v1/*` 仍保持默认兼容路径。

## 验证

- `npm run typecheck`：通过。
- `npm run test`：2/2 Node boundary tests 通过，确认页面不直接调用 `fetch`、不依赖 `window._*`，请求基础设施集中在 client。
- `npm run build`：通过；Vite 产物 gzip 约 JS 71.6 kB、CSS 7.1 kB。
- `node --check static/js/app.js`、`python3 -m py_compile app.py backend/app/api/v1/routes.py`：通过。
- 使用本地缓存依赖运行全量 pytest：86/86 通过；API smoke 覆盖 health、summary、regions、triage 正常/空输入和 404 边界。
- 浏览器运行态检查 1440×900、1280×800、768×1024、390×844：首页、移动导航、AI Journey 手动切换、首页→triage→后端状态展示均通过；console error/warning 为空。

## 未验证与有意保留

- 新前端仍为并行入口，未替换 legacy 默认 `/`；route parity、完整 E2E、独立截图 baseline 和 CI frontend job 留到后续切片。
- 完整追问、Routine/Urgent/Emergency 独立结果页、资源详情、地图和 Trust Center 证据页尚未实现。
- Vitest/Testing Library/Playwright 未在本切片加入：当前依赖缓存不可用，先用 Node boundary test 保持可重复门禁，后续依赖可用时补齐。
- 语音按钮保持 disabled；医院目录来源仍显示 `migration_pending`，未把迁移中的数据包装成正式来源。

## 下一步

优先完成 F3/F4：一次一个问题的 follow-up、四态结果组件和安全矩阵；随后加入 Playwright smoke、截图 baseline、keyboard/contrast 检查，并在完成 parity 后再讨论默认入口切换。
