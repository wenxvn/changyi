import { Component, Suspense, lazy, useEffect, useRef, useState, type ErrorInfo, type ReactNode } from "react";
import { AgentFallback } from "./AgentFallback";
import { AGENT_STAGE_LABEL, type AgentStage } from "./types";

const LazyAgentScene = lazy(() => import("./AgentScene").then((module) => ({ default: module.AgentScene })));

class SceneBoundary extends Component<{ onError: () => void; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(_error: Error, _info: ErrorInfo) {
    this.props.onError();
  }

  render() {
    return this.state.failed ? null : this.props.children;
  }
}

function webgl2Available(): boolean {
  try {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("webgl2", { failIfMajorPerformanceCaveat: true });
    context?.getExtension("WEBGL_lose_context")?.loseContext();
    return Boolean(context);
  } catch {
    return false;
  }
}

function isConstrainedDevice(): boolean {
  const navigatorWithHints = navigator as Navigator & {
    deviceMemory?: number;
    connection?: { saveData?: boolean };
  };
  return Boolean(
    navigatorWithHints.connection?.saveData
    || (navigatorWithHints.deviceMemory !== undefined && navigatorWithHints.deviceMemory <= 2)
    || navigator.hardwareConcurrency <= 2,
  );
}

export function CareAgent({ stage, compact = false }: { stage: AgentStage; compact?: boolean }) {
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const [visible, setVisible] = useState(false);
  const [canRender, setCanRender] = useState(false);
  const [failed, setFailed] = useState(false);
  const [skipMotion, setSkipMotion] = useState(false);

  useEffect(() => {
    const element = wrapperRef.current;
    if (!element || typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setVisible(true);
        observer.disconnect();
      }
    }, { rootMargin: "96px" });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible || typeof window === "undefined") return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setCanRender(!reduced && !isConstrainedDevice() && webgl2Available());
  }, [visible]);

  const label = AGENT_STAGE_LABEL[stage];
  const animated = canRender && !failed && !skipMotion;
  const showSkip = animated && (stage === "submitting" || stage === "waiting");

  return (
    <div
      ref={wrapperRef}
      className={`care-agent${compact ? " care-agent--compact" : ""} care-agent--${stage}`}
      data-testid="care-agent"
      data-agent-stage={stage}
    >
      <div className="care-agent__visual" aria-hidden="true">
        {animated ? (
          <SceneBoundary onError={() => setFailed(true)}>
            <Suspense fallback={<AgentFallback stage={stage} isStatic />}>
              <LazyAgentScene stage={stage} onError={() => setFailed(true)} />
            </Suspense>
          </SceneBoundary>
        ) : <AgentFallback stage={stage} isStatic={skipMotion || failed || !canRender} />}
      </div>
      <div className="care-agent__copy" role="status" aria-live="polite" aria-atomic="true">
        <span className="care-agent__eyebrow">常医智导助手</span>
        <strong>{label}</strong>
        <span className="care-agent__disclaimer">仅呈现请求状态与服务端返回信息，不进行独立医疗判断。</span>
      </div>
      {showSkip ? (
        <button className="care-agent__skip" type="button" onClick={() => setSkipMotion(true)}>
          跳过动态效果
        </button>
      ) : null}
    </div>
  );
}
