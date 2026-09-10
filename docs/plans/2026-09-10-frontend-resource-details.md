# 常医智导前端迁移计划：资源详情与来源边界

状态：已完成（首版，保留逐字段 provenance 门禁）  
日期：2026-09-10  
变更等级：L2（只读资源详情 API、公开字段白名单和前端详情加载；不改变医学规则或推荐排序）

## 目标

为医院和医生资料预览建立版本化详情契约，让详情内容来自后端公开字段白名单，并同步返回来源类别、状态、更新时间和许可登记状态。前端资源页在用户明确选择后读取详情，不再把索引对象本地当作完整资料。

## 非目标

- 不修改旧 `/api/*` 详情接口、医院常量、医生抓取数据或推荐结果。
- 不把医院等级、急诊字段、医生专长、论文/手术量等字段包装成官方背书、疗效证明或临床适配。
- 不伪造缺失的更新时间、许可证、逐字段出处或资源可用性；缺失值返回 `null`/登记状态。
- 不新增预约、导航、定位、电话外呼、收藏或生产认证。

## 契约决策

- 新增只读 `GET /api/v1/hospitals/<id>` 和 `GET /api/v1/doctors/<id>`，沿用 v1 envelope。
- 详情 `resource` 只包含前端公开资料需要的白名单字段；内部评分、学术成就、原始抓取链接等不通过新详情边界默认扩散。
- `provenance` 显式返回 `source_class`、`status`、`last_updated`、`license_status`、`field_level_status` 和 `notice`；当前医院为 `legacy_catalog_pending_provenance`，医生为 `public_source_mixed`，登记不足处保持可见。
- 详情加载失败时前端显示错误和重试，不回退为“详情已完整加载”；索引仍可继续浏览。

## 实施步骤

1. 抽取资源公开字段白名单和详情 payload builder。
2. 注册 v1 医院/医生详情路由，增加成功、404 和敏感字段不扩散测试。
3. 增加前端详情类型、runtime parser、API client，并让资源预览按选择读取详情。
4. 更新资源/地图契约、架构、状态、进度、历史、UI registry 和 review。
5. 运行 Python/TypeScript/boundary/build、API smoke 和资源页 desktop/mobile 检查。

## 验收标准

- 合法医院/医生 id 返回统一 v1 envelope、公开字段和 provenance；未知 id 返回稳定 `RESOURCE_NOT_FOUND`。
- 详情不返回医院内部评分/床位等未完成来源字段，不返回医生学术成就或原始抓取 URL 等未纳入新边界的字段。
- 资源页点击预览后请求对应详情 endpoint；加载、错误、重试和关闭状态可读。
- 旧 `/api/hospitals/<id>`、`/api/doctors/<id>`、legacy `/` 和推荐快照保持不变。

## 回滚

回退本计划新增的 resource detail application builder、v1 详情路由、前端详情 API/parser/状态和对应文档即可；不影响旧详情接口、列表接口、地图、Trust、triage 或推荐。
