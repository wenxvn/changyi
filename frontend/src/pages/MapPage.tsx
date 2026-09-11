import { useEffect, useMemo, useState } from "react";
import {
  CircleAlert,
  ExternalLink,
  LoaderCircle,
  MapPinned,
  Navigation,
  ShieldCheck,
  X,
} from "lucide-react";
import { ApiError } from "../api/client";
import { getMap } from "../api/map";
import { AmapNavigationLink } from "../components/ui/AmapNavigationLink";
import { StatusPill } from "../components/ui/StatusPill";
import type { MapHospitalRecord, MapPayload } from "../types/api";

type MapFilter = "all" | "emergency";

function errorFor(reason: unknown): ApiError {
  return reason instanceof ApiError
    ? reason
    : new ApiError("NETWORK_ERROR", "地图资源暂时无法载入，请稍后重试。");
}

function itemKey(item: MapHospitalRecord): string {
  return String(item.id ?? item.name ?? `${item.lat}-${item.lng}`);
}

function distanceLabel(item: MapHospitalRecord): string {
  return item.distance_km === null ? "距离未计算" : `${item.distance_km.toFixed(2)} km 直线距离`;
}

function sourceLabel(source: string): string {
  return source.includes("pending") ? "医院目录 · 资料核验中" : "医院位置资料";
}

function MapPreview({ item, onClose }: { item: MapHospitalRecord; onClose: () => void }) {
  return (
    <aside className="map-preview" aria-labelledby="map-preview-title">
      <div className="map-preview__topline">
        <span className="eyebrow">资源资料预览</span>
        <button type="button" onClick={onClose} aria-label="关闭地图资料预览"><X size={18} aria-hidden="true" /></button>
      </div>
      <div className="map-preview__heading">
        <div className={`map-preview__icon${item.emergency ? " map-preview__icon--emergency" : ""}`} aria-hidden="true">
          {item.emergency ? <ShieldCheck size={20} strokeWidth={1.5} /> : <MapPinned size={20} strokeWidth={1.5} />}
        </div>
        <div><h2 id="map-preview-title">{item.name ?? "未命名医院"}</h2><p>{[item.level, item.type].filter((value): value is string => Boolean(value)).join(" · ") || "公开资源资料"}</p></div>
      </div>
      <dl className="map-preview__facts">
        <div><dt>地址</dt><dd>{item.address ?? "未提供"}</dd></div>
        <div><dt>地图状态</dt><dd>{item.emergency ? "接口标记含急诊字段" : "普通资源点"}</dd></div>
        <div><dt>距离</dt><dd>{distanceLabel(item)}</dd></div>
        <div><dt>坐标</dt><dd>{item.lat.toFixed(4)}, {item.lng.toFixed(4)}</dd></div>
      </dl>
      <p className="map-preview__reason">{item.map_reason}</p>
      <AmapNavigationLink target={item} className="map-preview__navigation" />
      <p className="map-preview__source">资料来源信息仍在补充核验。距离为直线距离，仅供参考；实际路线请以高德地图导航结果为准。</p>
    </aside>
  );
}

function MapCanvas({ items, selectedKey, onSelect }: { items: MapHospitalRecord[]; selectedKey: string | null; onSelect: (item: MapHospitalRecord) => void }) {
  return (
    <div className="map-canvas" role="region" aria-label="常州医院位置分布图">
      <div className="map-canvas__topline"><span>常州位置分布</span><small>320400 · 医院资源</small></div>
      <div className="map-canvas__wash map-canvas__wash--one" />
      <div className="map-canvas__wash map-canvas__wash--two" />
      <svg viewBox="0 0 600 420" aria-hidden="true">
        <path className="map-canvas__contour" d="M36 315c76-41 71-136 165-151 62-11 93 28 147-22 57-52 119-30 165 14 34 32 43 73 93 84" />
        <path className="map-canvas__contour map-canvas__contour--soft" d="M28 220c71 20 109-57 181-55 88 3 100 54 174 12 71-39 133-6 189 30" />
        <path className="map-canvas__route" d="M94 342 178 258 294 274 390 187 526 106" />
        <path className="map-canvas__route map-canvas__route--soft" d="M178 258 247 122 390 187" />
      </svg>
      <div className="map-canvas__markers">
        {items.map((item) => {
          const key = itemKey(item);
          const selected = selectedKey === key;
          return (
            <button
              className={`map-marker${item.emergency ? " map-marker--emergency" : ""}${selected ? " map-marker--selected" : ""}`}
              key={key}
              type="button"
              style={{ left: `${item.map_point.x}%`, top: `${item.map_point.y}%` }}
              onClick={() => onSelect(item)}
              aria-label={`查看 ${item.name ?? "医院资源"}`}
              aria-pressed={selected}
              title={item.name ?? "医院资源"}
            >
              <span />
            </button>
          );
        })}
      </div>
      <div className="map-canvas__legend" aria-label="地图标记图例">
        <span><i className="map-legend-dot map-legend-dot--emergency" />含急诊字段</span>
        <span><i className="map-legend-dot" />普通资源</span>
      </div>
      <span className="map-canvas__caption">医院位置分布</span>
    </div>
  );
}

export function MapPage() {
  const [map, setMap] = useState<MapPayload | null>(null);
  const [filter, setFilter] = useState<MapFilter>("all");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    getMap({ signal: controller.signal })
      .then((payload) => {
        if (controller.signal.aborted) return;
        setMap(payload);
        setError(null);
      })
      .catch((reason) => {
        if (!controller.signal.aborted) setError(errorFor(reason));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [attempt]);

  const visibleItems = useMemo(
    () => map?.items.filter((item) => filter === "all" || item.emergency) ?? [],
    [filter, map],
  );
  const selectedItem = visibleItems.find((item) => itemKey(item) === selectedKey) ?? null;

  return (
    <section className="map-page page-container">
      <div className="map-page__hero">
        <div>
          <span className="eyebrow">常州服务区域 · 320400</span>
          <h1>从地图上，<br /><em>看见更实际的到院选择。</em></h1>
          <p>把公开医院资源放回常州城市关系中。列表和位置示意保持同步；急诊字段只表示接口标记，不代表实时急诊可用性。</p>
        </div>
        <div className="map-page__hero-note"><Navigation size={20} strokeWidth={1.4} aria-hidden="true" /><span>医院位置分布</span><small>可从医院资料打开高德导航。</small></div>
      </div>

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
            <span className="map-tabs__hint">{map.distance_method ? "已按直线距离计算" : "未使用用户定位"}</span>
          </div>
          <div id="map-resource-panel" className="map-layout" role="tabpanel" aria-labelledby={filter === "all" ? "map-tab-all" : "map-tab-emergency"} tabIndex={-1}>
            <div className="map-resource-list">
              <div className="map-resource-list__heading"><span>{map.region.name} · 公开资源</span><small>{visibleItems.length} 个位置</small></div>
              {visibleItems.map((item) => {
                const key = itemKey(item);
                const selected = key === selectedKey;
                return (
                  <button className={`map-resource-row${selected ? " map-resource-row--selected" : ""}`} key={key} type="button" onClick={() => setSelectedKey(key)} aria-pressed={selected}>
                    <span className={`map-resource-row__dot${item.emergency ? " map-resource-row__dot--emergency" : ""}`} aria-hidden="true" />
                    <span className="map-resource-row__body"><strong>{item.name ?? "未命名医院"}</strong><small>{item.address ?? "地址未提供"}</small></span>
                    <span className="map-resource-row__meta">{item.emergency ? "急诊字段" : "资源"}<br />{distanceLabel(item)}</span>
                  </button>
                );
              })}
            </div>
            <div className="map-stage">
              <MapCanvas items={visibleItems} selectedKey={selectedKey} onSelect={(item) => setSelectedKey(itemKey(item))} />
              {selectedItem ? <MapPreview item={selectedItem} onClose={() => setSelectedKey(null)} /> : <div className="map-stage__hint"><ExternalLink size={15} aria-hidden="true" />选择列表或 marker 查看公开资料</div>}
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
