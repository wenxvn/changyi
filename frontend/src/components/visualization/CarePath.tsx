import {
  CircleCheck,
  CircleDot,
  LoaderCircle,
  MapPinned,
  Route,
  ShieldCheck,
  Stethoscope,
} from "lucide-react";

export type CarePathPhase = "idle" | "analysing" | "ready";
export type CarePathTone = "neutral" | "info" | "success" | "warning" | "danger";

/** Algorithm chain stages shown as the product path. Progress is request-driven. */
export type CarePathStageId = "symptom" | "safety" | "direction" | "resources" | "arrival";

export interface CarePathStageState {
  id: CarePathStageId;
  status: "pending" | "active" | "done" | "blocked";
  hint?: string;
}

const pathSteps = [
  { id: "symptom" as const, label: "症状", caption: "用自己的话描述不适", icon: CircleDot, depth: 0 },
  { id: "safety" as const, label: "安全门", caption: "优先识别危险信号", icon: ShieldCheck, depth: 1 },
  { id: "direction" as const, label: "就医方向", caption: "整理科室与下一步", icon: Stethoscope, depth: 2 },
  { id: "resources" as const, label: "资源路径", caption: "医院 · 医生 · 导航", icon: MapPinned, depth: 1 },
  { id: "arrival" as const, label: "到院行动", caption: "带着依据去就医", icon: CircleCheck, depth: 0 },
];

interface CarePathProps {
  phase?: CarePathPhase;
  /** Optional explicit stage states from the real request lifecycle. */
  stages?: CarePathStageState[];
  tone?: CarePathTone;
  statusLabel?: string;
}

const phaseFooter: Record<CarePathPhase, string> = {
  idle: "产品路径示意 · 悬停查看每一步",
  analysing: "正在建立就医路径…",
  ready: "路径已就绪 · 即将进入工作台",
};

/**
 * Care path diagram. Stage progress is driven by explicit `stages` (real request
 * state) when provided; otherwise it is a static explainer. There is no timer
 * animation that pretends to be algorithm execution.
 */
export function CarePath({ phase = "idle", stages, tone = "neutral", statusLabel }: CarePathProps) {
  const isAnalysing = phase === "analysing";
  const isReady = phase === "ready";

  const stageById = new Map((stages ?? []).map((stage) => [stage.id, stage]));
  const resolvedProgress = isReady
    ? pathSteps.length
    : stages
      ? pathSteps.filter((step) => stageById.get(step.id)?.status === "done").length
      : 0;
  const footer = statusLabel ?? phaseFooter[phase];

  return (
    <div
      className={[
        "care-path",
        phase !== "idle" ? `care-path--${phase}` : "",
        tone !== "neutral" ? `care-path--tone-${tone}` : "",
      ].filter(Boolean).join(" ")}
      aria-label="症状到就医路径的产品流程示意"
      aria-busy={isAnalysing}
    >
      <div className="care-path__orb care-path__orb--one" />
      <div className="care-path__orb care-path__orb--two" />
      <div className="care-path__header">
        <span className="eyebrow eyebrow--muted">Care Routing Path</span>
        {isAnalysing ? (
          <LoaderCircle className="spin care-path__header-spin" size={16} strokeWidth={1.7} aria-hidden="true" />
        ) : (
          <Route size={16} strokeWidth={1.7} aria-hidden="true" />
        )}
      </div>
      <div className="care-path__stage" role="list">
        <svg className="care-path__connectors" viewBox="0 0 280 320" aria-hidden="true" preserveAspectRatio="none">
          <path
            className={[
              "care-path__flow",
              isAnalysing ? "is-analysing" : "",
              isReady ? "is-ready" : "",
            ].filter(Boolean).join(" ")}
            d="M40 36 C40 70, 70 78, 70 110 S110 150, 110 184 S150 220, 150 254 S190 290, 200 300"
          />
        </svg>
        {pathSteps.map((step, index) => {
          const Icon = step.icon;
          const stageState = stageById.get(step.id);
          const isDone = stageState
            ? stageState.status === "done"
            : isReady || index < resolvedProgress;
          const isBlocked = stageState?.status === "blocked";
          const isActive = stageState
            ? stageState.status === "active"
            : !isDone && isAnalysing && index === resolvedProgress;
          const isBusy = isActive && isAnalysing;
          return (
            <div
              key={step.id}
              role="listitem"
              className={[
                "care-path__step",
                `care-path__step--d${step.depth}`,
                isActive ? "is-active" : "",
                isDone ? "is-done" : "",
                isBusy ? "is-busy" : "",
                isBlocked ? "is-blocked" : "",
              ].filter(Boolean).join(" ")}
              style={{ "--i": index } as React.CSSProperties}
            >
              <div
                className={[
                  "care-path__node",
                  isDone ? "care-path__node--done" : "",
                  isActive ? "care-path__node--active" : "",
                  isBlocked ? "care-path__node--blocked" : "",
                  !isDone && !isActive && !isBlocked ? "care-path__node--soft" : "",
                ].filter(Boolean).join(" ")}
              >
                {isBusy ? (
                  <LoaderCircle className="spin" size={14} strokeWidth={1.8} aria-hidden="true" />
                ) : (
                  <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
                )}
              </div>
              <div className="care-path__copy">
                <p>{step.label}</p>
                <span>{stageState?.hint ?? step.caption}</span>
              </div>
            </div>
          );
        })}
      </div>
      <div className="care-path__footer">
        <span className={`care-path__pulse${isAnalysing ? " is-busy" : ""}${isReady ? " is-ready" : ""}`} />
        <span>{footer}</span>
      </div>
    </div>
  );
}
