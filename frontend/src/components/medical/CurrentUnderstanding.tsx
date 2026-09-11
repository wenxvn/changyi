import { ClipboardList, ShieldCheck } from "lucide-react";
import { StatusPill } from "../ui/StatusPill";
import type { FollowupPayload, TriagePayload } from "../../types/api";

interface CurrentUnderstandingProps {
  condition: string;
  result: TriagePayload;
  followup?: FollowupPayload | null;
}

const statusLabel: Record<TriagePayload["triage_status"], string> = {
  EMERGENCY: "需要优先评估",
  URGENT: "建议尽快评估",
  ROUTINE: "可继续了解路径",
  INSUFFICIENT_INFORMATION: "需要补充信息",
};

export function CurrentUnderstanding({ condition, result, followup }: CurrentUnderstandingProps) {
  const status = result.triage_status;
  const statusTone = status === "ROUTINE" ? "success" : status === "EMERGENCY" || status === "URGENT" ? "warning" : "neutral";

  return (
    <aside className="current-understanding" aria-labelledby="understanding-title">
      <div className="current-understanding__header">
        <span className="eyebrow" id="understanding-title"><ClipboardList size={14} aria-hidden="true" /> 当前理解</span>
        <StatusPill tone={statusTone}>{statusLabel[status]}</StatusPill>
      </div>
      <div className="current-understanding__quote">“{condition}”</div>
      <dl className="understanding-facts">
        <div>
          <dt>安全门状态</dt>
          <dd>{statusLabel[status]}</dd>
        </div>
        {result.matched_department ? (
          <div>
            <dt>返回的就医方向</dt>
            <dd>{result.matched_department}</dd>
          </div>
        ) : null}
        {followup?.needed ? (
          <div>
            <dt>下一步</dt>
            <dd>系统建议补足 {followup.questions.length} 个问题</dd>
          </div>
        ) : null}
      </dl>
      <p className="current-understanding__notice"><ShieldCheck size={15} aria-hidden="true" /> 这是系统对当前输入的辅助整理，不是诊断结论。</p>
    </aside>
  );
}
