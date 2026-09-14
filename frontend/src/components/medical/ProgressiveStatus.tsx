import { Check, CircleDot, LoaderCircle } from "lucide-react";

export type ProgressiveStageStatus = "pending" | "active" | "done" | "blocked";

export interface ProgressiveStage {
  id: string;
  label: string;
  status: ProgressiveStageStatus;
  hint?: string;
}

export function ProgressiveStatus({ stages, label }: { stages: ProgressiveStage[]; label?: string }) {
  return (
    <ol className="progressive-status" aria-live="polite" aria-label={label ?? "分析进度"}>
      {stages.map((stage, index) => (
        <li
          key={stage.id}
          className={[
            stage.status === "active" ? "is-active" : "",
            stage.status === "done" ? "is-done" : "",
            stage.status === "blocked" ? "is-blocked" : "",
          ].filter(Boolean).join(" ")}
        >
          <span className="progressive-status__icon" aria-hidden="true">
            {stage.status === "done" ? (
              <Check size={13} strokeWidth={2.2} />
            ) : stage.status === "active" ? (
              <LoaderCircle className="spin" size={13} strokeWidth={2} />
            ) : (
              <CircleDot size={13} strokeWidth={1.8} />
            )}
          </span>
          <div>
            <strong>{stage.label}</strong>
            {stage.hint ? <span>{stage.hint}</span> : null}
          </div>
          {index < stages.length - 1 ? <i className="progressive-status__rail" aria-hidden="true" /> : null}
        </li>
      ))}
    </ol>
  );
}
