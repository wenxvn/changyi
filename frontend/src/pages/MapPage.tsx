import { useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import {
  CircleAlert,
  ExternalLink,
  LoaderCircle,
  Minus,
  Navigation,
  Plus,
  X,
} from "lucide-react";
import { ApiError } from "../api/client";
import { getMap } from "../api/map";
import { AmapNavigationLink } from "../components/ui/AmapNavigationLink";
import { HospitalLogo } from "../components/ui/HospitalLogo";
import { LocationSelector } from "../components/ui/LocationSelector";
import { StatusPill } from "../components/ui/StatusPill";
import { useLocationContext } from "../state/locationContext";
import type { MapHospitalRecord, MapPayload } from "../types/api";

type MapFilter = "all" | "emergency";

function errorFor(reason: unknown): ApiError {
  return reason instanceof ApiError
    ? reason
    : new ApiError("NETWORK_ERROR", "地图资源暂时无法载入，请稍后重试。");
}

function itemKey(item: MapHospitalRecord): string {
  return String(item.id ?? item.name ?? item.lat + "-" + item.lng);
}

function distanceLabel(item: MapHospitalRecord, source: string | undefined): string {
  if (item.distance_km === null) return "距离未计算";
  return source === "district"
    ? item.distance_km.toFixed(2) + " km · 区域参考点估算"
    : item.distance_km.toFixed(2) + " km · 直线距离";
}

function sourceLabel(source: string): string {
  if (source.includes("pending") || source.includes("provisional")) return "医院目录 · 暂待核验";
  return "医院位置资料";
}

function MapPreview({ item, source, onClose }: { item: MapHospitalRecord; source?: string; onClose: () => void }) {
  return (
    <aside className="map-preview" aria-labelledby="map-preview-title">
      <div className="map-preview__topline">
        <span className="eyebrow">资源资料预览</span>
        <button type="button" onClick={onClose} aria-label="关闭地图资料预览"><X size={18} aria-hidden="true" /></button>
      </div>
      <div className="map-preview__heading">
        <HospitalLogo hospitalId={typeof item.id === "number" ? item.id : undefined} size="preview" className={item.emergency ? "hospital-logo--emergency" : ""} />
        <div><h2 id="map-preview-title">{item.name ?? "未命名医院"}</h2><p>{[item.level, item.type].filter((value): value is string => Boolean(value)).join(" · ") || "公开资源资料"}</p></div>
      </div>
      <dl className="map-preview__facts">
        <div><dt>地址</dt><dd>{item.address ?? "未提供"}</dd></div>
        <div><dt>地图状态</dt><dd>{item.emergency ? "接口标记含急诊字段" : "普通资源点"}</dd></div>
        <div><dt>距离</dt><dd>{distanceLabel(item, source)}</dd></div>
        <div><dt>坐标</dt><dd>{item.lat.toFixed(4)}, {item.lng.toFixed(4)}</dd></div>
      </dl>
      <p className="map-preview__reason">{item.map_reason}</p>
      <AmapNavigationLink target={item} className="map-preview__navigation" />
      <p className="map-preview__source">地图底图 © OpenStreetMap contributors。距离仅供参考，实际路线请以导航结果为准。</p>
    </aside>
  );
}

function project(lat: number, lng: number, zoom: number): { x: number; y: number } {
  const size = 256 * Math.pow(2, zoom);
  const safeLat = Math.max(-85.0511, Math.min(85.0511, lat));
  const sin = Math.sin((safeLat * Math.PI) / 180);
  return {
    x: ((lng + 180) / 360) * size,
    y: (0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI)) * size,
  };
}

function RealMapCanvas({
  items,
  userLocation,
  selectedKey,
  hoveredKey,
  onSelect,
  onHover,
}: {
  items: MapHospitalRecord[];
  userLocation?: MapPayload["user_location"];
  selectedKey: string | null;
  hoveredKey?: string | null;
  onSelect: (item: MapHospitalRecord) => void;
  onHover?: (key: string | null) => void;
}) {
  const [view, setView] = useState({ lat: 31.77, lng: 119.95, zoom: 11 });
  const [tileLoadFailed, setTileLoadFailed] = useState(false);
  const [tileAttempt, setTileAttempt] = useState(0);
  const dragRef = useRef<{ x: number; y: number } | null>(null);
  const center = project(view.lat, view.lng, view.zoom);
  const tileX = Math.floor(center.x / 256);
  const tileY = Math.floor(center.y / 256);
  const tileCount = Math.pow(2, view.zoom);
  const isDistrictReference = userLocation?.source === "district";
  const tiles: Array<{ key: string; left: string; top: string; url: string }> = [];
  for (let xOffset = -2; xOffset <= 2; xOffset += 1) {
    for (let yOffset = -2; yOffset <= 2; yOffset += 1) {
      const x = tileX + xOffset;
      const y = tileY + yOffset;
      if (y < 0 || y >= tileCount) continue;
      const wrappedX = (x + tileCount) % tileCount;
      tiles.push({
        key: wrappedX + "-" + y,
        left: "calc(50% + " + (x * 256 - center.x) + "px)",
        top: "calc(50% + " + (y * 256 - center.y) + "px)",
        // OSM standard tiles: public, no API key, attribution required.
        // CARTO free CDN started returning API KEY REQUIRED watermarks.
        url: "https://tile.openstreetmap.org/" + view.zoom + "/" + wrappedX + "/" + y + ".png",
      });
    }
  }

  useEffect(() => {
    const lat = userLocation?.lat;
    const lng = userLocation?.lng;
    if (typeof lat === "number" && typeof lng === "number") setView((current) => ({ ...current, lat, lng }));
  }, [userLocation?.lat, userLocation?.lng]);

  function handlePointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = { x: event.clientX, y: event.clientY };
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    if (!dragRef.current) return;
    const dx = event.clientX - dragRef.current.x;
    const dy = event.clientY - dragRef.current.y;
    dragRef.current = { x: event.clientX, y: event.clientY };
    const worldSize = 256 * Math.pow(2, view.zoom);
    setView((current) => ({
      ...current,
      lng: current.lng - (dx * 360) / worldSize,
      lat: current.lat + (dy * 360) / worldSize,
    }));
  }

  function handlePointerUp(event: ReactPointerEvent<HTMLDivElement>) {
    dragRef.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
  }

  function changeZoom(delta: number) {
    setView((current) => ({ ...current, zoom: Math.max(9, Math.min(16, current.zoom + delta)) }));
  }

  return (
    <div
      className="map-canvas map-canvas--real"
      role="region"
      aria-label="常州医院真实地理位置地图"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      <div className="map-canvas__topline"><span>常州地理位置</span><small>OpenStreetMap · 可拖动缩放</small></div>
      <div className="map-tile-layer" aria-hidden="true" key={tileAttempt}>
        {tiles.map((tile) => <img src={tile.url} alt="" key={tile.key} style={{ left: tile.left, top: tile.top }} onError={() => setTileLoadFailed(true)} />)}
      </div>
      {tileLoadFailed ? (
        <div className="map-tile-fallback" role="status">
          底图暂时未加载，医院坐标和公开资料仍可查看；实际路线请以高德导航为准。
          <button type="button" onClick={(event) => { event.stopPropagation(); setTileLoadFailed(false); setTileAttempt((value) => value + 1); }}>
            重试底图
          </button>
        </div>
      ) : null}
      <div className="map-canvas__markers">
        {items.map((item) => {
          const point = project(item.lat, item.lng, view.zoom);
          const key = itemKey(item);
          const selected = selectedKey === key;
          const hovered = hoveredKey === key;
          return (
            <button
              className={"map-marker" + (item.emergency ? " map-marker--emergency" : "") + (selected ? " map-marker--selected" : "") + (hovered && !selected ? " map-marker--hovered" : "")}
              key={key}
              type="button"
              style={{ left: "calc(50% + " + (point.x - center.x) + "px)", top: "calc(50% + " + (point.y - center.y) + "px)" }}
              onClick={(event) => { event.stopPropagation(); onSelect(item); }}
              onMouseEnter={() => onHover?.(key)}
              onMouseLeave={() => onHover?.(null)}
              onFocus={() => onHover?.(key)}
              onBlur={() => onHover?.(null)}
              aria-label={"查看 " + (item.name ?? "医院资源")}
              aria-pressed={selected}
              title={item.name ?? "医院资源"}
            >
              <span />
            </button>
          );
        })}
        {typeof userLocation?.lat === "number" && typeof userLocation.lng === "number" ? (() => {
          const point = project(userLocation.lat, userLocation.lng, view.zoom);
          return <span className="map-user-marker" style={{ left: "calc(50% + " + (point.x - center.x) + "px)", top: "calc(50% + " + (point.y - center.y) + "px)" }} aria-label={isDistrictReference ? "区域参考点" : "本次会话位置"} />;
        })() : null}
      </div>
      <div className="map-canvas__controls" aria-label="地图缩放">
        <button type="button" onClick={(event) => { event.stopPropagation(); changeZoom(1); }} aria-label="放大地图"><Plus size={16} aria-hidden="true" /></button>
        <button type="button" onClick={(event) => { event.stopPropagation(); changeZoom(-1); }} aria-label="缩小地图"><Minus size={16} aria-hidden="true" /></button>
      </div>
      <div className="map-canvas__legend" aria-label="地图标记图例">
        {typeof userLocation?.lat === "number" && typeof userLocation.lng === "number" ? <span><i className="map-legend-dot map-legend-dot--user" />{isDistrictReference ? "区域参考点" : "本次会话位置"}</span> : null}
        <span><i className="map-legend-dot map-legend-dot--emergency" />含急诊字段</span>
        <span><i className="map-legend-dot" />普通资源</span>
      </div>
      <span className="map-canvas__caption">底图 © OpenStreetMap contributors</span>
    </div>
  );
}

export function MapPage() {
  const [map, setMap] = useState<MapPayload | null>(null);
  const [filter, setFilter] = useState<MapFilter>("all");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);
  const rowRefs = useRef<Map<string, HTMLButtonElement | null>>(new Map());
  const { location } = useLocationContext();
  const triageContext = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("from") !== "triage") return null;
    return {
      safety: params.get("safety"),
      direction: params.get("direction"),
    };
  }, []);

  useEffect(() => {
    if (triageContext?.safety === "EMERGENCY") setFilter("emergency");
  }, [triageContext?.safety]);

  useEffect(() => {
    if (!selectedKey) return;
    const row = rowRefs.current.get(selectedKey);
    if (!row) return;
    row.scrollIntoView({ block: "nearest", behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }, [selectedKey]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    getMap({
      signal: controller.signal,
      location_source: location.source,
      ...(location.source === "geolocation" && location.lat !== null && location.lng !== null
        ? { lat: location.lat, lng: location.lng }
        : {}),
      ...(location.source === "district" && location.district ? { district: location.district } : {}),
    })
      .then((payload) => {
        if (controller.signal.aborted) return;
        setMap(payload);
        setSelectedKey(null);
        setError(null);
      })
      .catch((reason) => {
        if (!controller.signal.aborted) setError(errorFor(reason));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [attempt, location.source, location.district, location.lat, location.lng]);

  const visibleItems = useMemo(
    () => map?.items.filter((item) => filter === "all" || item.emergency) ?? [],
    [filter, map],
  );
  const selectedItem = visibleItems.find((item) => itemKey(item) === selectedKey) ?? null;
  const locationSource = map?.user_location?.source;

  return (
    <section className="map-page page-container">
      <div className="map-page__hero">
        <div>
          <span className="eyebrow">常州服务区域 · 320400</span>
          <h1>从地图上，<em>看见更实际的到院选择。</em></h1>
          <p>这里使用公开医院坐标叠加真实地理底图；急诊字段只表示接口标记，不代表实时急诊可用性。</p>
        </div>
        <div className="map-page__hero-note"><Navigation size={18} strokeWidth={1.5} aria-hidden="true" /><span>真实地理地图</span><small>可从医院资料打开导航。</small></div>
      </div>

      <LocationSelector />
      {triageContext ? (
        <div className="resource-context-bar" role="status" aria-label="当前就医上下文">
          <span className="resource-context-bar__title">当前就医上下文</span>
          <div className="resource-context-bar__items">
            {triageContext.direction ? <span><small>方向</small><strong>{triageContext.direction}</strong></span> : null}
            <span><small>区域</small><strong>常州 · 320400</strong></span>
            {triageContext.safety ? (
              <span>
                <small>安全状态</small>
                <strong className={`resource-context-bar__safety resource-context-bar__safety--${triageContext.safety.toLowerCase()}`}>
                  {triageContext.safety === "EMERGENCY" ? "需要优先评估" : triageContext.safety}
                </strong>
              </span>
            ) : null}
          </div>
          <small className="resource-context-bar__note">急诊字段只表示接口标记，不代表实时急诊可用性。</small>
        </div>
      ) : null}
      {loading ? <div className="map-loading" aria-live="polite"><LoaderCircle className="spin" size={18} aria-hidden="true" /> 正在读取医院位置索引…</div> : null}
      {!loading && error ? <div className="map-error" role="alert"><CircleAlert size={18} aria-hidden="true" /><span>{error.message}</span><button type="button" onClick={() => setAttempt((value) => value + 1)}>重试</button></div> : null}
      {!loading && !error && map ? (
        <>
          <div className="map-toolbar">
            <StatusPill tone="warning">{sourceLabel(map.source)}</StatusPill>
            <span>{map.notice}</span>
          </div>
          <div className="map-tabs" role="tablist" aria-label="地图资源筛选">
            <button id="map-tab-all" type="button" role="tab" aria-controls="map-resource-panel" aria-selected={filter === "all"} tabIndex={filter === "all" ? 0 : -1} className={filter === "all" ? "is-active" : ""} onClick={() => setFilter("all")}>全部资源 <small>{map.count}</small></button>
            <button id="map-tab-emergency" type="button" role="tab" aria-controls="map-resource-panel" aria-selected={filter === "emergency"} tabIndex={filter === "emergency" ? 0 : -1} className={filter === "emergency" ? "is-active" : ""} onClick={() => setFilter("emergency")}>含急诊字段 <small>{map.items.filter((item) => item.emergency).length}</small></button>
            <span className="map-tabs__hint">{map.distance_method === "haversine_reference_point_km" ? "按区域参考点估算" : map.distance_method ? "按直线距离计算" : "未使用用户定位"}</span>
          </div>
          <div id="map-resource-panel" className="map-layout" role="tabpanel" aria-labelledby={filter === "all" ? "map-tab-all" : "map-tab-emergency"} tabIndex={-1}>
            <div className="map-resource-list">
              <div className="map-resource-list__heading"><span>{map.region.name} · 公开资源</span><small>{visibleItems.length} 个位置</small></div>
              {visibleItems.map((item) => {
                const key = itemKey(item);
                const selected = key === selectedKey;
                const hovered = key === hoveredKey;
                return (
                  <button
                    className={"map-resource-row" + (selected ? " map-resource-row--selected" : "") + (hovered && !selected ? " map-resource-row--hovered" : "")}
                    key={key}
                    type="button"
                    ref={(element) => { rowRefs.current.set(key, element); }}
                    onClick={() => setSelectedKey(key)}
                    onMouseEnter={() => setHoveredKey(key)}
                    onMouseLeave={() => setHoveredKey(null)}
                    onFocus={() => setHoveredKey(key)}
                    onBlur={() => setHoveredKey(null)}
                    aria-pressed={selected}
                  >
                    <span className={"map-resource-row__dot" + (item.emergency ? " map-resource-row__dot--emergency" : "")} aria-hidden="true" />
                    <span className="map-resource-row__body"><strong>{item.name ?? "未命名医院"}</strong><small>{item.address ?? "地址未提供"}</small></span>
                    <span className="map-resource-row__meta">{item.emergency ? "急诊字段" : "资源"}<br />{distanceLabel(item, locationSource)}</span>
                  </button>
                );
              })}
            </div>
            <div className="map-stage">
              <RealMapCanvas
                items={visibleItems}
                userLocation={map.user_location}
                selectedKey={selectedKey}
                hoveredKey={hoveredKey}
                onSelect={(item) => setSelectedKey(itemKey(item))}
                onHover={setHoveredKey}
              />
              {selectedItem ? <MapPreview item={selectedItem} source={locationSource} onClose={() => setSelectedKey(null)} /> : <div className="map-stage__hint"><ExternalLink size={15} aria-hidden="true" />选择列表或 marker 查看公开资料</div>}
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
