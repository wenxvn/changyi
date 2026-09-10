# 前端就医地图契约

日期：2026-09-10  
范围：并行前端只读医院位置示意

## 请求

```text
GET /api/v1/map
GET /api/v1/map?lat=<latitude>&lng=<longitude>
```

请求经过 `frontend/src/api/client.ts`，返回统一 `{ data, meta, error }` envelope。默认不请求浏览器定位；只有调用方明确同时提供合法 `lat/lng` 时，后端才返回 `distance_km` 和 `haversine_straight_line_km`。

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
  "distance_method": null,
  "notice": "地图为资源位置示意，不是导航地图；医院来源逐字段 provenance 仍在迁移中。"
}
```

`map_point` 是服务端根据当前资源坐标生成的轻量视图投影，仅用于 SVG/CSS 位置示意。`distance_km` 是 Haversine 直线距离，不是驾车、公交或急救到院时间。`EMERGENCY_CAPABLE` 仅复述接口的急诊字段，不代表实时可用性；没有推荐上下文时不生成推荐 marker。

## 错误与展示安全边界

- 只提供 `lat` 或 `lng`、坐标不可解析或超范围时返回 `400 INVALID_LOCATION` v1 envelope。
- 坐标缺失的医院不进入位置点，不由前端猜测；当前医院资源仍显示来源待补齐。
- 地图页面必须显示“不请求定位”“非导航地图”以及来源限制；正式急诊路径和逐字段 provenance 仍待后续契约，资源详情使用 `frontend-resources.md` 的按 id 详情契约。
