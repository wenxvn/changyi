import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, CircleAlert, LoaderCircle, ShieldCheck } from "lucide-react";
import { ApiError } from "../api/client";
import { getFollowups, startTriage } from "../api/triage";
import type { ExpertPreference, VisitIntent, RoutingPreferences } from "../api/recommendations";
import { useFavoriteDoctors } from "../state/favoriteDoctors";
import { StatusPill } from "../components/ui/StatusPill";
import { CurrentUnderstanding } from "../components/medical/CurrentUnderstanding";
import { FollowupPrompt } from "../components/medical/FollowupPrompt";
import { ProgressiveStatus, type ProgressiveStage } from "../components/medical/ProgressiveStatus";
import { EmergencyFacilities } from "../components/medical/EmergencyFacilities";
import { ResourcePreview } from "../components/medical/ResourcePreview";
import { CareActions, TriageResults } from "../components/medical/TriageResults";
import { ExampleSymptomChips, type ExampleSymptom } from "../components/medical/ExampleSymptomChips";
import { SymptomComposer } from "../components/medical/SymptomComposer";
import { CareAgent } from "../components/agent/CareAgent";
import type { AgentStage } from "../components/agent/types";
import { LocationSelector } from "../components/ui/LocationSelector";
import { useRecommendations } from "../hooks/useRecommendations";
import { recordAnalysis } from "../state/demoProfile";
import { useLocationContext } from "../state/locationContext";
import type {
  FollowupAnswer,
  FollowupPayload,
  FollowupQuestion,
  TriagePayload,
} from "../types/api";

function errorFor(reason: unknown, fallback: string): ApiError {
  return reason instanceof ApiError ? reason : new ApiError("NETWORK_ERROR", fallback);
}

/** Ordinary resource matching only runs for a non-emergency result with a condition. */
function hasActionableResult(result: TriagePayload | null, submittedCondition: string): boolean {
  if (!result || result.triage_status === "EMERGENCY") return false;
  if (result.triage_status === "INSUFFICIENT_INFORMATION" && !result.matched_department) return false;
  return Boolean(submittedCondition.trim());
}

function followupFrom(result: TriagePayload): FollowupPayload | null {
  if (result.triage_status === "EMERGENCY") return null;
  const followup = result.triage?.followup;
  return followup?.needed ? followup : null;
}

const STEP_LABELS = ["描述症状", "补充信息", "安全方向", "资源路径"] as const;

function stepIndexFor(hasResult: boolean, hasFollowup: boolean, hasRecommendations: boolean): number {
  if (!hasResult) return 0;
  if (hasFollowup) return 1;
  if (!hasRecommendations) return 2;
  return 3;
}

export function TriagePage({
  onNavigate,
  initialSubmission,
}: {
  onNavigate: (path: string) => void;
  initialSubmission: { id: number; condition: string } | null;
}) {
  const [condition, setCondition] = useState(initialSubmission?.condition ?? "");
  const [agentStage, setAgentStage] = useState<AgentStage>(initialSubmission ? "submitting" : "idle");
  const [submittedCondition, setSubmittedCondition] = useState("");
  const [editingCondition, setEditingCondition] = useState(false);
  const [result, setResult] = useState<TriagePayload | null>(null);
  const [followup, setFollowup] = useState<FollowupPayload | null>(null);
  const [followupStep, setFollowupStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [followupAnswers, setFollowupAnswers] = useState<FollowupAnswer[]>([]);
  const [pathUpdated, setPathUpdated] = useState(false);
  const [previousTags, setPreviousTags] = useState<string[]>([]);
  const [previousDepts, setPreviousDepts] = useState<string[]>([]);
  const [previousDept, setPreviousDept] = useState<string | null>(null);
  const [expertPreference, setExpertPreference] = useState<ExpertPreference>("system");
  const [visitIntent, setVisitIntent] = useState<VisitIntent | "">("");
  const [preferencesOpen, setPreferencesOpen] = useState(false);
  const [routingPreferences, setRoutingPreferences] = useState<RoutingPreferences>({
    district_preference: "any_district",
    distance_preference: "distance_flexible",
    continuity_preference: false,
  });
  const { favoriteDoctorIds } = useFavoriteDoctors();
  const { location } = useLocationContext();
  const triageController = useRef<AbortController | null>(null);
  const requestPending = useRef(false);
  const requestSequence = useRef(0);
  const activeRequestId = useRef(0);
  const initialEntryStarted = useRef<number | null>(null);
  const lifecycleLease = useRef(0);
  const preferencesRef = useRef<HTMLDetailsElement | null>(null);

  useEffect(() => {
    const lease = ++lifecycleLease.current;
    return () => {
      queueMicrotask(() => {
        if (lifecycleLease.current === lease) triageController.current?.abort();
      });
    };
  }, []);

  useEffect(() => {
    if (!initialSubmission?.condition.trim()) return;
    let active = true;
    const { id, condition: initialValue } = initialSubmission;
    // Deferring only the dispatch to a microtask lets StrictMode's effect replay
    // discard its first setup without firing a duplicate network request.
    queueMicrotask(() => {
      if (!active || initialEntryStarted.current === id) return;
      initialEntryStarted.current = id;
      void submitCondition(initialValue);
    });
    return () => { active = false; };
  }, [initialSubmission?.id]);

  // Emergency short-circuit: ordinary resource recommendations are never requested
  // or rendered for an emergency result.
  const recommendationsEnabled = hasActionableResult(result, submittedCondition);
  const recommendationInput = {
    condition: submittedCondition,
    // Follow-up answers travel as structured question_id/value pairs; the original
    // condition is never rewritten by follow-up text.
    followup_answers: followupAnswers,
    expertPreference,
    visitIntent,
    routingPreferences,
    favoriteDoctorIds,
    location: {
      source: location.source,
      district: location.source === "district" ? location.district : null,
      lat: location.source === "geolocation" ? location.lat : null,
      lng: location.source === "geolocation" ? location.lng : null,
    },
  };
  const recommendations = useRecommendations(
    recommendationsEnabled,
    Boolean(followup?.needed),
    recommendationInput,
  );

  async function submitCondition(
    value: string,
    options: { preserveFollowupStep?: boolean; followupAnswers?: FollowupAnswer[] } = {},
  ) {
    const nextCondition = value.trim();
    if (!nextCondition || requestPending.current) return;
    const nextAnswers = options.followupAnswers ?? [];
    // Snapshot previous-round evidence for read-only diff highlight only.
    // This never drives triage logic; the server recomputes everything.
    if (nextAnswers.length > 0 && result) {
      setPreviousTags((result.triage?.symptom_tags ?? []).map((item) => item.tag));
      setPreviousDepts(
        Array.isArray(result.htriage_analysis?.department_candidates)
          ? result.htriage_analysis.department_candidates
              .filter((item) => item && typeof item.department === "string")
              .map((item) => (item as { department: string }).department)
          : [],
      );
      setPreviousDept(result.matched_department ?? null);
    } else if (nextAnswers.length === 0) {
      setPreviousTags([]);
      setPreviousDepts([]);
      setPreviousDept(null);
    }
    triageController.current?.abort();
    const controller = new AbortController();
    const requestId = ++requestSequence.current;
    activeRequestId.current = requestId;
    requestPending.current = true;
    triageController.current = controller;
    setLoading(true);
    setError(null);
    setFollowup(null);
    setFollowupAnswers(nextAnswers);
    setVisitIntent("");
    setPathUpdated(nextAnswers.length > 0);
    setAgentStage("submitting");
    if (nextAnswers.length === 0) setResult(null);
    if (!options.preserveFollowupStep) setFollowupStep(1);
    let triageSettled = false;
    const waitingFrame = window.requestAnimationFrame(() => {
      if (!triageSettled && !controller.signal.aborted && activeRequestId.current === requestId) {
        setAgentStage("waiting");
      }
    });
    try {
      const request = {
        condition: nextCondition,
        scenario: "common" as const,
        ...locationRequest(),
        followup_answers: nextAnswers,
      };
      const nextResult = await startTriage(request, controller.signal);
      triageSettled = true;
      window.cancelAnimationFrame(waitingFrame);
      if (controller.signal.aborted || activeRequestId.current !== requestId) return;
      setCondition(nextCondition);
      setSubmittedCondition(nextCondition);
      setResult(nextResult);
      setEditingCondition(false);
      const nextFollowup = followupFrom(nextResult);
      setFollowup(nextFollowup);
      setAgentStage(nextResult.triage_status === "EMERGENCY"
        ? "emergency"
        : nextFollowup ? "needs_followup" : "result_ready");
      if (!nextFollowup) recordAnalysis(nextResult);

      if (nextFollowup) {
        try {
          const followupResponse = await getFollowups(request, controller.signal);
          if (!controller.signal.aborted && activeRequestId.current === requestId) {
            setFollowup(followupResponse.followup);
            if (!followupResponse.followup.needed) setAgentStage("result_ready");
          }
        } catch {
          // Keep the follow-up embedded in the successful triage response.
        }
      }
    } catch (reason) {
      triageSettled = true;
      window.cancelAnimationFrame(waitingFrame);
      if (!controller.signal.aborted && activeRequestId.current === requestId) {
        setError(errorFor(reason, "分诊服务暂时无法连接。"));
        setResult(null);
        setAgentStage("error");
      }
    } finally {
      triageSettled = true;
      window.cancelAnimationFrame(waitingFrame);
      if (activeRequestId.current === requestId) {
        requestPending.current = false;
        if (!controller.signal.aborted) setLoading(false);
      }
    }
  }

  function locationRequest() {
    return {
      ...(location.source === "district" && location.district ? { district: location.district } : {}),
      ...(location.source === "geolocation" && location.lat !== null && location.lng !== null
        ? { lat: location.lat, lng: location.lng }
        : {}),
      location_source: location.source,
    } as const;
  }

  function handleAnswer(_question: FollowupQuestion, answer: FollowupAnswer) {
    if (loading) return;
    const previousAnswer = followupAnswers.find((item) => item.question_id === answer.question_id);
    const nextAnswers = [...followupAnswers.filter((item) => item.question_id !== answer.question_id), answer];
    const unresolvedRisk = answer.question_id === "red_flag_check" && answer.value === "unknown";
    if (!unresolvedRisk && (!previousAnswer || previousAnswer.value === "unknown")) {
      setFollowupStep((value) => value + 1);
    }
    void submitCondition(submittedCondition, { preserveFollowupStep: true, followupAnswers: nextAnswers });
  }

  function handleSkipFollowup() {
    setFollowup(null);
    setAgentStage("result_ready");
    if (result) recordAnalysis(result);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitCondition(condition);
  }

  function handleExample(example: ExampleSymptom) {
    setCondition(example.condition);
    void submitCondition(example.condition);
  }

  function openPreferences() {
    setPreferencesOpen(true);
    window.requestAnimationFrame(() => {
      const panel = preferencesRef.current;
      if (!panel) return;
      panel.open = true;
      panel.scrollIntoView({
        block: "center",
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
      });
      panel.querySelector("summary")?.focus({ preventScroll: true });
    });
  }

  const hasAnalysis = Boolean(result);
  const isEmergency = result?.triage_status === "EMERGENCY";
  const hasFollowup = Boolean(followup?.needed);
  const recommendationsReady = Boolean(recommendations.data);
  const activeStep = stepIndexFor(hasAnalysis, hasFollowup, recommendationsReady);

  const analysisStages = useMemo<ProgressiveStage[]>(() => {
    // Stages map the real algorithm chain. Status is request/result-driven,
    // not a decorative timer.
    if (loading) {
      return [
        { id: "request", label: "等待系统响应", status: "active", hint: followupAnswers.length > 0
          ? "补充信息已随请求发送；这里不展示实时分析进度。"
          : "请求已发送；这里不展示实时分析进度。" },
      ];
    }
    if (!result) {
      return [
        { id: "read", label: "读取症状描述", status: "pending" },
        { id: "safety", label: "Safety Gate", status: "pending" },
        { id: "direction", label: "就医方向路由", status: "pending" },
        { id: "inquiry", label: "自适应追问", status: "pending" },
        { id: "resources", label: "多目标资源路由", status: "pending" },
      ];
    }
    if (result.triage_status === "EMERGENCY") {
      return [
        { id: "read", label: "已读取描述", status: "done" },
        { id: "safety", label: "Safety Gate 完成", status: "done", hint: "高风险优先处理" },
        { id: "emergency", label: "急诊出口", status: "active", hint: "不再推荐普通就医路径" },
      ];
    }
    if (result.triage_status === "INSUFFICIENT_INFORMATION" || followup?.needed) {
      return [
        { id: "read", label: "已读取描述", status: "done" },
        { id: "safety", label: "Safety Gate 完成", status: "done" },
        {
          id: "abstain",
          label: "选择性拒答",
          status: "done",
          hint: "暂不强行给出确定科室方向",
        },
        {
          id: "inquiry",
          label: "自适应追问",
          status: loading ? "active" : "active",
          hint: "补充关键信息后重新计算",
        },
        { id: "resources", label: "多目标资源路由", status: recommendations.loading ? "active" : recommendations.data ? "done" : "pending" },
      ];
    }
    return [
      { id: "read", label: "已读取描述", status: "done" },
      { id: "safety", label: "Safety Gate 完成", status: "done", hint: result.triage_status === "URGENT" ? "建议尽快评估" : "未提示立即急诊" },
      {
        id: "direction",
        label: "就医方向路由",
        status: result.matched_department ? "done" : "active",
        hint: result.matched_department || "整理科室方向",
      },
      {
        id: "inquiry",
        label: "自适应追问",
        status: "done",
        hint: followupAnswers.length > 0 ? "已补充信息并重算" : "本轮无需追问",
      },
      {
        id: "resources",
        label: "多目标资源路由",
        status: recommendations.loading ? "active" : recommendations.data ? "done" : "pending",
        hint: recommendations.loading ? "正在匹配医院与医生" : undefined,
      },
    ];
  }, [loading, result, followup?.needed, recommendations.loading, recommendations.data, followupAnswers.length]);

  return (
    <section className="triage-page page-container">
      <div className="triage-page__topline">
        <button className="back-link" type="button" onClick={() => onNavigate("/")}>
          <ArrowLeft size={15} aria-hidden="true" /> 返回首页
        </button>
        {hasAnalysis ? (
          <ol className="triage-steps" aria-label="分诊进度">
            {STEP_LABELS.map((label, index) => (
              <li
                key={label}
                className={[
                  index < activeStep ? "is-complete" : "",
                  index === activeStep ? "is-active" : "",
                  index === activeStep + 1 ? "is-next" : "",
                ].filter(Boolean).join(" ")}
                aria-current={index === activeStep ? "step" : undefined}
              >
                <span className="triage-steps__index">{index < activeStep ? "✓" : index + 1}</span>
                <span>{label}</span>
              </li>
            ))}
          </ol>
        ) : null}
      </div>

      {!hasAnalysis ? (
        <>
          <div className="triage-page__intro">
            <div className="hero__eyebrow">
              <span className="eyebrow">智能就医 · 从描述开始</span>
              <StatusPill><ShieldCheck size={14} aria-hidden="true" /> 先看安全信号</StatusPill>
            </div>
            <h1>现在有什么不舒服？</h1>
            <p>用自己的话说说即可。系统返回后，再查看安全状态和适合的下一步。</p>
          </div>
          <div className="triage-entry-grid" id="triage-workspace">
            <div className="triage-workspace">
              <SymptomComposer
                id="triage-condition"
                value={condition}
                onChange={setCondition}
                onSubmit={handleSubmit}
                label="你的描述"
                submitLabel="查看安全状态"
                busyLabel="正在等待系统响应"
                loading={loading}
                rows={4}
                variant="workspace"
                onFocusChange={(focused) => {
                  if (!loading && !hasAnalysis) setAgentStage(focused ? "composing" : "idle");
                }}
              />
              <ExampleSymptomChips onSelect={handleExample} disabled={loading} />
            {loading ? (
              <div className="triage-progress-panel is-loading" role="status" data-testid="triage-waiting">
                <LoaderCircle className="spin" size={17} aria-hidden="true" /> 请求已发出，正在等待系统响应。
              </div>
            ) : (
              <div className="triage-empty">
                <div className="triage-empty__line" />
                <strong>提交后会在这里呈现安全状态和下一步</strong>
                <span>如信息不足，系统会先询问补充内容，不强行给出科室方向。</span>
              </div>
            )}
            {error ? (
              <div className="inline-error" role="alert">
                <CircleAlert size={18} aria-hidden="true" />
                <div>
                  <strong>{error.code === "MODEL_UNAVAILABLE" ? "部分智能分析暂时不可用" : "暂时还无法完成这一步"}</strong>
                  <p>{error.message} 你仍可以继续浏览医疗资源。</p>
                </div>
                <button type="button" onClick={() => void submitCondition(condition)}>重试</button>
              </div>
            ) : null}
            </div>
            <aside className="triage-entry-aside" aria-label="助手状态与使用说明">
              <CareAgent stage={agentStage} />
              <div className="triage-page__note">
                <ShieldCheck size={16} aria-hidden="true" />
                <span>结果仅供就医方向参考，不替代医生诊断；急症信息会优先显示安全行动。</span>
              </div>
              <details className="triage-entry-details">
                <summary>这项辅助服务会提供什么？</summary>
                <ul className="triage-page__outcomes">
                  <li><strong>安全状态</strong><span>是否需要优先急诊或尽快评估</span></li>
                  <li><strong>就医方向</strong><span>有依据时展示建议了解的科室方向</span></li>
                  <li><strong>资源路径</strong><span>常州医院、公开医生资料与导航入口</span></li>
                </ul>
              </details>
              <div className="triage-controls-panel triage-controls-panel--idle">
                <LocationSelector />
              </div>
            </aside>
          </div>
        </>
      ) : (
        <>
          {!isEmergency ? (
            <>
              <div className="triage-submitted-summary">
                <div>
                  <span className="eyebrow eyebrow--muted">你的描述</span>
                  <p>“{submittedCondition}”</p>
                </div>
                <button type="button" onClick={() => setEditingCondition(true)} disabled={loading}>修改</button>
              </div>
              <div className="triage-agent-result">
                <CareAgent stage={agentStage} compact />
              </div>
            </>
          ) : null}

          {editingCondition && !isEmergency ? (
            <SymptomComposer
              id="triage-condition"
              value={condition}
              onChange={setCondition}
              onSubmit={handleSubmit}
              label="你的描述"
              submitLabel="重新分析"
              busyLabel="正在等待系统响应"
              loading={loading}
              rows={3}
              variant="workspace"
              onFocusChange={(focused) => {
                if (!loading) setAgentStage(focused ? "composing" : result ? "result_ready" : "idle");
              }}
            />
          ) : null}

          {!isEmergency ? (
            <div className="triage-progress-panel" data-testid="algorithm-stages">
              <ProgressiveStatus stages={analysisStages} label="已返回的分诊与路径状态" />
            </div>
          ) : null}

          {error ? (
            <div className="inline-error" role="alert">
              <CircleAlert size={18} aria-hidden="true" />
              <div>
                <strong>{error.code === "MODEL_UNAVAILABLE" ? "部分智能分析暂时不可用" : "暂时还无法完成这一步"}</strong>
                <p>{error.message} 你仍可以继续浏览医疗资源。</p>
              </div>
              <button type="button" onClick={() => void submitCondition(condition)}>重试</button>
            </div>
          ) : null}

          <div className={`triage-care${isEmergency ? " triage-care--emergency" : ""}`}>
            <div className="triage-care__main">
              <div className="triage-page__results">
                <TriageResults
                  result={result as TriagePayload}
                  onNavigate={onNavigate}
                  pathUpdated={pathUpdated}
                  previousTags={previousTags}
                  previousDepts={previousDepts}
                  previousDept={previousDept}
                />
              </div>

              {!isEmergency ? (
                <>
                  {hasFollowup ? (
                    <FollowupPrompt
                      followup={followup as FollowupPayload}
                      stepNumber={followupStep}
                      disabled={loading}
                      directionDeferred={result?.triage_status === "INSUFFICIENT_INFORMATION" && !result.matched_department}
                      onAnswer={handleAnswer}
                      onSkip={handleSkipFollowup}
                    />
                  ) : null}

                  <section className="path-panel" aria-labelledby="path-panel-title">
                    <div className="path-panel__heading">
                      <h3 id="path-panel-title">{recommendationsReady ? "常州资源路径" : "资源路径"}</h3>
                      <span>
                        {recommendations.loading
                          ? "正在读取医院与医生"
                          : recommendationsReady
                            ? "公开资料 · 可按需打开导航"
                            : "等待匹配"}
                      </span>
                    </div>
                    {recommendations.loading ? (
                      <div className="path-panel__state" aria-live="polite">
                        <LoaderCircle className="spin" size={17} aria-hidden="true" /> 正在匹配常州医院与公开医生资料…
                      </div>
                    ) : null}
                    {!recommendations.loading && recommendations.error ? (
                      <div className="path-panel__state path-panel__state--error" role="alert">
                        <CircleAlert size={17} aria-hidden="true" />
                        <span>{recommendations.error.message}</span>
                        <button type="button" onClick={recommendations.reload}>重试</button>
                      </div>
                    ) : null}
                    {recommendationsReady && recommendations.data ? (
                      <ResourcePreview
                        recommendations={recommendations.data}
                        direction={result?.matched_department ?? null}
                        safety={result?.triage_status ?? null}
                        onNavigate={onNavigate}
                      />
                    ) : null}
                    {!recommendations.loading && !recommendations.error && !recommendationsReady ? (
                      <div className="path-panel__state">
                        <span>
                          {hasFollowup
                            ? "补充信息后会自动匹配资源；也可以先跳过追问查看当前方向。"
                            : "点击「查看当前资源路径」读取公开资源。"}
                        </span>
                      </div>
                    ) : null}
                  </section>
                </>
              ) : null}
            </div>

            <aside className="triage-care__aside" aria-label="当前上下文">
              {isEmergency ? <EmergencyFacilities onNavigate={onNavigate} /> : null}
              {!isEmergency ? (
                <>
                  <CurrentUnderstanding
                    condition={submittedCondition}
                    result={result as TriagePayload}
                    previousTags={previousTags}
                    pathUpdated={pathUpdated}
                  />
                  <CareActions
                    direction={result?.matched_department ?? null}
                    safety={result?.triage_status ?? "ROUTINE"}
                    recommendationsReady={recommendationsReady}
                    recommendationsLoading={recommendations.loading}
                    recommendationsError={recommendations.error?.message ?? null}
                    onOpenPreferences={openPreferences}
                    onLoadRecommendations={recommendations.reload}
                    onNavigate={onNavigate}
                  />
                </>
              ) : null}
              <div id="care-location">
                <LocationSelector />
              </div>
              {!isEmergency ? (
                <details className="triage-prefs" ref={preferencesRef} open={preferencesOpen} onToggle={(event) => setPreferencesOpen(event.currentTarget.open)}>
                  <summary id="care-preferences">
                    <span>资源偏好</span>
                    <small>只影响匹配，不改变安全分诊</small>
                  </summary>
                  <div className="triage-prefs__body">
                    <p className="triage-prefs__explain">
                      修改偏好会重新请求资源排序；医院/医生顺序会真实变化，解释只使用接口已返回的依据。
                    </p>
                    <fieldset className="expert-preference visit-intent">
                      <legend>这次主要想解决什么？</legend>
                      <p className="expert-preference__note">只影响就医资源匹配，不改变安全分诊结果；急症仍优先急诊/急救。</p>
                      {([
                        ["", "先按系统判断"],
                        ["first_visit", "首次就诊"],
                        ["follow_up", "已有诊断，需要复诊"],
                        ["review_results", "已有检查，希望进一步就医"],
                        ["procedure_consult", "手术 / 专科治疗咨询"],
                        ["unsure", "不确定"],
                      ] as Array<[VisitIntent | "", string]>).map(([value, label]) => (
                        <label key={value || "default"}>
                          <input
                            type="radio"
                            name="visit-intent"
                            value={value}
                            checked={visitIntent === value}
                            onChange={() => setVisitIntent(value)}
                          />
                          {label}
                        </label>
                      ))}
                    </fieldset>
                    <fieldset className="expert-preference routing-preferences">
                      <legend>就医资源偏好</legend>
                      <p className="expert-preference__note">只影响资源匹配，不改变安全分诊；默认关闭。</p>
                      <label>
                        <span className="routing-preferences__label">跨区就医</span>
                        <select
                          value={routingPreferences.district_preference}
                          onChange={(event) => setRoutingPreferences((prev) => ({
                            ...prev,
                            district_preference: event.target.value as RoutingPreferences["district_preference"],
                          }))}
                          data-testid="pref-district"
                        >
                          <option value="prefer_home_district">优先本区</option>
                          <option value="allow_cross_district">可接受跨区</option>
                          <option value="any_district">不限</option>
                        </select>
                      </label>
                      <label>
                        <span className="routing-preferences__label">大致距离</span>
                        <select
                          value={routingPreferences.distance_preference}
                          onChange={(event) => setRoutingPreferences((prev) => ({
                            ...prev,
                            distance_preference: event.target.value as RoutingPreferences["distance_preference"],
                          }))}
                          data-testid="pref-distance"
                        >
                          <option value="prefer_nearby">就近优先</option>
                          <option value="allow_farther_for_fit">可接受更远但资源更匹配</option>
                          <option value="distance_flexible">不特别在意距离</option>
                        </select>
                      </label>
                      <label>
                        <input
                          type="checkbox"
                          checked={Boolean(routingPreferences.continuity_preference)}
                          onChange={(event) => setRoutingPreferences((prev) => ({
                            ...prev,
                            continuity_preference: event.target.checked,
                          }))}
                          data-testid="pref-continuity"
                        />
                        优先考虑之前收藏 / 复诊医生
                      </label>
                    </fieldset>
                    <fieldset className="expert-preference">
                      <legend>医生资源偏好</legend>
                      <p className="expert-preference__note">专家资源不一定适合所有常见病与初诊场景；默认为系统平衡推荐。</p>
                      <label>
                        <input
                          type="radio"
                          name="expert-preference"
                          value="system"
                          checked={expertPreference === "system"}
                          onChange={() => setExpertPreference("system")}
                        />
                        系统平衡推荐
                      </label>
                      <label>
                        <input
                          type="radio"
                          name="expert-preference"
                          value="wish_expert"
                          checked={expertPreference === "wish_expert"}
                          onChange={() => setExpertPreference("wish_expert")}
                        />
                        希望优先专家
                      </label>
                      <label>
                        <input
                          type="radio"
                          name="expert-preference"
                          value="no_expert"
                          checked={expertPreference === "no_expert"}
                          onChange={() => setExpertPreference("no_expert")}
                        />
                        不特别需要专家
                      </label>
                    </fieldset>
                  </div>
                </details>
              ) : null}
            </aside>
          </div>
        </>
      )}
    </section>
  );
}
