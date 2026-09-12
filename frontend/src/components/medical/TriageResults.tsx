import { ArrowRight, ExternalLink, MapPinned, PhoneCall, ShieldAlert, Sparkles } from "lucide-react";
import { Button } from "../ui/Button";
import { StatusPill } from "../ui/StatusPill";
import { AmapNavigationLink } from "../ui/AmapNavigationLink";
import { DoctorAvatar } from "../ui/DoctorAvatar";
import { HospitalLogo } from "../ui/HospitalLogo";
import { FavoriteDoctorButton } from "../ui/FavoriteDoctorButton";
import { useFavoriteDoctors } from "../../state/favoriteDoctors";
import type {
  RecommendationPayload,
  RecommendedDoctor,
  RecommendedHospital,
  TriagePayload,
} from "../../types/api";

interface TriageResultsProps {
  result: TriagePayload;
  recommendations: RecommendationPayload | null;
  recommendationsLoading?: boolean;
  recommendationsError?: string | null;
  onLoadRecommendations: () => void;
  onNavigate: (path: string) => void;
}

function formatDistance(value: number | null | undefined): string | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return value < 1 ? `${Math.round(value * 1000)} m` : `${value.toFixed(1)} km`;
}

function hospitalName(item: RecommendedHospital): string {
  return typeof item.hospital.name === "string" && item.hospital.name ? item.hospital.name : "推荐医疗机构";
}

function doctorName(item: RecommendedDoctor): string {
  return typeof item.doctor.name === "string" && item.doctor.name ? item.doctor.name : "公开医生资料";
}

function recommendationReasons(item: RecommendedHospital): string[] {
  return (item.explanations ?? []).filter(Boolean).slice(0, 3);
}

function resourceSourceLabel(source: string | undefined): string {
  if (source === "real" || source === "real_data") return "常州公开资源";
  if (source === "mock") return "演示资源";
  return "公开资源";
}

function RecommendationError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="recommendation-error" role="alert">
      <span><ShieldAlert size={17} aria-hidden="true" /> {message}</span>
      <button type="button" onClick={onRetry}>重试</button>
    </div>
  );
}

function transitDatasetLabel(datasetId: string): string {
  if (datasetId === "bus_stations") return "公交站";
  if (datasetId === "taxi_operations") return "出租车";
  if (datasetId === "bike") return "共享骑行";
  return datasetId;
}

function TrafficAccessNote({ item }: { item: RecommendedHospital }) {
  const access = item.traffic_access;
  if (!access || typeof access !== "object") return null;
  const summary = typeof access.summary === "string" ? access.summary : "";
  const used = Boolean(access.used_in_ranking);
  if (!summary || summary.includes("暂无交通融合数据")) return null;
  const quality = access.quality;
  const datasetNotes = (quality && typeof quality === "object" && !Array.isArray(quality)
    ? Object.entries(quality as Record<string, unknown>)
        .filter(([, value]) => Boolean(value) && typeof value === "object")
        .map(([datasetId, value]) => {
          const row = value as Record<string, unknown>;
          const status = typeof row.quality === "string" ? row.quality : "UNKNOWN";
          const rankable = Boolean(row.rankable);
          const suffix = datasetId === "bike" ? "仅展示" : rankable ? "可参与排序" : "仅参考";
          return `${transitDatasetLabel(datasetId)}：${status} · ${suffix}`;
        })
    : []);
  return (
    <p className="resource-card__traffic">
      <span>交通可达性</span>
      {summary}
      {datasetNotes.length ? <span className="resource-card__traffic-quality">{datasetNotes.join("；")}</span> : null}
      <small>{used ? "交通资源参考，可能参与可达性排序。" : "仅作交通资源参考，不参与正式推荐排序。"}</small>
    </p>
  );
}

function HospitalCard({ item, index, onNavigate }: { item: RecommendedHospital; index: number; onNavigate: (path: string) => void }) {
  const name = hospitalName(item);
  const hospital = item.hospital;
  const distance = formatDistance(item.distance);
  const reasons = recommendationReasons(item);
  return (
    <article className="resource-card">
      <div className="resource-card__topline">
        <span className="resource-card__index">0{index + 1}</span>
        <span className="resource-card__meta">医院路径</span>
      </div>
      <div className="resource-card__identity">
        <HospitalLogo hospitalId={typeof hospital.id === "number" ? hospital.id : undefined} />
        <div>
          <h3>{name}</h3>
          <p className="resource-card__subline">{[hospital.level, hospital.type].filter((value): value is string => Boolean(value)).join(" · ") || "公开资源资料"}</p>
        </div>
      </div>
      <p className="resource-card__address">{hospital.address ?? "地址信息以机构公开资料为准"}{distance ? ` · ${distance}` : ""}</p>
      {item.matched_department ? <div className="resource-card__department">{item.matched_department}</div> : null}
      {reasons.length > 0 ? (
        <ul className="reason-list">
          {reasons.map((reason) => <li key={reason}>{reason}</li>)}
        </ul>
      ) : null}
      <TrafficAccessNote item={item} />
      <div className="resource-card__actions">
        <AmapNavigationLink target={hospital} className="resource-card__link" />
        <button
          className="resource-card__link"
          type="button"
          onClick={() => typeof hospital.id === "number" && onNavigate(`/resources?hospital=${hospital.id}`)}
          disabled={typeof hospital.id !== "number"}
        >
          公开资料详情 <ExternalLink size={14} aria-hidden="true" />
        </button>
      </div>
    </article>
  );
}

function DoctorRow({
  item,
  onNavigate,
  favorite,
  onToggleFavorite,
}: {
  item: RecommendedDoctor;
  onNavigate: (path: string) => void;
  favorite: boolean;
  onToggleFavorite: (doctorId: number) => void;
}) {
  const doctor = item.doctor;
  return (
    <div className="doctor-row doctor-row--with-favorite">
      <button
        className="doctor-row__main"
        type="button"
        onClick={() => typeof doctor.id === "number" && onNavigate(`/resources?doctor=${doctor.id}`)}
        disabled={typeof doctor.id !== "number"}
      >
        <DoctorAvatar name={doctor.name} photoUrl={doctor.photo_url} />
        <div>
          <strong>{doctorName(item)}</strong>
          <span>{[doctor.title, doctor.department, doctor.hospital_name].filter((value): value is string => Boolean(value)).join(" · ") || "公开医生资料"}</span>
        </div>
      </button>
      {typeof doctor.id === "number" ? (
        <FavoriteDoctorButton doctorId={doctor.id} active={favorite} onToggle={onToggleFavorite} compact />
      ) : null}
    </div>
  );
}

function EmergencyResult({ result, onNavigate }: Pick<TriageResultsProps, "result" | "onNavigate">) {
  const tags = (result.triage?.red_flag_tags ?? []).filter(Boolean).filter((tag, index, all) => all.indexOf(tag) === index).slice(0, 4);
  const reasons = (result.triage?.reasons ?? []).filter(Boolean).slice(0, 2);
  return (
    <article className="safety-result safety-result--emergency" role="alert" aria-labelledby="emergency-result-title">
      <div className="safety-result__signal"><ShieldAlert size={18} aria-hidden="true" /><span>高风险 · 安全优先</span></div>
      <StatusPill tone="danger">需要优先评估</StatusPill>
      <h2 id="emergency-result-title">需要优先进行紧急医疗评估</h2>
      <p>不要继续等待在线推荐结果。如果当前情况紧急、持续加重或有人意识/呼吸异常，请立即联系当地急救服务。</p>
      {tags.length > 0 ? (
        <div className="safety-signals">
          <span className="eyebrow eyebrow--muted">描述中返回的风险信号</span>
          <ul>{tags.map((tag) => <li key={tag}>{tag}</li>)}</ul>
        </div>
      ) : null}
      {reasons.length > 0 ? <p className="safety-result__reason">{reasons.join(" ")}</p> : null}
      <div className="safety-result__actions">
        <a className="button button--danger" href="tel:120"><PhoneCall size={17} aria-hidden="true" /> 拨打 120</a>
        <Button variant="secondary" onClick={() => onNavigate("/map")} icon={<MapPinned size={16} aria-hidden="true" />}>查看急诊资源</Button>
      </div>
      <small>系统只提供辅助分流信息，不替代急救指令、医生诊断或处方。</small>
    </article>
  );
}

function RoutineOrUrgentResult({
  result,
  recommendations,
  recommendationsLoading,
  recommendationsError,
  onLoadRecommendations,
  onNavigate,
}: Omit<TriageResultsProps, "onNavigate"> & Pick<TriageResultsProps, "onNavigate">) {
  const { isFavorite, toggleFavorite } = useFavoriteDoctors();
  const insufficient = result.triage_status === "INSUFFICIENT_INFORMATION";
  const urgent = result.triage_status === "URGENT";
  const title = insufficient ? "还需要一点信息，才能继续" : urgent ? "建议尽快进行医疗评估" : "可以继续了解合适的就医路径";
  const detail = insufficient
    ? "当前描述不足以支持下一步资源路径。请先完成一项补充说明，系统会再次整理完整描述。"
    : urgent
    ? "当前结果表示需要尽快获得专业医疗评估；如果症状加重或出现危险信号，请优先急诊。"
    : "当前返回的安全状态未提示需要立即急诊；这不是诊断结论，建议结合专业医疗意见。";
  return (
    <article className={`safety-result safety-result--${insufficient ? "insufficient" : urgent ? "urgent" : "routine"}`} aria-labelledby="care-result-title">
      <div className="safety-result__signal"><Sparkles size={18} aria-hidden="true" /><span>{insufficient ? "需要补充信息" : urgent ? "建议尽快评估" : "可以继续了解"}</span></div>
      <StatusPill tone={insufficient ? "neutral" : urgent ? "warning" : "success"}>{insufficient ? "需要补充信息" : urgent ? "建议尽快评估" : "可继续了解路径"}</StatusPill>
      <h2 id="care-result-title">{title}</h2>
      <p>{detail}</p>
      {result.matched_department ? <div className="safety-result__department"><span>建议首先了解</span><strong>{result.matched_department}</strong></div> : null}
      {!insufficient ? <div className="primary-path">
        <div className="primary-path__heading"><span className="eyebrow eyebrow--muted">主要就医路径</span><span>{recommendations ? "已找到资源" : "等待资源匹配"}</span></div>
        {recommendationsLoading ? <div className="result-loading" aria-live="polite">正在读取城市资源路径…</div> : null}
        {recommendationsError ? <RecommendationError message={recommendationsError} onRetry={onLoadRecommendations} /> : null}
        {!recommendations && !recommendationsLoading && !recommendationsError ? (
          <div className="primary-path__empty">
            <p>继续查看当前就医资源建议，页面会保留来源与推荐依据。</p>
            <Button variant="secondary" onClick={onLoadRecommendations} icon={<ArrowRight size={16} aria-hidden="true" />}>查看当前资源路径</Button>
          </div>
        ) : null}
        {recommendations ? (
          <div className="recommendation-content">
            <div className="recommendation-content__meta">{recommendations.resource_strategy?.visit_path ?? "门诊路径"} · {resourceSourceLabel(recommendations.data_source)}</div>
            {recommendations.recommended_hospitals.length > 0 ? (
              <div className="hospital-results">
                {recommendations.recommended_hospitals.slice(0, 3).map((item, index) => <HospitalCard item={item} index={index} onNavigate={onNavigate} key={`${hospitalName(item)}-${index}`} />)}
              </div>
            ) : <p className="result-empty">当前没有可展示的医院路径，请稍后重试或浏览医疗资源。</p>}
            {recommendations.recommended_doctors.length > 0 ? (
              <div className="doctor-preview">
                <div className="doctor-preview__heading"><span className="eyebrow eyebrow--muted">公开医生资料预览</span><span>医院路径优先</span></div>
                {recommendations.recommended_doctors.slice(0, 3).map((item, index) => (
                  <DoctorRow
                    item={item}
                    onNavigate={onNavigate}
                    key={`${doctorName(item)}-${index}`}
                    favorite={typeof item.doctor.id === "number" ? isFavorite(item.doctor.id) : false}
                    onToggleFavorite={toggleFavorite}
                  />
                ))}
              </div>
            ) : null}
            <p className="recommendation-notice">推荐分只用于资源排序，不代表诊断概率或治疗效果概率。来源和更新时间以资源详情为准。</p>
          </div>
        ) : null}
      </div> : null}
    </article>
  );
}

export function TriageResults({
  result,
  recommendations,
  recommendationsLoading,
  recommendationsError,
  onLoadRecommendations,
  onNavigate,
}: TriageResultsProps) {
  if (result.triage_status === "EMERGENCY") return <EmergencyResult result={result} onNavigate={onNavigate} />;
  return (
    <RoutineOrUrgentResult
      result={result}
      recommendations={recommendations}
      recommendationsLoading={recommendationsLoading}
      recommendationsError={recommendationsError}
      onLoadRecommendations={onLoadRecommendations}
      onNavigate={onNavigate}
    />
  );
}
