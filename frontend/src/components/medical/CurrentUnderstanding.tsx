import { ClipboardList, ShieldCheck } from "lucide-react";
import { StatusPill } from "../ui/StatusPill";
import type { TriagePayload } from "../../types/api";

interface CurrentUnderstandingProps {
  condition: string;
  result: TriagePayload;
}

const STATUS_TONE: Record<TriagePayload["triage_status"], "neutral" | "success" | "warning" | "danger"> = {
  EMERGENCY: "danger",
  URGENT: "warning",
  ROUTINE: "success",
  INSUFFICIENT_INFORMATION: "neutral",
};

const STATUS_LABEL: Record<TriagePayload["triage_status"], string> = {
  EMERGENCY: "需要优先评估",
  URGENT: "建议尽快评估",
  ROUTINE: "可继续了解路径",
  INSUFFICIENT_INFORMATION: "需要补充信息",
};

/**
 * Compact context card for the right rail: it restates what the system read and
 * which preferences are currently in play, so the left column can stay a decision.
 */
export function CurrentUnderstanding({ condition, result }: CurrentUnderstandingProps) {
  const status = result.triage_status;
  return (
    <aside className="context-card" aria-labelledby="understanding-title">
      <div className="context-card__header">
        <span className="eyebrow" id="understanding-title"><ClipboardList size={14} aria-hidden="true" /> 当前理解</span>
        <StatusPill tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</StatusPill>
      </div>
      <p className="context-card__quote">“{condition}”</p>
      <dl className="context-card__facts">
        <div>
          <dt>安全门</dt>
          <dd>{STATUS_LABEL[status]}</dd>
        </div>
        <div>
          <dt>就医方向</dt>
          <dd>{result.matched_department ?? "待补充信息后收窄"}</dd>
        </div>
      </dl>
      <p className="context-card__notice">
        <ShieldCheck size={14} aria-hidden="true" /> 系统对当前输入的辅助整理，不是诊断结论。
      </p>
    </aside>
  );
}
