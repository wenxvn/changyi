import { LocateFixed, MapPin, X } from "lucide-react";
import { Button } from "./Button";
import { CHANGZHOU_DISTRICTS, useLocationContext } from "../../state/locationContext";

export function LocationSelector() {
  const { location, chooseDistrict, requestPreciseLocation, clearLocation } = useLocationContext();
  const label = location.source === "geolocation"
    ? "已使用本次会话精确位置"
    : location.source === "district"
    ? `${location.district} · 区域参考点`
    : "未提供位置";

  return (
    <section className="location-selector" aria-labelledby="location-selector-title">
      <div className="location-selector__heading">
        <span className="eyebrow" id="location-selector-title"><MapPin size={14} aria-hidden="true" /> 到院位置</span>
        {location.source !== "unknown" ? (
          <button className="location-selector__clear" type="button" onClick={clearLocation}>
            清除 <X size={13} aria-hidden="true" />
          </button>
        ) : null}
      </div>
      <p className="location-selector__status">{label}</p>
      <div className="location-selector__controls">
        <Button
          type="button"
          variant="secondary"
          onClick={requestPreciseLocation}
          disabled={location.requesting}
          icon={<LocateFixed size={16} aria-hidden="true" />}
        >
          {location.requesting ? "请求定位中…" : "使用本次精确定位"}
        </Button>
        <label className="location-selector__select">
          <span className="sr-only">选择所在区域</span>
          <select
            value={location.source === "district" ? location.district ?? "" : ""}
            onChange={(event) => chooseDistrict(event.target.value)}
            aria-label="选择所在区域"
          >
            <option value="">选择所在区域</option>
            {CHANGZHOU_DISTRICTS.map((district) => <option value={district.name} key={district.code}>{district.name}（参考点估算）</option>)}
          </select>
        </label>
      </div>
      <p className="location-selector__message" role={location.error ? "alert" : undefined}>
        {location.error ?? location.message}
      </p>
    </section>
  );
}
