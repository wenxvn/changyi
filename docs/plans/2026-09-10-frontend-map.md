# 常医智导前端迁移计划：就医地图首版

状态：进行中（首版）  
日期：2026-09-10  
变更等级：L2（只读地图资源 API、前端选择状态和可视化；不改变医学规则或推荐排序）

## 目标

在并行 `frontend/` 中把 `/map` 从占位页推进为基于现有医院坐标字段的列表/地图联动视图：展示常州示范区医院资源、急诊字段标记、选中 marker、公开地址、数据来源状态，并在 API 收到明确的用户坐标时计算直线距离。

## 非目标

- 不请求浏览器定位权限，不上传用户位置，不接第三方地图、导航、预约、电话外呼或路线规划。
- 没有推荐上下文时不生成“推荐医院”marker、不声称官方排序；急诊字段仅按接口标记展示。
- 不把直线距离包装成驾车/公交到院时间，不改变推荐策略、交通权重或急症规则。
- 不修改 legacy `/`、旧 API、医院原始常量或资源详情 provenance；附近急诊正式路径另立契约。

## 关键决策

- 新增只读 `/api/v1/map`，复用 v1 envelope，返回医院公开字段、坐标、marker 类型、数据来源和可选 `distance_km`。
- 列表和 marker 共用同一 API items；选择状态只在前端控制，避免列表与地图各自加载/排序。
- 坐标缺失或用户位置未提供时显示明确空值文案；不在前端猜测坐标或计算医学意义。
- 地图视觉使用轻量 SVG/CSS 区域示意，标注“非导航地图”；真实地图底图和急诊路径留待后续。

## 实施步骤

1. 抽取只读地图 view payload 和可选坐标/直线距离计算边界。
2. 注册 `/api/v1/map`，为非法坐标返回稳定 v1 错误 envelope。
3. 增加前端 Map 类型、运行时 parser、API client 和 MapPage 列表/marker/preview 联动。
4. 接入 App Shell `/map`，更新 tokenized styles、架构、契约、UI registry、status、progress、history 和 review。
5. 运行 Python/pytest、TypeScript/boundary tests/build、map API smoke 和 desktop/390×844 浏览器检查。

## 验收标准

- `/api/v1/map` 返回当前医院坐标和公开资源字段，急诊字段与来源状态可见；默认不需要用户定位。
- 列表选择与 marker 选择互相同步，选中预览包含地址、资源类型、急诊字段和非官方说明。
- `lat/lng` 完整且合法时返回直线距离；未提供或非法时不静默伪造距离。
- 桌面和移动端无横向溢出，首屏只加载地图资源一次；没有定位权限、外部地图或医学排序副作用。
- Trust、Resources、Triage 和 legacy 默认入口保持现有行为，地图仍不标记为正式导航能力。

## 回滚

回退本计划新增的 map view service、v1 route、前端 Map 类型/API/页面/样式和对应文档即可；不影响现有资源、Trust、triage、推荐或 legacy 行为。
