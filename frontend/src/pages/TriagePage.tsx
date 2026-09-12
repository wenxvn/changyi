import { FormEvent, useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, CircleAlert, LoaderCircle, ShieldCheck } from "lucide-react";
import { ApiError } from "../api/client";
import { getFollowups, startTriage } from "../api/triage";
import { getRecommendations, type ExpertPreference, type VisitIntent, type RoutingPreferences } from "../api/recommendations";
import { useFavoriteDoctors } from "../state/favoriteDoctors";
import { Button } from "../components/ui/Button";
import { StatusPill } from "../components/ui/StatusPill";
import { CurrentUnderstanding } from "../components/medical/CurrentUnderstanding";
import { FollowupPrompt } from "../components/medical/FollowupPrompt";
import { TriageResults } from "../components/medical/TriageResults";
import { LocationSelector } from "../components/ui/LocationSelector";
import { SpeechInput } from "../components/ui/SpeechInput";
import { recordAnalysis } from "../state/demoProfile";
import { useLocationContext } from "../state/locationContext";
import type {
  FollowupAnswer,
  FollowupPayload,
  FollowupQuestion,
  RecommendationPayload,
  TriagePayload,
} from "../types/api";

function errorFor(reason: unknown, fallback: string): ApiError {
  return reason instanceof ApiError ? reason : new ApiError("NETWORK_ERROR", fallback);
}

function followupFrom(result: TriagePayload): FollowupPayload | null {
  if (result.triage_status === "EMERGENCY") return null;
  const followup = result.triage?.followup;
  return followup?.needed ? followup : null;
}

function stepIndexFor(hasResult: boolean, hasFollowup: boolean, hasRecommendations: boolean): number {
  if (!hasResult) return 0;
  if (hasFollowup) return 1;
  if (!hasRecommendations) return 2;
  return 3;
}

const STEP_LABELS = ["描述症状", "补充信息", "安全方向", "资源路径"] as const;

export function TriagePage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const initialCondition = new URLSearchParams(window.location.search).get("condition") ?? "";
  const [condition, setCondition] = useState(initialCondition);
  const [submittedCondition, setSubmittedCondition] = useState("");
  const [editingCondition, setEditingCondition] = useState(false);
  const [result, setResult] = useState<TriagePayload | null>(null);
  const [followup, setFollowup] = useState<FollowupPayload | null>(null);
  const [followupStep, setFollowupStep] = useState(1);
  const [recommendations, setRecommendations] = useState<RecommendationPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [recommendationsError, setRecommendationsError] = useState<ApiError | null>(null);
  const [followupAnswers, setFollowupAnswers] = useState<FollowupAnswer[]>([]);
  const [expertPreference, setExpertPreference] = useState<ExpertPreference>("system");
  const [visitIntent, setVisitIntent] = useState<VisitIntent | "">("");
  const [routingPreferences, setRoutingPreferences] = useState<RoutingPreferences>({
    district_preference: "any_district",
    distance_preference: "distance_flexible",
    continuity_preference: false,
  });
  const { favoriteDoctorIds } = useFavoriteDoctors();
  const { location } = useLocationContext();
  const triageController = useRef<AbortController | null>(null);
  const recommendationController = useRef<AbortController | null>(null);

  useEffect(() => {
    if (initialCondition.trim()) void submitCondition(initialCondition);
    return () => {
      triageController.current?.abort();
      recommendationController.current?.abort();
    };
    // The initial URL condition is intentionally submitted once when the page opens.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const locationRequest = () => ({
    ...(location.source === "district" && location.district ? { district: location.district } : {}),
    ...(location.source === "geolocation" && location.lat !== null && location.lng !== null
      ? { lat: location.lat, lng: location.lng }
      : {}),
    location_source: location.source,
  } as const);

  useEffect(() => {
    setRecommendations(null);
    setRecommendationsError(null);
    setVisitIntent("");
  }, [location.source, location.district, location.lat, location.lng]);

  useEffect(() => {
    if (!recommendations || recommendationsLoading) return;
    void loadRecommendations();
    // Reload recommendations when the user changes expert preference after results are shown.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expertPreference, visitIntent, routingPreferences, favoriteDoctorIds.join(",")]);

  async function submitCondition(
    value: string,
    options: { preserveFollowupStep?: boolean; followupAnswers?: FollowupAnswer[] } = {},
  ) {
    const nextCondition = value.trim();
    if (!nextCondition || loading) return;
    const nextAnswers = options.followupAnswers ?? [];
    triageController.current?.abort();
    recommendationController.current?.abort();
    const controller = new AbortController();
    triageController.current = controller;
    setLoading(true);
    setError(null);
    setRecommendationsError(null);
    setRecommendations(null);
    setFollowup(null);
    setFollowupAnswers(nextAnswers);
    setVisitIntent("");
    if (!options.preserveFollowupStep) setFollowupStep(1);
    try {
      const request = {
        condition: nextCondition,
        scenario: "common" as const,
        ...locationRequest(),
        followup_answers: nextAnswers,
      };
      const nextResult = await startTriage(request, controller.signal);
      if (controller.signal.aborted) return;
      setCondition(nextCondition);
      setSubmittedCondition(nextCondition);
      setResult(nextResult);
      setEditingCondition(false);
      const nextFollowup = followupFrom(nextResult);
      setFollowup(nextFollowup);
      if (!nextFollowup) recordAnalysis(nextResult);

      if (nextFollowup) {
        try {
          const followupResponse = await getFollowups(request, controller.signal);
          if (!controller.signal.aborted) setFollowup(followupResponse.followup);
        } catch {
          // Keep the follow-up embedded in the successful triage response.
        }
      }
    } catch (reason) {
      if (!controller.signal.aborted) {
        setError(errorFor(reason, "分诊服务暂时无法连接。"));
        setResult(null);
      }
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }

  async function loadRecommendations() {
    if (!result || result.triage_status === "EMERGENCY" || !submittedCondition.trim()) return;
    recommendationController.current?.abort();
    const controller = new AbortController();
    recommendationController.current = controller;
    setRecommendationsLoading(true);
    setRecommendationsError(null);
    try {
      const payload = await getRecommendations(
        {
          condition: submittedCondition,
          scenario: "common",
          ...locationRequest(),
          followup_answers: followupAnswers,
          expert_preference: expertPreference,
          ...(visitIntent ? { visit_intent: visitIntent } : {}),
          routing_preferences: routingPreferences,
          ...(routingPreferences.continuity_preference && favoriteDoctorIds.length
            ? { favorite_doctor_ids: favoriteDoctorIds.slice(0, 50) }
            : {}),
        },
        controller.signal,
      );
      if (!controller.signal.aborted) setRecommendations(payload);
    } catch (reason) {
      if (!controller.signal.aborted) {
        setRecommendationsError(errorFor(reason, "资源推荐暂时无法连接。"));
      }
    } finally {
      if (!controller.signal.aborted) setRecommendationsLoading(false);
    }
  }

  function handleAnswer(_question: FollowupQuestion, answer: FollowupAnswer) {
    if (loading) return;
    const nextAnswers = [...followupAnswers, answer];
    setFollowupStep((value) => value + 1);
    void submitCondition(submittedCondition, { preserveFollowupStep: true, followupAnswers: nextAnswers });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitCondition(condition);
  }

  const canShowResults = Boolean(result && result.triage_status !== "EMERGENCY");
  const hasAnalysis = Boolean(result);
  const activeStep = stepIndexFor(hasAnalysis, Boolean(followup), Boolean(recommendations));

  return (
    <section className="triage-page page-container">
      <button className="back-link" type="button" onClick={() => onNavigate("/")}>
        <ArrowLeft size={15} aria-hidden="true" /> 返回首页
      </button>

      {hasAnalysis ? (
        <ol className="triage-steps" aria-label="分诊进度">
          {STEP_LABELS.map((label, index) => (
            <li key={label} className={index <= activeStep ? "is-active" : index === activeStep + 1 ? "is-next" : ""} aria-current={index === activeStep ? "step" : undefined}>
              <span className="triage-steps__index">{index + 1}</span>
              <span>{label}</span>
            </li>
          ))}
        </ol>
      ) : null}

      <div className={`triage-page__layout${hasAnalysis ? " triage-page__layout--active" : ""}`}>
        {result ? (
          <CurrentUnderstanding
            condition={submittedCondition}
            result={result}
            followup={followup}
            recommendations={recommendations}
            recommendationsLoading={recommendationsLoading}
            onNavigate={onNavigate}
          />
        ) : (
          <div className="triage-page__intro">
            <div className="hero__eyebrow"><span className="eyebrow">智能就医 · 从描述开始</span><StatusPill><ShieldCheck size={14} aria-hidden="true" /> 先看安全信号</StatusPill></div>
            <h1>先说说，<em>现在有什么不舒服？</em></h1>
            <p>用自己的话描述即可。常医智导会先整理安全信号，再决定是否需要更多信息和就医资源。</p>
            <div className="triage-page__note"><ShieldCheck size={16} aria-hidden="true" /><span>这里的结果是辅助信息，不替代医生诊断。急症信号会优先提示急救出口。</span></div>
            <ul className="triage-page__outcomes">
              <li><strong>安全状态</strong><span>是否需要优先急诊或尽快评估</span></li>
              <li><strong>就医方向</strong><span>建议首先了解的科室方向</span></li>
              <li><strong>资源路径</strong><span>常州医院、公开医生与导航入口</span></li>
            </ul>
          </div>
        )}

        <div className="triage-workspace">
          {result && !editingCondition ? (
            <div className="triage-submitted-summary">
              <div><span className="eyebrow eyebrow--muted">你的描述</span><p>“{submittedCondition}”</p></div>
              <button type="button" onClick={() => setEditingCondition(true)} disabled={loading}>修改</button>
            </div>
          ) : (
            <form className="symptom-composer symptom-composer--large" onSubmit={handleSubmit}>
              <label htmlFor="triage-condition" className="symptom-composer__label">你的描述</label>
              <textarea
                id="triage-condition"
                value={condition}
                onChange={(event) => setCondition(event.target.value)}
                placeholder="例如：最近总是头晕，大概有几天了。"
                rows={5}
                maxLength={2000}
                disabled={loading}
              />
              <div className="symptom-composer__footer">
                <div className="symptom-composer__tools">
                  <SpeechInput
                    disabled={loading}
                    onTranscript={(text) => setCondition((value) => (value ? `${value}${value.endsWith("。") ? "" : "。"}${text}` : text))}
                  />
                  <span className="character-count">{condition.length} / 2000</span>
                </div>
                <Button type="submit" disabled={!condition.trim() || loading} icon={loading ? <LoaderCircle className="spin" size={17} aria-hidden="true" /> : <ArrowRight size={17} aria-hidden="true" />}>
                  {loading ? "正在分析" : "查看安全状态"}
                </Button>
              </div>
            </form>
          )}

          <LocationSelector />

          {canShowResults ? (
            <details className="triage-prefs" open={!recommendations && !recommendationsLoading}>
              <summary>
                <span>资源偏好</span>
                <small>只影响匹配，不改变安全分诊</small>
              </summary>
              <div className="triage-prefs__body">
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

          {error ? (
            <div className="inline-error" role="alert">
              <CircleAlert size={18} aria-hidden="true" />
              <div><strong>{error.code === "MODEL_UNAVAILABLE" ? "部分智能分析暂时不可用" : "暂时还无法完成这一步"}</strong><p>{error.message} 你仍可以继续浏览医疗资源。</p></div>
              <button type="button" onClick={() => void submitCondition(condition)}>重试</button>
            </div>
          ) : null}

          {loading && !result ? <div className="triage-loading" aria-live="polite"><LoaderCircle className="spin" size={17} aria-hidden="true" /> 安全门正在读取这段描述…</div> : null}

          {result ? (
            <div className="triage-page__results">
              <FollowupPrompt
                followup={followup ?? { needed: false, confidence: "unknown", missing_slots: [], questions: [] }}
                stepNumber={followupStep}
                disabled={loading}
                onAnswer={handleAnswer}
                onSkip={() => {
                  setFollowup(null);
                  if (result) recordAnalysis(result);
                  void loadRecommendations();
                }}
              />
              <TriageResults
                result={result}
                recommendations={recommendations}
                recommendationsLoading={recommendationsLoading}
                recommendationsError={recommendationsError?.message ?? null}
                onLoadRecommendations={loadRecommendations}
                onNavigate={onNavigate}
              />
              {canShowResults && followup ? <p className="triage-page__followup-note">可以继续补充，也可以跳过追问查看当前方向。系统不会把当前整理当作诊断。</p> : null}
            </div>
          ) : (
            <div className="triage-empty"><div className="triage-empty__line" /><span>提交后会在这里呈现安全状态和下一步</span></div>
          )}
        </div>
      </div>
    </section>
  );
}
