import { ArrowRight, Check, CircleAlert, MapPinned, PhoneCall, ShieldAlert, SlidersHorizontal, Stethoscope } from "lucide-react";
import { Button } from "../ui/Button";
import { StatusPill } from "../ui/StatusPill";
import { SafetyGateVisual } from "../algorithm/SafetyGateVisual";
import { DepartmentMatchVisual } from "../algorithm/DepartmentMatchVisual";
import type { TriagePayload } from "../../types/api";
import { hospitalContextQuery } from "./recommendationDisplay";

interface TriageResultsProps {
  result: TriagePayload;
  onNavigate: (path: string) => void;
  /** True after follow-up answers were applied so the UI can show path refresh. */
  pathUpdated?: boolean;
  /** Read-only snapshot of the previous round for diff highlight; never drives logic. */
  previousTags?: string[];
  previousDepts?: string[];
  previousDept?: string | null;
}

interface CareActionsProps {
  direction: string | null;
  safety: TriagePayload["triage_status"];
  recommendationsReady: boolean;
  recommendationsLoading: boolean;
  recommendationsError: string | null;
  onOpenPreferences: () => void;
  onLoadRecommendations: () => void;
  onNavigate: (path: string) => void;
}

const STATUS_COPY: Record<TriagePayload["triage_status"], { label: string; headline: string; plain: string }> = {
  EMERGENCY: {
    label: "需要优先评估",
    headline: "需要优先进行紧急医疗评估",
    plain: "描述中出现需要优先处理的危险信号。",
  },
  URGENT: {
    label: "建议尽快评估",
    headline: "建议尽快安排医疗评估",
    plain: "当前描述提示需要在较短时间内获得专业评估。",
  },
  ROUTINE: {
    label: "未提示立即急诊",
    headline: "可以继续了解合适的就医路径",
    plain: "当前描述未提示需要立即急诊；这不是诊断结论。",
  },
  INSUFFICIENT_INFORMATION: {
    label: "需要补充信息",
    headline: "还需要一点信息，才能继续",
    plain: "当前描述还不足以判断就医方向，系统先给出一般性建议。",
  },
};

function careSteps(status: TriagePayload["triage_status"]) {
  const safety = { label: "安全评估", detail: status === "ROUTINE" ? "未提示立即急诊" : status === "URGENT" ? "建议尽快评估" : "已优先处理", done: true };
  if (status === "EMERGENCY") {
    return [safety, { label: "急诊出口", detail: "不再推荐普通就医路径", done: false }];
  }
  if (status === "INSUFFICIENT_INFORMATION") {
    return [safety, { label: "补充信息", detail: "完善理解后继续", done: false }];
  }
  return [safety, { label: "就医方向", detail: "科室方向已给出", done: true }, { label: "城市资源", detail: "医院、医生与导航", done: false }];
}

function EmergencyResult({ result, onNavigate }: Pick<TriageResultsProps, "result" | "onNavigate">) {
  const tags = (result.triage?.red_flag_tags ?? []).filter(Boolean).filter((tag, index, all) => all.indexOf(tag) === index).slice(0, 4);
  const reasons = (result.triage?.reasons ?? []).filter(Boolean).slice(0, 2);
  return (
    <article className="care-result care-result--emergency" role="alert" aria-labelledby="emergency-result-title">
      <div className="care-result__rail" aria-hidden="true" />
      <div className="care-result__status">
        <StatusPill tone="danger"><ShieldAlert size={13} aria-hidden="true" /> {STATUS_COPY.EMERGENCY.label}</StatusPill>
        <span className="care-result__status-note">普通资源推荐已停止</span>
      </div>
      <h2 id="emergency-result-title">{STATUS_COPY.EMERGENCY.headline}</h2>
      <p className="care-result__lede">
        请不要继续等待在线推荐。如果情况紧急、持续加重，或有人意识、呼吸异常，请立即拨打 120。
      </p>
      <div className="care-result__actions care-result__actions--emergency">
        <a className="button button--danger button--large" href="tel:120">
          <span>拨打 120</span>
          <span className="button__icon"><PhoneCall size={18} aria-hidden="true" /></span>
        </a>
        <Button
          variant="secondary"
          className="button--large"
          onClick={() => onNavigate(`/map?${hospitalContextQuery(null, "EMERGENCY")}`)}
          icon={<MapPinned size={17} aria-hidden="true" />}
        >
          查看附近急诊资源
        </Button>
      </div>
      {tags.length > 0 ? (
        <div className="care-result__signals">
          <span className="eyebrow eyebrow--muted">识别到的风险信号</span>
          <ul>{tags.map((tag) => <li key={tag}>{tag}</li>)}</ul>
        </div>
      ) : null}
      {reasons.length > 0 ? <p className="care-result__reason">{reasons.join(" ")}</p> : null}
      <p className="care-result__emergency-notice">
        目录存在急诊字段 ≠ 当前可以接诊。真实急救以 120 调度为准。
      </p>
      <p className="care-result__disclaimer">系统只提供辅助分流信息，不替代急救指令、医生诊断或处方。</p>
    </article>
  );
}

function CareResult({ result, onNavigate, pathUpdated, previousTags, previousDepts, previousDept }: TriageResultsProps) {
  const status = result.triage_status;
  const copy = STATUS_COPY[status];
  const insufficient = status === "INSUFFICIENT_INFORMATION";
  const urgent = status === "URGENT";
  const steps = careSteps(status);
  const contextDirection = result.matched_department ?? null;
  const reasons = (result.triage?.reasons ?? []).filter(Boolean).slice(0, 2);
  const missing = (result.triage?.followup?.missing_slots ?? []).filter(Boolean).slice(0, 3);
  const modelNotice = result.disease_prediction?.notice && result.disease_prediction.abstain_reason !== "safety_gate_priority"
    ? result.disease_prediction.notice : null;
  const deptCandidates = Array.isArray(result.htriage_analysis?.department_candidates)
    ? result.htriage_analysis.department_candidates.filter((item) => item && typeof item.department === "string").slice(0, 3)
    : [];
  const previousDeptSet = new Set(previousDepts ?? []);
  const deptChanged = Boolean(pathUpdated && previousDept && contextDirection && previousDept !== contextDirection);
  const populationEntry = deptCandidates.some((item) => item.source === "population_context");
  const symptomTags = (result.triage?.symptom_tags ?? []).map((tag) => tag.tag).filter(Boolean);

  return (
    <>
      <article
        className={`care-result care-result--${insufficient ? "insufficient" : urgent ? "urgent" : "routine"} care-result--enhanced`}
        aria-labelledby="care-result-title"
        data-testid="care-result"
        data-triage-status={status}
      >
        <SafetyGateVisual
          status={status}
          redFlags={(result.triage?.red_flag_tags ?? []).filter(Boolean)}
        />

        <div className="care-result__rail" aria-hidden="true" />

        {pathUpdated ? (
          <p className="care-result__updated" data-testid="path-updated" role="status">
            <Check size={14} aria-hidden="true" /> 信息补充后，路径已更新
          </p>
        ) : null}

        <h2 id="care-result-title" className="care-result__headline">{copy.headline}</h2>
        <p className="care-result__lede">
          {insufficient
            ? "暂不强行给出科室方向。先补充关键信息，系统会重新整理一次。"
            : urgent
              ? "请尽快安排专业医疗评估；如果症状加重或出现新的危险信号，请优先急诊。"
              : "可以按下面的方向先去了解科室与常州资源；最终判断以医生面诊为准。"}
        </p>

        {contextDirection ? (
          <div className="care-result__direction">
            <span className="care-result__direction-label">
              <Stethoscope size={15} aria-hidden="true" /> {insufficient ? "当前一般性方向" : "建议先了解"}
            </span>
            <strong>{contextDirection}</strong>
            {deptChanged ? <small data-testid="evidence-diff">补充后更新：{previousDept} → {contextDirection}</small> : null}
            {insufficient ? <small>信息不足时方向会偏保守，补充后可进一步收窄。</small> : null}
          </div>
        ) : null}

        {!insufficient && deptCandidates.filter((item) => item.department !== contextDirection).length > 0 ? (
          <DepartmentMatchVisual
            candidates={deptCandidates
              .filter((item) => item.department !== contextDirection)
              .map((item) => ({
                name: item.department,
                score: (item.score ?? 0) * 100,
                reasoning: [],
              }))}
            symptomTags={symptomTags}
            title="其他可选方向"
            highlightPrimary={false}
          />
        ) : null}

        {reasons.length > 0 ? (
          <p className="care-result__why" data-testid="result-why">
            <span className="eyebrow eyebrow--muted">为什么这样判断</span>
            {reasons.join(" ")}
          </p>
        ) : null}

        <details className="care-result__evidence" data-testid="result-dept-evidence">
          <summary>科室依据 <small>未经临床校准</small></summary>
          <ul>
            {contextDirection ? <li>当前方向：{contextDirection}</li> : <li>当前没有确定的科室方向。</li>}
            {symptomTags.length > 0 ? <li>识别到的症状词：{symptomTags.slice(0, 6).join("、")}</li> : null}
            {deptCandidates.length > 0 ? (
              <li>
                候选方向：
                {deptCandidates.map((item, index) => (
                  <span key={item.department}>
                    {index > 0 ? "、" : ""}
                    {item.department}
                    {previousDeptSet.has(item.department) ? "" : pathUpdated ? "（本轮新增）" : ""}
                  </span>
                ))}
              </li>
            ) : null}
            {populationEntry ? <li>人口词仅作为人群入口（population_context），不作为疾病概率或确诊依据。</li> : null}
            <li>科室候选分只是相对排序，未经临床校准，也不是患病概率。</li>
          </ul>
        </details>

        {modelNotice ? <p className="care-result__reason" data-testid={result.disease_prediction?.abstained ? "model-abstention-notice" : "model-scope-notice"}>
          {modelNotice} <small>此说明仅针对辅助疾病分析，不能用于判断就医是否安全。</small>
        </p> : null}

        <ol className="care-result__steps" aria-label="就医路径进度">
          {steps.map((step, index) => (
            <li key={step.label} className={step.done ? "is-complete" : "is-current"}>
              <span className="care-result__steps-icon" aria-hidden="true">
                {step.done ? <Check size={12} strokeWidth={2.4} /> : <span className="care-result__steps-dot" />}
              </span>
              <span className="care-result__steps-copy">
                <strong>{step.label}</strong>
                <small>{step.detail}</small>
              </span>
              {index < steps.length - 1 ? <i className="care-result__steps-rail" aria-hidden="true" /> : null}
            </li>
          ))}
        </ol>
      </article>
    </>
  );
}

/**
 * Next-step checklist shown in the context rail: it always names the single
 * action that moves the care path forward and keeps the resource trigger visible.
 */
export function CareActions({
  direction,
  safety,
  recommendationsReady,
  recommendationsLoading,
  recommendationsError,
  onOpenPreferences,
  onLoadRecommendations,
  onNavigate,
}: CareActionsProps) {
  const routingDeferred = safety === "INSUFFICIENT_INFORMATION" && !direction;
  return (
    <section className="care-actions" aria-labelledby="care-actions-title">
      <div className="care-actions__heading">
        <h3 id="care-actions-title">下一步</h3>
        <span>{routingDeferred ? "待补充与复核" : recommendationsReady ? "资源路径已就绪" : recommendationsLoading ? "正在匹配常州资源…" : "按顺序完成即可"}</span>
      </div>
      <ul className="care-actions__list">
        <li className={recommendationsReady ? "is-done" : "is-current"}>
          <MapPinned size={16} aria-hidden="true" />
          <div>
            <strong>{routingDeferred ? "先确认危险信号" : recommendationsReady ? "已匹配医院与医生" : "匹配常州医院与医生"}</strong>
            <span>
              {routingDeferred
                ? "请先补充信息并结合专业复核，再整理就医方向。"
                : recommendationsReady
                ? "资源路径来自公开资料；可直接打开导航。"
                : recommendationsLoading
                  ? "正在按安全状态与科室方向读取公开资源。"
                  : "点击后读取公开资源，页面会保留来源与推荐依据。"}
            </span>
          </div>
        </li>
      </ul>
      <div className="care-actions__buttons">
        <Button
          variant={routingDeferred || recommendationsReady ? "secondary" : "primary"}
          onClick={
            routingDeferred
              ? () => onNavigate(`/resources?${hospitalContextQuery(direction, safety)}`)
              : recommendationsReady
              ? () => onNavigate(`/resources?${hospitalContextQuery(direction, safety)}`)
              : onLoadRecommendations
          }
          disabled={recommendationsLoading}
          icon={<ArrowRight size={16} aria-hidden="true" />}
        >
          {routingDeferred ? "浏览医疗资源目录" : "查看当前资源路径"}
        </Button>
        {!routingDeferred ? <Button variant="ghost" onClick={onOpenPreferences} icon={<SlidersHorizontal size={15} aria-hidden="true" />}>
          调整到院偏好
        </Button> : null}
      </div>
      {recommendationsError ? (
        <p className="care-actions__error" role="alert">
          <CircleAlert size={15} aria-hidden="true" /> {recommendationsError}
          <button type="button" onClick={onLoadRecommendations}>重试</button>
        </p>
      ) : null}
    </section>
  );
}

export function TriageResults(props: TriageResultsProps) {
  if (props.result.triage_status === "EMERGENCY") {
    return <EmergencyResult result={props.result} onNavigate={props.onNavigate} />;
  }
  return <CareResult {...props} />;
}
