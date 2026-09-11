# 前端资源浏览契约

日期：2026-09-10  
范围：并行前端只读资源索引与资源详情

## 请求

```text
GET /api/v1/hospitals
GET /api/v1/hospitals/<id>
GET /api/v1/doctors
GET /api/v1/doctors?hospital_id=<id>
GET /api/v1/doctors/<id>
```

所有请求经过 `frontend/src/api/client.ts`，返回统一 v1 envelope。资源页默认只调用医院索引；用户切换到医生视图时再调用医生索引；用户选择卡片后才调用对应详情。

## 数据

医院索引 `data`：

```json
{
  "items": [{"id": 1, "name": "...", "level": "...", "type": "...", "address": "...", "departments": [], "derived_capability_areas": [], "emergency": true}],
  "count": 21,
  "source": "legacy_catalog_pending_provenance"
}
```

医生索引 `data`：

```json
{
  "items": [{"id": 1001, "name": "...", "title": "...", "hospital_name": "...", "department": "...", "specialties": [], "outpatient_time": "..."}],
  "count": 2100,
  "source": "public_source_mixed"
}
```

实际数量、字段完整度和来源状态以接口响应为准，不在前端硬编码。

详情 `data`：

```json
{
  "resource_type": "hospital",
  "resource": {"id": 1, "name": "...", "address": "...", "departments": [], "derived_capability_areas": []},
  "source": "legacy_catalog_pending_provenance",
  "provenance": {
    "source_class": "legacy_catalog_pending_provenance",
    "status": "migration_pending",
    "last_updated": null,
    "license_status": "not_recorded",
    "catalog_status": "provisional",
    "field_level_status": "public_facts_and_derived_features",
    "unsupported_fields": ["beds", "daily_outpatients", "rating", "description"],
    "notice": "..."
  },
  "derived_capability": {"status": "provisional", "formula_version": "legacy-strength-score-v1"},
  "related": {"doctor_count": 0, "doctors": []}
}
```

医生详情的 `resource_type` 为 `doctor`，`related.hospital` 为最小医院公开摘要；未知 id 返回 `404 RESOURCE_NOT_FOUND`。详情资源只输出公开字段白名单，不扩散医院内部评分/床位字段、医生学术成就或原始抓取链接。

## 展示安全边界

- “公开资料”是数据来源描述，不代表临床验证、官方推荐或诊断结论。
- 医院的等级、地址、科室、急诊字段只作为接口资料展示；派生能力区域会标记为 provisional，不代表官方评级；beds、daily_outpatients、rating、description 等未支持字段不进入公开医院事实。
- 医生卡片只展示姓名、职称、所属医院、科室、公开专长和门诊字段（若存在）；学术字段不作为默认排序或疗效暗示。
- 详情加载中的索引对象不能被当作完整资料；详情请求失败时显示错误和重试，并保留继续浏览索引的能力。
- 资源列表不能替代 Emergency 路径；急症用户应留在安全结果页，地图/附近急诊另立契约。
