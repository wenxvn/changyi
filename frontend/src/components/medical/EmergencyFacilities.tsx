import { useEffect, useState } from "react";
import { CircleAlert, LoaderCircle, MapPinned } from "lucide-react";
import { getMap } from "../../api/map";
import { AmapNavigationLink } from "../ui/AmapNavigationLink";
import { Button } from "../ui/Button";
import type { MapHospitalRecord, MapPayload } from "../../types/api";

interface EmergencyFacilitiesProps {
  onNavigate: (path: string) => void;
}

/**
 * Emergency side panel: only public hospital records whose catalogue field is
 * already marked as having an emergency department. Nothing here is inferred,
 * and the marker never claims real-time availability.
 */
export function EmergencyFacilities({ onNavigate }: EmergencyFacilitiesProps) {
  const [map, setMap] = useState<MapPayload | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getMap({ signal: controller.signal, location_source: "unknown" })
      .then((payload) => {
        if (!controller.signal.aborted) setMap(payload);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      });
    return () => controller.abort();
  }, []);

  const items: MapHospitalRecord[] = (map?.items ?? []).filter((item) => item.emergency).slice(0, 5);

  return (
    <section className="emergency-side" aria-labelledby="emergency-side-title">
      <div className="emergency-side__heading">
        <h3 id="emergency-side-title"><MapPinned size={16} aria-hidden="true" /> 就近急诊资源</h3>
        <small>公开字段标记，非实时可用性</small>
      </div>

      {!map && !error ? (
        <p className="emergency-side__state" aria-live="polite">
          <LoaderCircle className="spin" size={15} aria-hidden="true" /> 正在读取公开急诊字段…
        </p>
      ) : null}
      {error ? (
        <p className="emergency-side__state" role="status">
          <CircleAlert size={15} aria-hidden="true" /> 公开急诊索引暂时无法载入。
        </p>
      ) : null}

      {items.length > 0 ? (
        <ul className="emergency-side__list">
          {items.map((item) => (
            <li key={String(item.id ?? item.name)}>
              <div>
                <strong>{item.name ?? "未命名医院"}</strong>
                <span>{[item.level, item.type].filter(Boolean).join(" · ") || "公开机构资料"}</span>
                <small>{item.address ?? "地址以机构公开资料为准"}</small>
              </div>
              <AmapNavigationLink target={item} className="emergency-side__link" />
            </li>
          ))}
        </ul>
      ) : null}

      <p className="emergency-side__notice" data-testid="emergency-availability-notice">
        这些标记说明目录中记录了急诊科室，不代表当前可以接诊。真实急救请以 120 调度为准。
      </p>

      <Button
        variant="secondary"
        onClick={() => onNavigate("/map?from=triage&safety=EMERGENCY")}
        icon={<MapPinned size={16} aria-hidden="true" />}
      >
        在地图上查看急诊分布
      </Button>
    </section>
  );
}
