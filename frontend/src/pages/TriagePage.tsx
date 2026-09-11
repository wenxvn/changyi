import { FormEvent, useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, CircleAlert, LoaderCircle, ShieldCheck } from "lucide-react";
import { ApiError } from "../api/client";
import { getFollowups, startTriage } from "../api/triage";
import { getRecommendations } from "../api/recommendations";
import { Button } from "../components/ui/Button";
import { StatusPill } from "../components/ui/StatusPill";
import { CurrentUnderstanding } from "../components/medical/CurrentUnderstanding";
import { FollowupPrompt } from "../components/medical/FollowupPrompt";
import { TriageResults } from "../components/medical/TriageResults";
import { recordAnalysis } from "../state/demoProfile";
import type {
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

function appendAnswer(condition: string, question: FollowupQuestion, answer: string): string {
  const supplement = `\n补充信息：${question.question}\n${answer}`;
  return `${condition.slice(0, Math.max(0, 2000 - supplement.length))}${supplement}`;
}

export function TriagePage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const initialCondition = new URLSearchParams(window.location.search).get("condition") ?? "";
  const [condition, setCondition] = useState(initialCondition);
  const [submittedCondition, setSubmittedCondition] = useState("");
  const [result, setResult] = useState<TriagePayload | null>(null);
  const [followup, setFollowup] = useState<FollowupPayload | null>(null);
  const [followupStep, setFollowupStep] = useState(1);
  const [recommendations, setRecommendations] = useState<RecommendationPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [recommendationsError, setRecommendationsError] = useState<ApiError | null>(null);
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

  async function submitCondition(value: string, options: { preserveFollowupStep?: boolean } = {}) {
    const nextCondition = value.trim();
    if (!nextCondition || loading) return;
    triageController.current?.abort();
    recommendationController.current?.abort();
    const controller = new AbortController();
    triageController.current = controller;
    setLoading(true);
    setError(null);
    setRecommendationsError(null);
    setRecommendations(null);
    setFollowup(null);
    if (!options.preserveFollowupStep) setFollowupStep(1);
    try {
      const nextResult = await startTriage({ condition: nextCondition, scenario: "common" }, controller.signal);
      if (controller.signal.aborted) return;
      setCondition(nextCondition);
      setSubmittedCondition(nextCondition);
      setResult(nextResult);
      const nextFollowup = followupFrom(nextResult);
      setFollowup(nextFollowup);
      if (!nextFollowup) recordAnalysis(nextResult);

      if (nextFollowup) {
        // The v1 triage response already contains a safe follow-up fallback. The
        // dedicated endpoint is queried to keep the UI on the published follow-up contract.
        try {
          const followupResponse = await getFollowups(
            { condition: nextCondition, scenario: "common" },
            controller.signal,
          );
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
        { condition: submittedCondition, scenario: "common" },
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

  function handleAnswer(question: FollowupQuestion, answer: string) {
    if (loading) return;
    const enrichedCondition = appendAnswer(submittedCondition, question, answer);
    setFollowupStep((value) => value + 1);
    void submitCondition(enrichedCondition, { preserveFollowupStep: true });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitCondition(condition);
  }

  const canShowResults = Boolean(result && result.triage_status !== "EMERGENCY");

  return (
    <section className="triage-page page-container">
      <button className="back-link" type="button" onClick={() => onNavigate("/")}>
        <ArrowLeft size={15} aria-hidden="true" /> 返回首页
      </button>
      <div className="triage-page__layout">
        <div className="triage-page__intro">
          <div className="hero__eyebrow"><span className="eyebrow">智能就医 · WORKSPACE</span><StatusPill><ShieldCheck size={14} aria-hidden="true" /> 后端安全门</StatusPill></div>
          <h1>先说说，<br /><em>现在有什么不舒服？</em></h1>
          <p>用自己的话描述即可。常医智导会先把你的描述交给安全门，再决定是否需要更多信息和资源路径。</p>
          <div className="triage-page__note"><ShieldCheck size={16} aria-hidden="true" /><span>这里的结果是辅助信息，不替代医生诊断。</span></div>
        </div>

        <div className="triage-workspace">
          <form className="symptom-composer symptom-composer--large" onSubmit={handleSubmit}>
            <label htmlFor="triage-condition" className="symptom-composer__label">你的描述</label>
            <textarea
              id="triage-condition"
              value={condition}
              onChange={(event) => setCondition(event.target.value)}
              placeholder="例如：最近总是头晕，大概有几天了。"
              rows={7}
              maxLength={2000}
              disabled={loading}
            />
            <div className="symptom-composer__footer">
              <span className="character-count">{condition.length} / 2000</span>
              <Button type="submit" disabled={!condition.trim() || loading} icon={loading ? <LoaderCircle className="spin" size={17} aria-hidden="true" /> : <ArrowRight size={17} aria-hidden="true" />}>
                {loading ? "正在分析" : "交给安全门"}
              </Button>
            </div>
          </form>

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
              <CurrentUnderstanding condition={submittedCondition} result={result} followup={followup} />
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
            <div className="triage-empty"><div className="triage-empty__line" /><span>安全门会在这里呈现后端返回的状态</span></div>
          )}
        </div>
      </div>
    </section>
  );
}
