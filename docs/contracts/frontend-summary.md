# Frontend Summary Contract

状态：v1 draft  
Endpoint：`GET /api/v1/summary`  
变更等级：L2，只读数据摘要

## Response envelope

响应遵循现有 v1 envelope：

```json
{
  "data": {
    "region": {"code": "320400", "name": "常州市", "status": "active"},
    "metrics": {
      "hospitals": {"value": 21, "label": "医疗机构", "source_class": "legacy_catalog_import", "status": "provisional"},
      "doctors": {"value": 2100, "label": "医生公开资料", "source_class": "public_source_mixed"},
      "bus_routes": {"value": 50, "label": "公交线路", "source_class": "public_secondary_masked"},
      "districts": {"value": 7, "label": "城市区域", "source_class": "legacy_user_locations"}
    },
    "generated_from": {"region_pack_version": "...", "dataset_status": "..."}
  },
  "meta": {"request_id": "...", "model_version": "...", "region_code": "320400"},
  "error": null
}
```

示例数值仅用于字段说明，前端、文档和演示不得将示例数字作为事实。运行值由后端当前数据计算。

## Semantics

- `hospitals` 当前来自 active Region Pack 的 `hospitals/catalog.json`，其 `source_class` 为 `legacy_catalog_import`、状态为 `provisional`，不得在 UI 中标成官方已验证目录。旧 source 兼容字段若仍出现在 v1 资源列表，只能作为兼容标记。
- `doctors` 来自当前公开资料混合数据，`source_class` 为 `public_source_mixed`。
- `bus_routes` 来自已加载公交线路摘要，来源类别和质量限制随 API 返回。
- `districts` 来自 active Region Pack 的 districts，不代表用户精确位置。
- `metrics.*.value` 是资源条目计数，不是医疗质量、诊断概率或覆盖率。
