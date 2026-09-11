import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  Building2,
  CircleAlert,
  ExternalLink,
  Filter,
  LoaderCircle,
  MapPinned,
  Search,
  Stethoscope,
  X,
} from "lucide-react";
import { ApiError } from "../api/client";
import { getDoctorDetail, getDoctors, getHospitalDetail, getHospitals } from "../api/resources";
import { Button } from "../components/ui/Button";
import { StatusPill } from "../components/ui/StatusPill";
import { AmapNavigationLink } from "../components/ui/AmapNavigationLink";
import type { DoctorRecord, HospitalRecord, ResourceDetailPayload } from "../types/api";

type ResourceTab = "overview" | "hospitals" | "doctors";
type Selection =
  | { kind: "hospital"; item: HospitalRecord }
  | { kind: "doctor"; item: DoctorRecord };

function errorFor(reason: unknown, fallback: string): ApiError {
  return reason instanceof ApiError ? reason : new ApiError("NETWORK_ERROR", fallback);
}

function sourceLabel(source: string): string {
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
  const departments = (hospital.departments ?? []).slice(0, 4);
  return (
    <article className={`resource-index-card${selected ? " resource-index-card--selected" : ""}`}>
      <div className="resource-index-card__mark" aria-hidden="true"><Building2 size={20} strokeWidth={1.5} /></div>
      <div className="resource-index-card__body">
        <div className="resource-index-card__topline">
          <span className="eyebrow eyebrow--muted">医院资源</span>
          {hospital.emergency ? <span className="resource-index-card__flag">含急诊字段</span> : null}
        </div>
        <h3>{hospital.name ?? "未命名医院"}</h3>
        <p className="resource-index-card__subline">
          {[hospital.level, hospital.type].filter((value): value is string => Boolean(value)).join(" · ") || "公开资源资料"}
        </p>
        <p className="resource-index-card__address">{hospital.address ?? "地址信息以机构公开资料为准"}</p>
        {departments.length > 0 ? (
          <div className="resource-chip-list" aria-label="主要科室">
            {departments.map((department) => <span key={department}>{department}</span>)}
          </div>
        ) : <p className="resource-index-card__muted">科室信息未在当前接口提供。</p>}
        <div className="resource-index-card__actions">
          <button className="resource-index-card__link" type="button" onClick={onSelect} aria-pressed={selected}>
            {selected ? "正在查看资料" : "查看公开资料"} <ExternalLink size={14} aria-hidden="true" />
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
}: {
  doctor: DoctorRecord;
  selected: boolean;
  onSelect: () => void;
}) {
  const specialties = (doctor.specialties ?? []).slice(0, 3);
  const initial = doctor.name?.slice(0, 1) ?? "医";
  return (
    <article className={`resource-index-card resource-index-card--doctor${selected ? " resource-index-card--selected" : ""}`}>
      <div className="doctor-index-avatar" aria-hidden="true">{initial}</div>
      <div className="resource-index-card__body">
        <div className="resource-index-card__topline">
          <span className="eyebrow eyebrow--muted">公开医生资料</span>
          {doctor.outpatient_time ? <span className="resource-index-card__flag">门诊字段</span> : null}
        </div>
        <h3>{doctor.name ?? "公开医生资料"}</h3>
        <p className="resource-index-card__subline">{[doctor.title, doctor.department].filter((value): value is string => Boolean(value)).join(" · ") || "职称/科室未提供"}</p>
        <p className="resource-index-card__address">{doctor.hospital_name ?? "所属医院未提供"}</p>
        {specialties.length > 0 ? (
          <div className="resource-chip-list" aria-label="公开专长">
            {specialties.map((specialty) => <span key={specialty}>{specialty}</span>)}
          </div>
        ) : <p className="resource-index-card__muted">公开专长未在当前接口提供。</p>}
        <button className="resource-index-card__link" type="button" onClick={onSelect} aria-pressed={selected}>
          {selected ? "正在查看资料" : "查看公开资料"} <ExternalLink size={14} aria-hidden="true" />
        </button>
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
}: {
  selection: Selection;
  detail: ResourceDetailPayload | null;
  loading: boolean;
  error: ApiError | null;
  onRetry: () => void;
  onClose: () => void;
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
            <h2 id="resource-detail-title">{hospital.name ?? "未命名医院"}</h2>
            <p className="resource-detail__lede">{hospital.description ?? "当前接口未提供医院概览；请以机构公开信息为准。"}</p>
            <dl className="resource-detail__facts">
              <div><dt>机构类型</dt><dd>{[hospital.level, hospital.type].filter((value): value is string => Boolean(value)).join(" · ") || "未提供"}</dd></div>
              <div><dt>地址</dt><dd>{hospital.address ?? "未提供"}</dd></div>
              <div><dt>电话</dt><dd>{hospital.phone ?? "未提供"}</dd></div>
              <div><dt>急诊字段</dt><dd>{hospital.emergency === true ? "接口标记为可用" : "接口未标记"}</dd></div>
              <div><dt>关联医生</dt><dd>{detail.related.doctor_count} 条公开索引</dd></div>
            </dl>
            {hospital.strengths?.length ? <div className="resource-detail__section"><span className="eyebrow eyebrow--muted">重点方向字段</span><p>{hospital.strengths.slice(0, 6).join(" · ")}</p></div> : null}
            <AmapNavigationLink target={hospital} className="resource-detail__navigation" />
            <ResourceProvenanceNote detail={detail} />
          </>
        );
      })() : null}
      {!loading && !error && detail?.resource_type === "doctor" ? (() => {
        const doctor = detail.resource;
        return (
          <>
            <div className="resource-detail__identity"><div className="doctor-index-avatar doctor-index-avatar--large" aria-hidden="true">{doctor.name?.slice(0, 1) ?? "医"}</div><div><h2 id="resource-detail-title">{doctor.name ?? "公开医生资料"}</h2><p>{[doctor.title, doctor.department].filter((value): value is string => Boolean(value)).join(" · ") || "职称/科室未提供"}</p></div></div>
            <dl className="resource-detail__facts">
              <div><dt>所属医院</dt><dd>{doctor.hospital_name ?? "未提供"}</dd></div>
              <div><dt>公开专长</dt><dd>{doctor.specialties?.slice(0, 6).join(" · ") || doctor.specialty || "未提供"}</dd></div>
              <div><dt>门诊字段</dt><dd>{doctor.outpatient_time ?? "未提供"}</dd></div>
              <div><dt>关联医院详情</dt><dd>{detail.related.hospital?.name ?? "未关联"}</dd></div>
            </dl>
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
  const [activeTab, setActiveTab] = useState<ResourceTab>("overview");
  const [query, setQuery] = useState("");
  const [hospitals, setHospitals] = useState<HospitalRecord[]>([]);
  const [hospitalSource, setHospitalSource] = useState("unknown");
  const [doctors, setDoctors] = useState<DoctorRecord[]>([]);
  const [doctorSource, setDoctorSource] = useState("unknown");
  const doctorRequestStarted = useRef(false);
  const [hospitalLoading, setHospitalLoading] = useState(true);
  const [doctorLoading, setDoctorLoading] = useState(false);
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

  useEffect(() => {
    if (activeTab !== "doctors" || doctorRequestStarted.current) return;
    const controller = new AbortController();
    doctorRequestStarted.current = true;
    setDoctorLoading(true);
    getDoctors({ signal: controller.signal }).then((payload) => {
      if (controller.signal.aborted) return;
      setDoctors(payload.items);
      setDoctorSource(payload.source);
      setDoctorError(null);
    }).catch((reason) => {
      if (!controller.signal.aborted) setDoctorError(errorFor(reason, "医生资源暂时无法载入。"));
    }).finally(() => {
      if (!controller.signal.aborted) setDoctorLoading(false);
    });
    return () => controller.abort();
  }, [activeTab]);

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
  const filteredHospitals = useMemo(
    () => hospitals.filter((hospital) => includesQuery([
      hospital.name,
      hospital.alias,
      hospital.address,
      ...(hospital.departments ?? []),
      ...(hospital.strengths ?? []),
    ], normalizedQuery)),
    [hospitals, normalizedQuery],
  );
  const filteredDoctors = useMemo(
    () => doctors.filter((doctor) => includesQuery([
      doctor.name,
      doctor.hospital_name,
      doctor.department,
      doctor.specialty,
      ...(doctor.specialties ?? []),
    ], normalizedQuery)),
    [doctors, normalizedQuery],
  );
  const visibleDoctors = filteredDoctors.slice(0, 48);
  const showingDoctors = activeTab === "doctors";
  const showingHospitals = activeTab !== "doctors";
  const resultCount = showingDoctors ? filteredDoctors.length : filteredHospitals.length;

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
    getDoctors().then((payload) => {
      setDoctors(payload.items);
      setDoctorSource(payload.source);
    }).catch((reason) => setDoctorError(errorFor(reason, "医生资源暂时无法载入。"))).finally(() => setDoctorLoading(false));
  }

  return (
    <section className="resources-page page-container">
      <div className="resources-page__hero">
        <div>
          <span className="eyebrow">常州医疗资源 · 320400</span>
          <h1>把城市资源，放回你的<br /><em>就医路径。</em></h1>
          <p>搜索医院、科室或医生，先从公开资料了解可用资源。个性化推荐仍以问诊结果和服务端解释为准。</p>
        </div>
        <div className="resources-page__hero-note"><Stethoscope size={20} strokeWidth={1.4} aria-hidden="true" /><span>公开资料索引</span><small>不是诊断，也不是官方排名。</small></div>
      </div>

      <div className="resources-toolbar">
        <label className="resources-search"><Search size={18} aria-hidden="true" /><span className="sr-only">搜索医疗资源</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索医院、科室或医生" /></label>
        <Button variant="secondary" onClick={() => onNavigate("/map")} icon={<MapPinned size={16} aria-hidden="true" />}>打开医院地图</Button>
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
          <div className="resource-index-layout">
            <div className="resource-index-grid">{filteredHospitals.map((hospital) => <HospitalCard key={String(hospital.id ?? hospital.name)} hospital={hospital} selected={selection?.kind === "hospital" && selection.item.id === hospital.id} onSelect={() => setSelection({ kind: "hospital", item: hospital })} />)}</div>
            {selection ? <ResourceDetail selection={selection} detail={detail} loading={detailLoading} error={detailError} onRetry={() => setDetailAttempt((value) => value + 1)} onClose={() => setSelection(null)} /> : null}
          </div>
        ) : null}

        {showingDoctors && !doctorLoading && !doctorError && visibleDoctors.length > 0 ? (
          <div className="resource-index-layout">
            <div>
              <div className="resource-index-grid">{visibleDoctors.map((doctor, index) => <DoctorCard key={String(doctor.id ?? `${doctor.name}-${index}`)} doctor={doctor} selected={selection?.kind === "doctor" && selection.item.id === doctor.id} onSelect={() => setSelection({ kind: "doctor", item: doctor })} />)}</div>
              {filteredDoctors.length > visibleDoctors.length ? <p className="resource-index-cap">当前展示前 {visibleDoctors.length} 条匹配资料；继续缩小关键词以定位更多结果。</p> : null}
            </div>
            {selection ? <ResourceDetail selection={selection} detail={detail} loading={detailLoading} error={detailError} onRetry={() => setDetailAttempt((value) => value + 1)} onClose={() => setSelection(null)} /> : null}
          </div>
        ) : null}
      </div>

      <div className="resources-page__footer-note"><ArrowRight size={15} aria-hidden="true" /><span>需要根据当前症状寻找路径？</span><button type="button" onClick={() => onNavigate("/triage")}>开始智能分诊</button></div>
    </section>
  );
}
