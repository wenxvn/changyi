# H-20260910-007：资源详情与来源边界首版

- 类型：资源详情 API、公开字段白名单、前端详情状态
- 变更等级：L2
- 结果：医院/医生详情首版完成；legacy 默认入口与旧详情接口保持不变。

## 事件

在 F7/F8 资源索引之后新增 `/api/v1/hospitals/<id>` 和 `/api/v1/doctors/<id>`。后端通过独立 application builder 只返回资源页需要的公开字段，并把 source class、迁移状态、更新时间、许可登记和字段级登记状态作为显式 provenance 返回。前端只有在用户选择卡片后请求详情，索引对象不再充当完整资料。

## 安全与兼容

- 医院内部床位、评分、日均接诊等字段没有进入新详情 read model。
- 医生学术成就和原始抓取链接没有进入新详情 read model。
- 详情文案继续声明公开资料不等于官方推荐、疗效证明或临床适配；未登记字段不被猜测填充。
- 旧 `/api/hospitals/<id>`、`/api/doctors/<id>`、legacy `/`、推荐、地图、Trust 和 Safety 逻辑未改动。

## 验证

89 个 pytest、6/6 前端边界测试、typecheck、Python 编译和详情 API smoke 通过；资源详情 desktop/390×844 运行态验证通过。

## 后续

补逐字段 provenance 和正式发布审核；继续正式附近急诊路径、结构化 follow-up、完整 route parity 及 Playwright/视觉/无障碍门禁。
