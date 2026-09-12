import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Building2,
  CircleAlert,
  ExternalLink,
  Filter,
  LoaderCircle,
  MapPinned,
  RotateCcw,
  Search,
  Stethoscope,
  X,
} from "lucide-react";
import { ApiError } from "../api/client";
import { getDoctorDetail, getDoctors, getHospitalDetail, getHospitals } from "../api/resources";
import { Button } from "../components/ui/Button";
import { StatusPill } from "../components/ui/StatusPill";
import { AmapNavigationLink } from "../components/ui/AmapNavigationLink";
import { DoctorAvatar } from "../components/ui/DoctorAvatar";
import { HospitalLogo } from "../components/ui/HospitalLogo";
import { FavoriteDoctorButton } from "../components/ui/FavoriteDoctorButton";
import { useFavoriteDoctors } from "../state/favoriteDoctors";
import type { DoctorRecord, HospitalRecord, ResourceDetailPayload } from "../types/api";

type ResourceTab = "overview" | "hospitals" | "doctors";
type Selection =
  | { kind: "hospital"; item: HospitalRecord }
  | { kind: "doctor"; item: DoctorRecord };

function errorFor(reason: unknown, fallback: string): ApiError {
  return reason instanceof ApiError ? reason : new ApiError("NETWORK_ERROR", fallback);
}

function sourceLabel(source: string): string {
  if (source.includes("provisional")) return "医院目录 · 暂待核验";
  if (source.includes("pending")) return "医院目录 · 资料核验中";
  if (source.includes("public")) return "公开资料 · 来源混合";
  return "资料来源待补齐";
}

function includesQuery(values: Array<string | undefined>, query: string): boolean {
  if (!query) return true;
  return values.some((value) => value?.toLocaleLowerCase().includes(query));
}

function HospitalCard({
  hospital,
  selected,
  onSelect,
}: {
  hospital: HospitalRecord;
  selected: boolean;
  onSelect: () => void;
}) {
  const departments = (hospital.departments ?? []).slice(0, 3);
  const meta = [hospital.level, hospital.type].filter((value): value is string => Boolean(value));
  return (
    <article className={`resource-index-card${selected ? " resource-index-card--selected" : ""}`}>
      <HospitalLogo hospitalId={typeof hospital.id === "number" ? hospital.id : undefined} />
      <div className="resource-index-card__body">
        <div className="resource-index-card__topline">
          {hospital.emergency ? <span className="resource-index-card__flag resource-index-card__flag--emergency">急诊字段</span> : <span className="resource-index-card__flag">医院</span>}
          {hospital.district ? <span className="resource-index-card__district">{hospital.district}</span> : null}
        </div>
        <h3>{hospital.name ?? "未命名医院"}</h3>
        {meta.length > 0 ? <p className="resource-index-card__subline">{meta.join(" · ")}</p> : null}
        <p className="resource-index-card__address">{hospital.address ?? "地址以机构公开资料为准"}</p>
        {departments.length > 0 ? (
          <div className="resource-chip-list" aria-label="主要科室">
            {departments.map((department) => <span key={department}>{department}</span>)}
            {(hospital.departments?.length ?? 0) > 3 ? <span className="resource-chip-list__more">+{(hospital.departments?.length ?? 0) - 3}</span> : null}
          </div>
        ) : null}
        <div className="resource-index-card__actions">
          <button className="resource-index-card__link" type="button" onClick={onSelect} aria-pressed={selected}>
            {selected ? "查看中" : "公开资料"} <ExternalLink size={13} aria-hidden="true" />
          </button>
          <AmapNavigationLink target={hospital} className="resource-index-card__link" />
        </div>
      </div>
    </article>
  );
}

function DoctorCard({
  doctor,
  selected,
  onSelect,
  favorite,
  onToggleFavorite,
}: {
  doctor: DoctorRecord;
  selected: boolean;
  onSelect: () => void;
  favorite: boolean;
  onToggleFavorite: (doctorId: number) => void;
}) {
  const specialties = (doctor.specialties ?? []).slice(0, 2);
  return (
    <article className={`resource-index-card resource-index-card--doctor${selected ? " resource-index-card--selected" : ""}`}>
      <DoctorAvatar name={doctor.name} photoUrl={doctor.photo_url} />
      <div className="resource-index-card__body">
        <div className="resource-index-card__topline">
          <span className="resource-index-card__flag">医生</span>
          <div className="resource-index-card__topline-actions">
            {doctor.outpatient_time ? <span className="resource-index-card__flag">门诊</span> : null}
            {typeof doctor.id === "number" ? (
              <FavoriteDoctorButton
                doctorId={doctor.id}
                active={favorite}
                onToggle={onToggleFavorite}
                compact
              />
            ) : null}
          </div>
        </div>
        <h3>{doctor.name ?? "公开医生资料"}</h3>
        <p className="resource-index-card__subline">{[doctor.title, doctor.department].filter((value): value is string => Boolean(value)).join(" · ") || "职称/科室未提供"}</p>
        <p className="resource-index-card__address">{doctor.hospital_name ?? "所属医院未提供"}</p>
        {specialties.length > 0 ? (
          <div className="resource-chip-list" aria-label="公开专长">
            {specialties.map((specialty) => <span key={specialty}>{specialty}</span>)}
          </div>
        ) : null}
        <div className="resource-index-card__actions">
          <button className="resource-index-card__link" type="button" onClick={onSelect} aria-pressed={selected}>
            {selected ? "查看中" : "公开资料"} <ExternalLink size={13} aria-hidden="true" />
          </button>
        </div>
      </div>
    </article>
  );
}

function ResourceProvenanceNote({ detail }: { detail: ResourceDetailPayload }) {
  return (
    <div className="resource-detail__provenance">
      <StatusPill tone="warning">{sourceLabel(detail.provenance.source_class)}</StatusPill>
      <span>{detail.provenance.notice}</span>
      <small>
        更新时间：{detail.provenance.last_updated ?? "未登记"} · 许可状态：{detail.provenance.license_status === "not_recorded" ? "未登记" : detail.provenance.license_status}
      </small>
    </div>
  );
}

function ResourceDetail({
  selection,
  detail,
  loading,
  error,
  onRetry,
  onClose,
  onNavigate,
  isFavorite,
  onToggleFavorite,
}: {
  selection: Selection;
  detail: ResourceDetailPayload | null;
  loading: boolean;
  error: ApiError | null;
  onRetry: () => void;
  onClose: () => void;
  onNavigate: (path: string) => void;
  isFavorite: (doctorId: number) => boolean;
  onToggleFavorite: (doctorId: number) => void;
}) {
  return (
    <aside className="resource-detail" aria-labelledby="resource-detail-title">
      <div className="resource-detail__topline"><span className="eyebrow">资料详情</span><button type="button" onClick={onClose} aria-label="关闭资料详情"><X size={18} aria-hidden="true" /></button></div>
      {loading ? <div className="resource-detail__state" aria-live="polite"><LoaderCircle className="spin" size={18} aria-hidden="true" /> 正在读取详情…</div> : null}
      {!loading && error ? <div className="resource-detail__state resource-detail__state--error" role="alert"><CircleAlert size={18} aria-hidden="true" /><span>{error.message}</span><button type="button" onClick={onRetry}>重试</button></div> : null}
      {!loading && !error && detail?.resource_type === "hospital" ? (() => {
        const hospital = detail.resource;
        return (
          <>
            <div className="resource-detail__identity">
              <HospitalLogo hospitalId={typeof hospital.id === "number" ? hospital.id : undefined} size="preview" />
              <div><h2 id="resource-detail-title">{hospital.name ?? "未命名医院"}</h2><p>{[hospital.level, hospital.type].filter((value): value is string => Boolean(value)).join(" · ") || "公开机构资料"}</p></div>
            </div>
            <p className="resource-detail__lede">当前展示公开机构字段与派生能力线索；不构成官方排名、疗效或临床质量结论。</p>
            <dl className="resource-detail__facts">
              <div><dt>机构类型</dt><dd>{[hospital.level, hospital.type].filter((value): value is string => Boolean(value)).join(" · ") || "未提供"}</dd></div>
              <div><dt>地址</dt><dd>{hospital.address ?? "未提供"}</dd></div>
              <div><dt>区域</dt><dd>{hospital.district ?? "公开资料未可靠标注行政区"}</dd></div>
              <div><dt>电话</dt><dd>{hospital.phone ?? "未提供"}</dd></div>
              <div><dt>急诊字段</dt><dd>{hospital.emergency === true ? "资料显示设有急诊（非实时接诊能力）" : "资料未标记急诊"}</dd></div>
              <div><dt>关联医生</dt><dd>{detail.related.doctor_count} 条公开索引</dd></div>
            </dl>
            {detail.derived_capability?.areas.length ? <div className="resource-detail__section"><span className="eyebrow eyebrow--muted">派生能力线索 · {detail.derived_capability.status}</span><p>{detail.derived_capability.areas.slice(0, 8).join(" · ")}</p><small>{detail.derived_capability.notice} 公式版本：{detail.derived_capability.formula_version}</small></div> : null}
            {detail.related.doctors?.length ? <div className="resource-detail__section"><span className="eyebrow eyebrow--muted">关联公开医生</span><div className="resource-detail__related-list">{detail.related.doctors.slice(0, 8).map((doctor) => <button type="button" key={String(doctor.id ?? doctor.name)} onClick={() => typeof doctor.id === "number" && onNavigate("/resources?doctor=" + doctor.id)}><strong>{doctor.name ?? "公开医生资料"}</strong><span>{[doctor.title, doctor.department].filter((value): value is string => Boolean(value)).join(" · ") || "公开资料"}</span></button>)}</div></div> : null}
            <AmapNavigationLink target={hospital} className="resource-detail__navigation" />
            <ResourceProvenanceNote detail={detail} />
          </>
        );
      })() : null}
      {!loading && !error && detail?.resource_type === "doctor" ? (() => {
        const doctor = detail.resource;
        return (
          <>
            <div className="resource-detail__identity">
              <DoctorAvatar name={doctor.name} photoUrl={doctor.photo_url} size="large" />
              <div>
                <h2 id="resource-detail-title">{doctor.name ?? "公开医生资料"}</h2>
                <p>{[doctor.title, doctor.department].filter((value): value is string => Boolean(value)).join(" · ") || "职称/科室未提供"}</p>
                {typeof doctor.id === "number" ? (
                  <FavoriteDoctorButton
                    doctorId={doctor.id}
                    active={isFavorite(doctor.id)}
                    onToggle={onToggleFavorite}
                  />
                ) : null}
              </div>
            </div>
            <dl className="resource-detail__facts">
              <div><dt>所属医院</dt><dd>{doctor.hospital_name ?? "未提供"}</dd></div>
              <div><dt>公开专长</dt><dd>{doctor.specialties?.slice(0, 6).join(" · ") || doctor.specialty || "未提供"}</dd></div>
              <div><dt>门诊字段</dt><dd>{doctor.outpatient_time ?? "未提供"}</dd></div>
              <div><dt>关联医院详情</dt><dd>{detail.related.hospital?.name ?? "未关联"}</dd></div>
              <div>
                <dt>资料来源</dt>
                <dd>
                  {doctor.doctor_page_url ? (
                    <a href={doctor.doctor_page_url} target="_blank" rel="noreferrer">查看公开医生主页</a>
                  ) : doctor.photo_url ? (
                    "医院公开资料 / 本地公开照片资产"
                  ) : (
                    "公开资料索引"
                  )}
                  {doctor.photo_provenance_status ? ` · 照片状态 ${doctor.photo_provenance_status}` : ""}
                </dd>
              </div>
            </dl>
            <p className="resource-detail__lede">公开科研与资料信息不等于临床 patient-fit，不作为主要推荐依据。</p>
            {detail.related.hospital ? <AmapNavigationLink target={detail.related.hospital} label="导航到所属医院" className="resource-detail__navigation" /> : null}
            <ResourceProvenanceNote detail={detail} />
          </>
        );
      })() : null}
      {!loading && !error && !detail ? <div className="resource-detail__state" role="status">暂未收到详情数据，请重试。</div> : null}
      {!loading && !error && detail && detail.resource_type !== selection.kind ? <div className="resource-detail__state resource-detail__state--error" role="alert">详情类型与当前选择不一致，请重试。</div> : null}
    </aside>
  );
}

export function ResourcesPage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const { isFavorite, toggleFavorite } = useFavoriteDoctors();
  const initialParams = useMemo(() => new URLSearchParams(window.location.search), []);
  const [activeTab, setActiveTab] = useState<ResourceTab>(() => {
    const type = initialParams.get("type");
    if (type === "doctor" || type === "doctors") return "doctors";
    if (type === "hospital" || type === "hospitals") return "hospitals";
    return "overview";
  });
  const [query, setQuery] = useState(initialParams.get("q") ?? "");
  const [hospitalLevel, setHospitalLevel] = useState(initialParams.get("level") ?? "");
  const [hospitalType, setHospitalType] = useState(initialParams.get("hospital_type") ?? "");
  const [hospitalDistrict, setHospitalDistrict] = useState(initialParams.get("district") ?? "");
  const [hospitalEmergency, setHospitalEmergency] = useState(initialParams.get("emergency") ?? "");
  const [doctorHospital, setDoctorHospital] = useState(initialParams.get("hospital_name") ?? "");
  const [doctorDepartment, setDoctorDepartment] = useState(initialParams.get("department") ?? "");
  const [doctorTitle, setDoctorTitle] = useState(initialParams.get("title") ?? "");
  const [hospitals, setHospitals] = useState<HospitalRecord[]>([]);
  const [hospitalSource, setHospitalSource] = useState("unknown");
  const [doctors, setDoctors] = useState<DoctorRecord[]>([]);
  const [doctorSource, setDoctorSource] = useState("unknown");
  const [doctorPage, setDoctorPage] = useState(() => {
    const page = Number(initialParams.get("page"));
    return Number.isInteger(page) && page > 0 ? page : 1;
  });
  const [doctorTotal, setDoctorTotal] = useState(0);
  const [doctorHasMore, setDoctorHasMore] = useState(false);
  const [doctorFacets, setDoctorFacets] = useState<{
    hospital_names: string[];
    departments: string[];
    titles: string[];
  }>({ hospital_names: [], departments: [], titles: [] });
  const [hospitalLoading, setHospitalLoading] = useState(true);
  const [doctorLoading, setDoctorLoading] = useState(false);
  const [doctorAppending, setDoctorAppending] = useState(false);
  const [hospitalError, setHospitalError] = useState<ApiError | null>(null);
  const [doctorError, setDoctorError] = useState<ApiError | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [detail, setDetail] = useState<ResourceDetailPayload | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<ApiError | null>(null);
  const [detailAttempt, setDetailAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setHospitalLoading(true);
    getHospitals(controller.signal).then((payload) => {
      if (controller.signal.aborted) return;
      setHospitals(payload.items);
      setHospitalSource(payload.source);
      setHospitalError(null);
    }).catch((reason) => {
      if (!controller.signal.aborted) setHospitalError(errorFor(reason, "医院资源暂时无法载入。"));
    }).finally(() => {
      if (!controller.signal.aborted) setHospitalLoading(false);
    });
    return () => controller.abort();
  }, []);

  const doctorFilterKey = `${doctorHospital}|${doctorDepartment}|${doctorTitle}|${query.trim()}`;

  useEffect(() => {
    if (activeTab !== "doctors") return;
    const controller = new AbortController();
    setDoctorLoading(true);
    getDoctors({
      hospitalName: doctorHospital || undefined,
      department: doctorDepartment || undefined,
      title: doctorTitle || undefined,
      q: query.trim() || undefined,
      page: 1,
      pageSize: 24,
      signal: controller.signal,
    }).then((payload) => {
      if (controller.signal.aborted) return;
      setDoctors(payload.items);
      setDoctorSource(payload.source);
      setDoctorPage(1);
      setDoctorTotal(payload.total ?? payload.count);
      setDoctorHasMore(Boolean(payload.has_more));
      if (payload.facets) setDoctorFacets(payload.facets);
      setDoctorError(null);
    }).catch((reason) => {
      if (!controller.signal.aborted) setDoctorError(errorFor(reason, "医生资源暂时无法载入。"));
    }).finally(() => {
      if (!controller.signal.aborted) setDoctorLoading(false);
    });
    return () => controller.abort();
    // doctorFilterKey intentionally aggregates the filter inputs that reset to page 1.
  }, [activeTab, doctorFilterKey]);

  function loadMoreDoctors() {
    if (!doctorHasMore || doctorLoading || doctorAppending) return;
    const nextPage = doctorPage + 1;
    setDoctorAppending(true);
    getDoctors({
      hospitalName: doctorHospital || undefined,
      department: doctorDepartment || undefined,
      title: doctorTitle || undefined,
      q: query.trim() || undefined,
      page: nextPage,
      pageSize: 24,
    }).then((payload) => {
      setDoctors((previous) => {
        const seen = new Set(previous.map((item) => item.id));
        const merged = [...previous];
        for (const item of payload.items) {
          if (!seen.has(item.id)) merged.push(item);
        }
        return merged;
      });
      setDoctorPage(nextPage);
      setDoctorTotal(payload.total ?? payload.count);
      setDoctorHasMore(Boolean(payload.has_more));
      if (payload.facets) setDoctorFacets(payload.facets);
      setDoctorSource(payload.source);
    }).catch((reason) => setDoctorError(errorFor(reason, "医生资源暂时无法载入。")))
      .finally(() => setDoctorAppending(false));
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const hospitalId = Number(params.get("hospital"));
    if (Number.isInteger(hospitalId) && hospitalId > 0 && hospitals.length > 0) {
      const hospital = hospitals.find((item) => item.id === hospitalId);
      if (hospital) {
        setActiveTab("hospitals");
        setSelection({ kind: "hospital", item: hospital });
        return;
      }
    }
    const doctorId = Number(params.get("doctor"));
    if (!Number.isInteger(doctorId) || doctorId <= 0) return;
    setActiveTab("doctors");
    const cached = doctors.find((item) => item.id === doctorId);
    if (cached) {
      setSelection({ kind: "doctor", item: cached });
      return;
    }
    const controller = new AbortController();
    getDoctorDetail(doctorId, controller.signal).then((payload) => {
      if (controller.signal.aborted) return;
      setSelection({ kind: "doctor", item: payload.resource });
    }).catch(() => {
      if (!controller.signal.aborted) {
        setDoctorError(new ApiError("RESOURCE_NOT_FOUND", "该医生资料暂时无法载入。"));
      }
    });
    return () => controller.abort();
  }, [hospitals, doctors]);

  useEffect(() => {
    if (!selection) {
      setDetail(null);
      setDetailError(null);
      setDetailLoading(false);
      return;
    }
    const resourceId = selection.item.id;
    if (typeof resourceId !== "number") {
      setDetail(null);
      setDetailError(new ApiError("INVALID_RESOURCE", "当前资料缺少可查询的资源编号。"));
      setDetailLoading(false);
      return;
    }
    const controller = new AbortController();
    setDetail(null);
    setDetailError(null);
    setDetailLoading(true);
    const request = selection.kind === "hospital"
      ? getHospitalDetail(resourceId, controller.signal)
      : getDoctorDetail(resourceId, controller.signal);
    request.then((payload) => {
      if (controller.signal.aborted) return;
      setDetail(payload);
    }).catch((reason) => {
      if (!controller.signal.aborted) setDetailError(errorFor(reason, "资源详情暂时无法载入。"));
    }).finally(() => {
      if (!controller.signal.aborted) setDetailLoading(false);
    });
    return () => controller.abort();
  }, [detailAttempt, selection]);

  const normalizedQuery = query.trim().toLocaleLowerCase();
  const hospitalLevels = useMemo(
    () => Array.from(new Set(hospitals.map((item) => item.level).filter((value): value is string => Boolean(value)))).sort(),
    [hospitals],
  );
  const hospitalTypes = useMemo(
    () => Array.from(new Set(hospitals.map((item) => item.type).filter((value): value is string => Boolean(value)))).sort(),
    [hospitals],
  );
  const hospitalDistricts = useMemo(
    () => Array.from(new Set(hospitals.map((item) => item.district).filter((value): value is string => typeof value === "string" && Boolean(value)))).sort(),
    [hospitals],
  );
  const doctorHospitalNames = useMemo(
    () => doctorFacets.hospital_names.length
      ? doctorFacets.hospital_names
      : Array.from(new Set(doctors.map((item) => item.hospital_name).filter((value): value is string => Boolean(value)))).sort(),
    [doctorFacets.hospital_names, doctors],
  );
  const doctorDepartments = useMemo(
    () => doctorFacets.departments.length
      ? doctorFacets.departments
      : Array.from(new Set(doctors.map((item) => item.department).filter((value): value is string => Boolean(value)))).sort(),
    [doctorFacets.departments, doctors],
  );
  const doctorTitles = useMemo(
    () => doctorFacets.titles.length
      ? doctorFacets.titles
      : Array.from(new Set(doctors.map((item) => item.title || item.position).filter((value): value is string => Boolean(value)))).sort(),
    [doctorFacets.titles, doctors],
  );
  const filteredHospitals = useMemo(
    () => hospitals.filter((hospital) => {
      if (hospitalLevel && hospital.level !== hospitalLevel) return false;
      if (hospitalType && hospital.type !== hospitalType) return false;
      if (hospitalDistrict && hospital.district !== hospitalDistrict) return false;
      if (hospitalEmergency === "yes" && hospital.emergency !== true) return false;
      if (hospitalEmergency === "no" && hospital.emergency === true) return false;
      return includesQuery([
        hospital.name,
        hospital.alias,
        hospital.address,
        hospital.district ?? undefined,
        ...(hospital.departments ?? []),
        ...(hospital.strengths ?? []),
        ...(hospital.derived_capability_areas ?? []),
      ], normalizedQuery);
    }),
    [hospitals, hospitalLevel, hospitalType, hospitalDistrict, hospitalEmergency, normalizedQuery],
  );
  // Doctor filtering/pagination is server-side; only keep a local safety net for
  // rows already fetched so progressive loading stays consistent.
  const filteredDoctors = useMemo(
    () => doctors.filter((doctor) => {
      if (doctorHospital && doctor.hospital_name !== doctorHospital) return false;
      if (doctorDepartment && doctor.department !== doctorDepartment) return false;
      if (doctorTitle && (doctor.title || doctor.position) !== doctorTitle) return false;
      return includesQuery([
        doctor.name,
        doctor.hospital_name,
        doctor.department,
        doctor.specialty,
        ...(doctor.specialties ?? []),
      ], normalizedQuery);
    }),
    [doctors, doctorHospital, doctorDepartment, doctorTitle, normalizedQuery],
  );
  const visibleDoctors = filteredDoctors;
  const showingDoctors = activeTab === "doctors";
  const showingHospitals = activeTab !== "doctors";
  const resultCount = showingDoctors ? doctorTotal : filteredHospitals.length;
  const hasActiveFilters = Boolean(hospitalLevel || hospitalType || hospitalDistrict || hospitalEmergency || doctorHospital || doctorDepartment || doctorTitle);

  useEffect(() => {
    const params = new URLSearchParams();
    if (activeTab === "doctors") params.set("type", "doctor");
    if (activeTab === "hospitals") params.set("type", "hospital");
    if (query.trim()) params.set("q", query.trim());
    if (hospitalLevel) params.set("level", hospitalLevel);
    if (hospitalType) params.set("hospital_type", hospitalType);
    if (hospitalDistrict) params.set("district", hospitalDistrict);
    if (hospitalEmergency) params.set("emergency", hospitalEmergency);
    if (doctorHospital) params.set("hospital_name", doctorHospital);
    if (doctorDepartment) params.set("department", doctorDepartment);
    if (doctorTitle) params.set("title", doctorTitle);
    if (selection?.kind === "hospital" && typeof selection.item.id === "number") {
      params.set("hospital", String(selection.item.id));
    } else if (!selection && initialParams.get("hospital")) {
      params.set("hospital", initialParams.get("hospital") as string);
    }
    if (selection?.kind === "doctor" && typeof selection.item.id === "number") {
      params.set("doctor", String(selection.item.id));
    } else if (!selection && initialParams.get("doctor")) {
      params.set("doctor", initialParams.get("doctor") as string);
    }
    const search = params.toString();
    const next = search ? `?${search}` : window.location.pathname;
    window.history.replaceState(null, "", next);
  }, [activeTab, query, hospitalLevel, hospitalType, hospitalDistrict, hospitalEmergency, doctorHospital, doctorDepartment, doctorTitle, selection]);

  function resetFilters() {
    setQuery("");
    setHospitalLevel("");
    setHospitalType("");
    setHospitalDistrict("");
    setHospitalEmergency("");
    setDoctorHospital("");
    setDoctorDepartment("");
    setDoctorTitle("");
  }

  function retryHospitals() {
    setHospitalError(null);
    setHospitalLoading(true);
    getHospitals().then((payload) => {
      setHospitals(payload.items);
      setHospitalSource(payload.source);
    }).catch((reason) => setHospitalError(errorFor(reason, "医院资源暂时无法载入。"))).finally(() => setHospitalLoading(false));
  }

  function retryDoctors() {
    setDoctorError(null);
    setDoctorLoading(true);
    getDoctors({
      hospitalName: doctorHospital || undefined,
      department: doctorDepartment || undefined,
      title: doctorTitle || undefined,
      q: query.trim() || undefined,
      page: 1,
      pageSize: 24,
    }).then((payload) => {
      setDoctors(payload.items);
      setDoctorSource(payload.source);
      setDoctorPage(1);
      setDoctorTotal(payload.total ?? payload.count);
      setDoctorHasMore(Boolean(payload.has_more));
      if (payload.facets) setDoctorFacets(payload.facets);
    }).catch((reason) => setDoctorError(errorFor(reason, "医生资源暂时无法载入。"))).finally(() => setDoctorLoading(false));
  }

  return (
    <section className="resources-page page-container">
      <div className="resources-page__hero">
        <div>
          <span className="eyebrow">常州医疗资源 · 320400</span>
          <h1>把城市资源，<em>放回你的就医路径。</em></h1>
          <p>搜索医院、科室或医生，先从公开资料了解可用资源。个性化推荐仍以问诊结果和服务端解释为准。</p>
        </div>
        <div className="resources-page__hero-note"><Stethoscope size={18} strokeWidth={1.5} aria-hidden="true" /><span>公开资料索引</span><small>不是诊断，也不是官方排名。</small></div>
      </div>

      <div className="resources-toolbar">
        <label className="resources-search"><Search size={18} aria-hidden="true" /><span className="sr-only">搜索医疗资源</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索医院、科室或医生" /></label>
        <Button variant="secondary" onClick={() => onNavigate("/map")} icon={<MapPinned size={16} aria-hidden="true" />}>打开医院地图</Button>
      </div>

      <div className="resources-filters" aria-label={activeTab === "doctors" ? "医生筛选" : "医院筛选"}>
        <span className="resources-filters__label"><Filter size={14} aria-hidden="true" /> 筛选</span>
        {activeTab !== "doctors" ? (
          <>
            <label className="resources-filters__field">
              <span className="sr-only">医院等级</span>
              <select value={hospitalLevel} onChange={(event) => setHospitalLevel(event.target.value)} data-testid="filter-hospital-level">
                <option value="">全部等级</option>
                {hospitalLevels.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
            <label className="resources-filters__field">
              <span className="sr-only">医院类型</span>
              <select value={hospitalType} onChange={(event) => setHospitalType(event.target.value)} data-testid="filter-hospital-type">
                <option value="">全部类型</option>
                {hospitalTypes.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
            <label className="resources-filters__field">
              <span className="sr-only">区域</span>
              <select value={hospitalDistrict} onChange={(event) => setHospitalDistrict(event.target.value)} data-testid="filter-hospital-district">
                <option value="">全部区域</option>
                {hospitalDistricts.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
            <label className="resources-filters__field">
              <span className="sr-only">急诊字段</span>
              <select value={hospitalEmergency} onChange={(event) => setHospitalEmergency(event.target.value)} data-testid="filter-hospital-emergency">
                <option value="">急诊字段不限</option>
                <option value="yes">资料显示设有急诊</option>
                <option value="no">资料未标记急诊</option>
              </select>
            </label>
          </>
        ) : (
          <>
            <label className="resources-filters__field">
              <span className="sr-only">所属医院</span>
              <select value={doctorHospital} onChange={(event) => setDoctorHospital(event.target.value)} data-testid="filter-doctor-hospital">
                <option value="">全部医院</option>
                {doctorHospitalNames.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
            <label className="resources-filters__field">
              <span className="sr-only">科室</span>
              <select value={doctorDepartment} onChange={(event) => setDoctorDepartment(event.target.value)} data-testid="filter-doctor-department">
                <option value="">全部科室</option>
                {doctorDepartments.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
            <label className="resources-filters__field">
              <span className="sr-only">职称</span>
              <select value={doctorTitle} onChange={(event) => setDoctorTitle(event.target.value)} data-testid="filter-doctor-title">
                <option value="">全部职称</option>
                {doctorTitles.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
          </>
        )}
        {hasActiveFilters || query.trim() ? (
          <button className="resources-filters__reset" type="button" onClick={resetFilters}>
            <RotateCcw size={13} aria-hidden="true" /> 重置
          </button>
        ) : null}
      </div>

      <div className="resources-tabs" role="tablist" aria-label="医疗资源类型">
        {([[
          "overview", "资源总览",
        ], ["hospitals", "医院"], ["doctors", "医生"]] as Array<[ResourceTab, string]>).map(([tab, label]) => (
          <button key={tab} id={`resource-tab-${tab}`} type="button" role="tab" aria-controls="resource-results-panel" aria-selected={activeTab === tab} tabIndex={activeTab === tab ? 0 : -1} className={activeTab === tab ? "is-active" : ""} onClick={() => { setActiveTab(tab); setSelection(null); }}>
            {label}
          </button>
        ))}
        <span className="resources-tabs__hint"><Filter size={14} aria-hidden="true" /> {resultCount > 0 ? `${resultCount.toLocaleString("zh-CN")} 条可筛选资料` : "等待资源"}</span>
      </div>

      <div className="resources-source-row">
        <StatusPill tone={hospitalSource.includes("pending") ? "warning" : "neutral"}>{sourceLabel(showingDoctors ? doctorSource : hospitalSource)}</StatusPill>
        <span>筛选只改变当前列表展示，不会改变个性化推荐结果。</span>
      </div>

      <div id="resource-results-panel" role="tabpanel" aria-labelledby={`resource-tab-${activeTab}`} tabIndex={-1}>
        {showingHospitals && hospitalError ? <div className="resources-error" role="alert"><CircleAlert size={18} aria-hidden="true" /><span>{hospitalError.message}</span><button type="button" onClick={retryHospitals}>重试</button></div> : null}
        {showingDoctors && doctorError ? <div className="resources-error" role="alert"><CircleAlert size={18} aria-hidden="true" /><span>{doctorError.message}</span><button type="button" onClick={retryDoctors}>重试</button></div> : null}

        {showingHospitals && hospitalLoading ? <div className="resources-loading" aria-live="polite"><LoaderCircle className="spin" size={18} aria-hidden="true" /> 正在读取医院索引…</div> : null}
        {showingDoctors && doctorLoading ? <div className="resources-loading" aria-live="polite"><LoaderCircle className="spin" size={18} aria-hidden="true" /> 正在读取医生公开资料…</div> : null}

        {!hospitalLoading && showingHospitals && !hospitalError && filteredHospitals.length === 0 ? <div className="resources-empty"><Building2 size={22} aria-hidden="true" /><strong>没有匹配的医院资料</strong><span>可以换一个医院名称、地址或科室关键词。</span></div> : null}
        {!doctorLoading && showingDoctors && !doctorError && filteredDoctors.length === 0 ? <div className="resources-empty"><Stethoscope size={22} aria-hidden="true" /><strong>没有匹配的医生资料</strong><span>可以换一个姓名、医院、科室或公开专长关键词。</span></div> : null}

        {showingHospitals && !hospitalLoading && !hospitalError && filteredHospitals.length > 0 ? (
          <div className={`resource-index-layout${selection ? " resource-index-layout--with-detail" : ""}`}>
            <div className="resource-index-grid">{filteredHospitals.map((hospital) => <HospitalCard key={String(hospital.id ?? hospital.name)} hospital={hospital} selected={selection?.kind === "hospital" && selection.item.id === hospital.id} onSelect={() => setSelection({ kind: "hospital", item: hospital })} />)}</div>
            {selection ? <ResourceDetail selection={selection} detail={detail} loading={detailLoading} error={detailError} onRetry={() => setDetailAttempt((value) => value + 1)} onClose={() => setSelection(null)} onNavigate={onNavigate} isFavorite={isFavorite} onToggleFavorite={toggleFavorite} /> : null}
          </div>
        ) : null}

        {showingDoctors && !doctorLoading && !doctorError && visibleDoctors.length > 0 ? (
          <div className={`resource-index-layout${selection ? " resource-index-layout--with-detail" : ""}`}>
            <div>
              <div className="resource-index-grid">{visibleDoctors.map((doctor, index) => (
                <DoctorCard
                  key={String(doctor.id ?? `${doctor.name}-${index}`)}
                  doctor={doctor}
                  selected={selection?.kind === "doctor" && selection.item.id === doctor.id}
                  onSelect={() => setSelection({ kind: "doctor", item: doctor })}
                  favorite={typeof doctor.id === "number" ? isFavorite(doctor.id) : false}
                  onToggleFavorite={toggleFavorite}
                />
              ))}</div>
              <p className="resource-index-cap" aria-live="polite">
                已加载 {visibleDoctors.length.toLocaleString("zh-CN")} / {doctorTotal.toLocaleString("zh-CN")} 条公开医生资料
                {doctorHasMore ? "。" : "。已到末页。"}
              </p>
              {doctorHasMore ? (
                <div className="resource-index-pagination">
                  <Button
                    variant="secondary"
                    onClick={loadMoreDoctors}
                    disabled={doctorAppending}
                    icon={doctorAppending ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : undefined}
                  >
                    {doctorAppending ? "正在加载…" : "加载更多"}
                  </Button>
                </div>
              ) : null}
            </div>
            {selection ? <ResourceDetail selection={selection} detail={detail} loading={detailLoading} error={detailError} onRetry={() => setDetailAttempt((value) => value + 1)} onClose={() => setSelection(null)} onNavigate={onNavigate} isFavorite={isFavorite} onToggleFavorite={toggleFavorite} /> : null}
          </div>
        ) : null}
      </div>

      <div className="resources-page__footer-note"><ArrowRight size={15} aria-hidden="true" /><span>需要根据当前症状寻找路径？</span><button type="button" onClick={() => onNavigate("/triage")}>开始智能分诊</button></div>
    </section>
  );
}
