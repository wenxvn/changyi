import { useEffect, useRef, useState } from "react";
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

const pathSteps = [
  { label: "症状", caption: "用自己的话描述不适", icon: CircleDot, depth: 0 },
  { label: "安全门", caption: "优先识别危险信号", icon: ShieldCheck, depth: 1 },
  { label: "就医方向", caption: "整理科室与下一步", icon: Stethoscope, depth: 2 },
  { label: "资源路径", caption: "医院 · 医生 · 导航", icon: MapPinned, depth: 1 },
  { label: "到院行动", caption: "带着依据去就医", icon: CircleCheck, depth: 0 },
] as const;

interface CarePathProps {
  phase?: CarePathPhase;
  progress?: number;
  tone?: CarePathTone;
  statusLabel?: string;
}

const phaseFooter: Record<CarePathPhase, string> = {
  idle: "从安全开始 · 悬停查看每一步",
  analysing: "正在建立就医路径…",
  ready: "路径已就绪 · 即将进入工作台",
};

export function CarePath({ phase = "idle", progress, tone = "neutral", statusLabel }: CarePathProps) {
  const [active, setActive] = useState(0);
  const timerRef = useRef<number | null>(null);
  const isAnalysing = phase === "analysing";
  const isReady = phase === "ready";

  useEffect(() => {
    if (!isAnalysing) {
      if (timerRef.current !== null) {
        window.clearInterval(timerRef.current);
        timerRef.current = null;
      }
      if (isReady) setActive(pathSteps.length);
      return;
    }

    setActive(0);
    let index = 0;
    timerRef.current = window.setInterval(() => {
      index += 1;
      setActive(index);
      if (index >= pathSteps.length - 1 && timerRef.current !== null) {
        window.clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }, 160);

    return () => {
      if (timerRef.current !== null) {
        window.clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isAnalysing, isReady]);

  const resolvedProgress = typeof progress === "number" ? progress : isReady ? pathSteps.length : active;
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
          const isDone = index < resolvedProgress;
          const isActive = !isDone && (isAnalysing ? index === resolvedProgress : index === active);
          return (
            <button
              type="button"
              role="listitem"
              key={step.label}
              className={[
                "care-path__step",
                `care-path__step--d${step.depth}`,
                isActive ? "is-active" : "",
                isDone ? "is-done" : "",
                isAnalysing && index === resolvedProgress ? "is-busy" : "",
              ].filter(Boolean).join(" ")}
              style={{ "--i": index } as React.CSSProperties}
              onMouseEnter={() => {
                if (!isAnalysing && !isReady) setActive(index);
              }}
              onFocus={() => {
                if (!isAnalysing && !isReady) setActive(index);
              }}
              onClick={() => {
                if (!isAnalysing && !isReady) setActive(index);
              }}
            >
              <div
                className={[
                  "care-path__node",
                  isDone ? "care-path__node--done" : "",
                  isActive ? "care-path__node--active" : "",
                  !isDone && !isActive ? "care-path__node--soft" : "",
                ].filter(Boolean).join(" ")}
              >
                {isAnalysing && index === resolvedProgress ? (
                  <LoaderCircle className="spin" size={14} strokeWidth={1.8} aria-hidden="true" />
                ) : (
                  <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
                )}
              </div>
              <div className="care-path__copy">
                <p>{step.label}</p>
                <span>{step.caption}</span>
              </div>
            </button>
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
