import { ArrowRight, ExternalLink, MapPinned } from "lucide-react";
import { Button } from "../ui/Button";
import { AmapNavigationLink } from "../ui/AmapNavigationLink";
import { DoctorAvatar } from "../ui/DoctorAvatar";
import { HospitalLogo } from "../ui/HospitalLogo";
import { FavoriteDoctorButton } from "../ui/FavoriteDoctorButton";
import { useFavoriteDoctors } from "../../state/favoriteDoctors";
import type { RecommendationPayload, RecommendedDoctor, RecommendedHospital } from "../../types/api";
import {
  doctorName,
  doctorReasons,
  formatDistance,
  hospitalContextQuery,
  hospitalName,
  recommendationReasons,
  resourceSourceLabel,
  trafficSummary,
  trafficUsedInRanking,
} from "./recommendationDisplay";

interface ResourcePreviewProps {
  recommendations: RecommendationPayload;
  direction?: string | null;
  safety?: string | null;
  maxHospitals?: number;
  maxDoctors?: number;
  onNavigate: (path: string) => void;
}

export function RecommendedHospitalCard({
  item,
  index,
  direction,
  safety,
  onNavigate,
}: {
  item: RecommendedHospital;
  index: number;
  direction?: string | null;
  safety?: string | null;
  onNavigate: (path: string) => void;
}) {
  const hospital = item.hospital;
  const distance = formatDistance(item.distance);
  const reasons = recommendationReasons(item, 2);
  const traffic = trafficSummary(item);
  const context = hospitalContextQuery(direction, safety);
  return (
    <article className="path-card">
      <div className="path-card__rank" aria-hidden="true">{index + 1}</div>
      <div className="path-card__body">
        <div className="path-card__identity">
          <HospitalLogo hospitalId={typeof hospital.id === "number" ? hospital.id : undefined} />
          <div className="path-card__title">
            <h4>{hospitalName(item)}</h4>
            <p>{[hospital.level, hospital.type].filter((value): value is string => Boolean(value)).join(" · ") || "公开资源资料"}</p>
          </div>
        </div>
        {item.matched_department ? (
          <p className="path-card__match">
            匹配方向 <strong>{item.matched_department}</strong>
          </p>
        ) : null}
        {reasons.length > 0 ? (
          <ul className="path-card__reasons">
            {reasons.map((reason) => <li key={reason}>{reason}</li>)}
          </ul>
        ) : null}
        <p className="path-card__meta">
          {hospital.address ?? "地址以机构公开资料为准"}
          {distance ? ` · ${distance}` : ""}
        </p>
        {traffic ? (
          <p className="path-card__traffic">
            {traffic}
            <small>{trafficUsedInRanking(item) ? "交通参考已参与可达性排序。" : "交通资源仅供参考。"}</small>
          </p>
        ) : null}
        <div className="path-card__actions">
          <AmapNavigationLink target={hospital} className="path-card__link path-card__link--primary" />
          <button
            className="path-card__link"
            type="button"
            disabled={typeof hospital.id !== "number"}
            onClick={() => typeof hospital.id === "number" && onNavigate(`/resources?hospital=${hospital.id}&${context}`)}
          >
            公开资料详情 <ExternalLink size={13} aria-hidden="true" />
          </button>
        </div>
      </div>
    </article>
  );
}

function RecommendedDoctorRow({
  item,
  onNavigate,
}: {
  item: RecommendedDoctor;
  onNavigate: (path: string) => void;
}) {
  const { isFavorite, toggleFavorite } = useFavoriteDoctors();
  const doctor = item.doctor;
  const reasons = doctorReasons(item, 1);
  return (
    <div className="path-doctor">
      <button
        className="path-doctor__main"
        type="button"
        disabled={typeof doctor.id !== "number"}
        onClick={() => typeof doctor.id === "number" && onNavigate(`/resources?doctor=${doctor.id}`)}
      >
        <DoctorAvatar name={doctor.name} photoUrl={doctor.photo_url} />
        <span className="path-doctor__copy">
          <strong>{doctorName(item)}</strong>
          <small>
            {[doctor.title, doctor.department, doctor.hospital_name].filter((value): value is string => Boolean(value)).join(" · ") || "公开医生资料"}
          </small>
          {reasons.length > 0 ? <em>{reasons.join(" · ")}</em> : null}
        </span>
      </button>
      {typeof doctor.id === "number" ? (
        <FavoriteDoctorButton
          doctorId={doctor.id}
          active={isFavorite(doctor.id)}
          onToggle={toggleFavorite}
          compact
        />
      ) : null}
    </div>
  );
}

/**
 * Resource preview block used inside the triage care path: it only renders fields
 * the ranking payload already returns, so the first screen stays a recommendation
 * rather than a table.
 */
export function ResourcePreview({
  recommendations,
  direction,
  safety,
  maxHospitals = 3,
  maxDoctors = 3,
  onNavigate,
}: ResourcePreviewProps) {
  const hospitals = recommendations.recommended_hospitals.slice(0, maxHospitals);
  const doctors = recommendations.recommended_doctors.slice(0, maxDoctors);
  const notice = typeof recommendations.ranking_notice === "string" ? recommendations.ranking_notice : "";
  const strategyNotice = recommendations.resource_strategy?.notice;

  return (
    <div className="path-resources">
      <div className="path-resources__meta">
        <span>{recommendations.resource_strategy?.visit_path ?? "门诊路径"}</span>
        <span>{resourceSourceLabel(recommendations.data_source)}</span>
      </div>

      {notice ? <p className="path-resources__notice">{notice}</p> : null}
      {!notice && strategyNotice ? <p className="path-resources__notice">{strategyNotice}</p> : null}

      {hospitals.length > 0 ? (
        <div className="path-card-list">
          {hospitals.map((item, index) => (
            <RecommendedHospitalCard
              key={`${hospitalName(item)}-${index}`}
              item={item}
              index={index}
              direction={direction}
              safety={safety}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      ) : (
        <p className="path-resources__empty">当前没有可展示的医院路径，可以稍后重试或直接浏览医疗资源。</p>
      )}

      {doctors.length > 0 ? (
        <div className="path-doctors">
          <div className="path-doctors__heading">
            <span className="eyebrow eyebrow--muted">公开医生资料</span>
            <small>医院路径优先</small>
          </div>
          {doctors.map((item, index) => (
            <RecommendedDoctorRow key={`${doctorName(item)}-${index}`} item={item} onNavigate={onNavigate} />
          ))}
        </div>
      ) : null}

      <div className="path-resources__footer">
        <Button
          variant="secondary"
          onClick={() => {
            const params = new URLSearchParams({ from: "triage" });
            if (direction) params.set("direction", direction);
            if (safety) params.set("safety", safety);
            onNavigate(`/resources?${params.toString()}`);
          }}
          icon={<ArrowRight size={16} aria-hidden="true" />}
        >
          查看完整资源列表
        </Button>
        <Button
          variant="ghost"
          onClick={() => {
            const params = new URLSearchParams({ from: "triage" });
            if (direction) params.set("direction", direction);
            if (safety) params.set("safety", safety);
            onNavigate(`/map?${params.toString()}`);
          }}
          icon={<MapPinned size={16} aria-hidden="true" />}
        >
          在地图上查看
        </Button>
      </div>

      <p className="path-resources__disclaimer">
        推荐分只用于资源排序，不代表诊断概率或治疗效果概率。来源与更新时间以资源详情为准。
      </p>
    </div>
  );
}
