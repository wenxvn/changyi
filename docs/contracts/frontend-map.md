# 前端就医地图契约

日期：2026-09-10  
范围：并行前端只读医院位置示意

## 请求

```text
GET /api/v1/map
GET /api/v1/map?location_source=geolocation&lat=<latitude>&lng=<longitude>
GET /api/v1/map?location_source=district&district=<district>
```

请求经过 `frontend/src/api/client.ts`，返回统一 `{ data, meta, error }` envelope。默认位置来源为 `unknown`，不请求浏览器定位；只有用户主动授权的合法 `lat/lng` 或明确选择区域参考点时，后端才返回距离。区域距离使用 `haversine_reference_point_km`，精确定位使用 `haversine_straight_line_km`。

## 数据

```json
{
  "region": {"code": "320400", "name": "常州市", "region_pack_version": "..."},
  "items": [{
    "id": 1,
    "name": "...",
    "level": "...",
    "type": "...",
    "address": "...",
    "lat": 31.7768,
    "lng": 119.958,
    "emergency": true,
    "marker_type": "EMERGENCY_CAPABLE",
    "map_reason": "接口标记含急诊字段；不等于实时急诊可用性。",
    "distance_km": null,
    "map_point": {"x": 50.0, "y": 50.0}
  }],
  "count": 21,
  "source": "legacy_catalog_pending_provenance",
  "provenance": {"status": "provisional", "source_class": "legacy_catalog_import"},
  "user_location": {"lat": null, "lng": null, "source": "unknown"},
  "distance_method": null,
  "notice": "地图用于辅助查看资源分布；距离仅供参考，实际路线请以高德导航结果为准。医院资料仍在核验。"
}
```

`map_point` 仍是服务端坐标投影的兼容字段；正式页面使用 OpenStreetMap 官方标准瓦片（`tile.openstreetmap.org`，无需 API Key）叠加公开医院坐标，支持拖动和缩放，并保留底图署名。CARTO 免费 CDN 在实际浏览器中可能返回 “API KEY REQUIRED” 水印瓦片，已不再使用。页面的医院资料预览可通过共享导航 utility 生成高德导航 URI；这只是外部地图跳转，不是系统计算的路线或急救指令。`distance_km` 是 Haversine 直线/区域参考点距离，不是驾车、公交或急救到院时间。`EMERGENCY_CAPABLE` 仅复述接口的急诊字段，不代表实时可用性；没有推荐上下文时不生成推荐 marker。底图加载失败时仍保留坐标 marker、医院列表、资料入口和高德导航，并显示降级提示。桌面端左侧列表独立滚动，右侧地图与 viewport 高度绑定并保持可见；移动端为正常单列。

## 错误与展示安全边界

- 只提供 `lat` 或 `lng`、坐标不可解析或超范围时返回 `400 INVALID_LOCATION` v1 envelope。
- 坐标缺失的医院不进入位置点，不由前端猜测；当前医院资源仍显示来源待补齐。
- 地图页面必须显示位置分布、直线距离限制、资料来源限制和高德导航入口；导航 URI 不得被包装为实时路线或急救指令。正式急诊可用性和逐字段 provenance 仍待后续契约，资源详情使用 `frontend-resources.md` 的按 id 详情契约。
