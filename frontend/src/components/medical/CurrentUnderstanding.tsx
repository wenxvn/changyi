import { ClipboardList, ShieldCheck, Tags } from "lucide-react";
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
 * only shows key signals that the backend already returned. No clinical
 * confidence is invented here.
 */
export function CurrentUnderstanding({ condition, result }: CurrentUnderstandingProps) {
  const status = result.triage_status;
  const tags = (result.triage?.red_flag_tags ?? []).filter(Boolean).filter((tag, index, all) => all.indexOf(tag) === index).slice(0, 6);
  const missing = (result.triage?.followup?.missing_slots ?? []).filter(Boolean).slice(0, 4);
  const answers = result.followup_answers ?? [];

  return (
    <aside className="context-card" aria-labelledby="understanding-title">
      <div className="context-card__header">
        <span className="eyebrow" id="understanding-title"><ClipboardList size={14} aria-hidden="true" /> 当前理解</span>
        <StatusPill tone={STATUS_TONE[status]}><span>{STATUS_LABEL[status]}</span></StatusPill>
      </div>
      <p className="context-card__quote">“{condition}”</p>

      {tags.length > 0 ? (
        <div className="context-card__tags" data-testid="understanding-tags">
          <span className="eyebrow eyebrow--muted"><Tags size={12} aria-hidden="true" /> 关键信号</span>
          <ul>
            {tags.map((tag) => <li key={tag}>{tag}</li>)}
          </ul>
        </div>
      ) : null}

      {answers.length > 0 ? (
        <div className="context-card__answers" data-testid="understanding-answers">
          <span className="eyebrow eyebrow--muted">已补充信息</span>
          <ul>
            {answers.map((answer) => (
              <li key={answer.question_id}>
                {answer.value ?? answer.text_answer ?? "已回答"}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <dl className="context-card__facts">
        <div>
          <dt>安全门</dt>
          <dd>{STATUS_LABEL[status]}</dd>
        </div>
        <div>
          <dt>就医方向</dt>
          <dd>
            {result.matched_department ?? "暂不强行给出科室方向"}
            {status === "INSUFFICIENT_INFORMATION" ? <small>信息不足 · 需要补充后再收窄</small> : null}
          </dd>
        </div>
        {missing.length > 0 ? (
          <div>
            <dt>待补充</dt>
            <dd>{missing.join("、")}</dd>
          </div>
        ) : null}
      </dl>
      <p className="context-card__notice">
        <ShieldCheck size={14} aria-hidden="true" /> 系统对当前输入的辅助整理，不是诊断结论。
      </p>
    </aside>
  );
}
