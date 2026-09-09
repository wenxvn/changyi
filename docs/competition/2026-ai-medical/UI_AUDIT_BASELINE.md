# Legacy UI 一致性审计（imprint audit）

日期：2026-09-09  
范围：`templates/index.html`、`static/js/app.js`、`static/css/style.css`  
状态：基线已确认（2026-09-09）；已写入 `ui-registry.md`，并完成首个低风险 UI 收敛切片。

## 审计摘要

静态扫描显示当前 UI 已有一组 CSS variables，但组件主要仍由长 CSS 文件和 JS 字符串 HTML 共同驱动。当前页面可作为 legacy 演示基线，不能直接作为竞赛版 Design System。

| 属性 | 观测 | 已确认基线 / 当前动作 |
| --- | ---: | --- |
| CSS 行数 | 7,174 | 新组件只使用 token；legacy 逐步迁移 |
| JS 行数 | 4,351 | 新页面禁止继续增加全局 `window.*` 和内联样式 |
| Hex 色值 | 572 | 收敛到语义 token；图表色另设有限 palette |
| `rgb/rgba` | 185 | 阴影/透明层保留少量 token，其余迁移 |
| 内联 `style=` | 104 | 仅允许动态宽度/高度等数据值，其余改 class |
| `window._*` 引用 | 97（当前扫描） | 新代码不新增；迁移到页面 state |
| `fetch(` | 25 | 统一 API client，保留错误/降级状态 |
| 定时器调用 | 初始审计 18；含 dashboard 自动轮播 | 已移除首页自动轮播；保留时钟刷新，内容由分页/滑动切换 |

## 冲突明细

### Border radius

发现 `999px`、`8px`、`10px`、`12px`、`50%`、`14px`、`4px`、`20px` 和 token 并存。建议把普通卡片/输入/按钮分别映射到 `--radius-sm`、`--radius`、新增 `--radius-lg`，胶囊继续使用语义 pill token；头像和圆形图标保留 `50%`。

### Background / border

`--bg`、`--card-bg`、`--primary-light`、`--border` 已存在，但大量组件直接使用 `#fff`、`#ffffff`、`#f8fafc`、`#dbeafe` 和 `#bfdbfe`。建议建立 `surface-page`、`surface-card`、`surface-muted`、`border-default`、`border-accent` 语义别名，避免直接引用色板。

### Text colors

`--text` 当前为黑色，`--text-secondary` 为 slate；页面同时使用 `#0f172a`、`#1f4e79`、`#2f3338`、`#475569`、`#5f6b7a`、`#64748b` 等近似层级。建议明确 primary/secondary/muted/medical-warning/medical-danger 五类文本语义，尤其不能让急症红旗因灰色说明文字而弱化。

### Spacing

组件同时使用 8/10/12/14/16/18/20/24/28px 等间距，且 JS 内联样式重复写入 margin、padding、gap。建议形成 4px 基准的 spacing token；新组件优先使用 8/12/16/24 四档，旧组件迁移前不做视觉重排。

### Interactive states

已有 `.nav-item:hover`、`.care-search input:focus`、按钮 hover 和 transition，但动态 HTML 中存在大量内联样式，键盘 `:focus-visible`、禁用态和加载/错误态未形成统一模式。建议新组件统一提供 hover、focus-visible、active、disabled、loading 五态；医疗红旗提供不依赖颜色的图标/文字冗余。

## 硬编码与可访问性重点

- `static/css/style.css` 的颜色硬编码应按上表迁移；代表位置包括登录卡片、mine cards、care intake、图表和状态标签。
- `static/js/app.js` 至少有 104 处内联 `style=`，其中动态图表尺寸可以保留，其余应转为 class 或 CSS custom property。
- 推荐结果、医院列表、医生卡片大量由字符串 HTML 生成；后续迁移必须继续 `esc()`，并补键盘操作、空态、错误态和屏幕阅读器标签。
- `.triage-top-alert`、`.tag-red` 等急症样式已有视觉入口，但必须保持在结果首屏且同时呈现明确文字，不可只靠颜色。
- 初始审计发现 JS 含 dashboard 自动轮播；本轮已改为用户操作，避免在红旗信息附近自动切换内容。

## 运行态限制

本次已用临时 Flask 环境打开 localhost 并完成一次 desktop 运行态检查：页面可加载、首页/智能推荐导航可用，截图 viewport 约为 1265×712；急症样例经过补充问诊后，页面首屏出现“疑似急症”、120 入口、急诊优先和免责声明。地理定位在本地审计中超时，页面提供了手动区域降级提示。

仍未完成 1440×900、1280×800、768×1024、390×844 的完整矩阵，也未完成独立 console 报告。服务日志记录了 `/favicon.ico` 和 Leaflet `layers-2x.png` 的 404，这些属于待修复的静态资源问题；本轮不扩大到静态资源修复。

## 基线确认与首个 UI 切片

负责人已确认以下三项建议，本轮据此执行：

1. 普通卡片 8px、输入/按钮 6–8px、面板 12px、pill 999px、头像圆形。
2. 现有硬编码颜色和内联样式作为后续迁移问题，按小切片逐步修复。
3. 竞赛首页移除自动轮播，改为用户可控内容切换。

已完成的首个低风险切片：

- `static/css/style.css` 增加 surface/text/border/accent/safety/radius/spacing 语义别名，并补充统一 `:focus-visible` 外轮廓。
- 共享卡片、表单控件、标签和首页轮播容器接入已确认的 token；未进行大范围视觉重排。
- `static/js/app.js` 移除 dashboard 自动轮播定时器，保留分页按钮和触摸滑动。
- `ui-registry.md` 已建立并记录 legacy 组件基线。
