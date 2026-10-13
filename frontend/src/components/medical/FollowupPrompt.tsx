import { useEffect, useState } from "react";
import { ArrowRight, CircleHelp, History } from "lucide-react";
import { Button } from "../ui/Button";
import { AgentFallback } from "../agent/AgentFallback";
import type { FollowupAnswer, FollowupPayload, FollowupQuestion } from "../../types/api";

interface FollowupPromptProps {
  followup: FollowupPayload;
  stepNumber: number;
  onAnswer: (question: FollowupQuestion, answer: FollowupAnswer) => void;
  onSkip: () => void;
  disabled?: boolean;
  directionDeferred?: boolean;
}

export function FollowupPrompt({
  followup,
  stepNumber,
  onAnswer,
  onSkip,
  disabled = false,
  directionDeferred = false,
}: FollowupPromptProps) {
  const question = followup.questions[0];
  const [freeText, setFreeText] = useState("");

  useEffect(() => {
    setFreeText("");
  }, [question?.id]);

  if (!followup.needed || !question) return null;

  const submitFreeText = () => {
    if (freeText.trim() && !disabled) onAnswer(question, { question_id: question.id, text_answer: freeText.trim() });
  };
  const primarySlot = (followup.missing_slots ?? []).filter(Boolean)[0] ?? null;

  return (
    <section className="followup-prompt" aria-labelledby="followup-title" data-testid="followup-prompt">
      <div className="followup-prompt__topline">
        <span className="eyebrow"><CircleHelp size={14} aria-hidden="true" /> 自适应追问 · <span>需要补充信息</span></span>
        <span className="followup-prompt__step">第 {stepNumber} 问 / 共 {Math.max(followup.questions.length, stepNumber)} 问</span>
      </div>
      <div className="followup-prompt__agent">
        <span className="followup-prompt__agent-mark" aria-hidden="true">
          <AgentFallback stage="needs_followup" isStatic />
        </span>
        <div>
          <strong>常医智导助手</strong>
          <p>为了更准确地给出就医方向，我还需要了解这一项信息。</p>
        </div>
      </div>
      <p className="followup-prompt__why">
        <History size={14} aria-hidden="true" />
        这道问题由系统根据本次输入返回；回答后会重新请求并更新路径。
      </p>
      <h2 id="followup-title">{question.question}</h2>
      {question.reason ? <p className="followup-prompt__reason">{question.reason}</p> : null}
      {primarySlot ? (
        <p className="followup-prompt__reason" data-testid="followup-slot-link">
          <small>本题主要补充：{primarySlot}；回答后症状证据与科室依据会同步更新。</small>
        </p>
      ) : null}

      {question.options.length > 0 ? (
        <div className="followup-prompt__options" role="group" aria-label="追问选项">
          {question.options.map((option) => (
            <button
              className="followup-option"
              type="button"
              key={option.value}
              disabled={disabled}
              data-testid={`followup-option-${option.value}`}
              onClick={() => onAnswer(question, { question_id: question.id, value: option.value })}
            >
              <span>{option.label}</span>
              <ArrowRight size={15} aria-hidden="true" />
            </button>
          ))}
        </div>
      ) : (
        <div className="followup-prompt__free-text">
          <label htmlFor="followup-answer">补充说明</label>
          <textarea
            id="followup-answer"
            value={freeText}
            onChange={(event) => setFreeText(event.target.value)}
            placeholder="用一句话补充即可"
            rows={3}
            maxLength={500}
            disabled={disabled}
          />
          <Button
            type="button"
            variant="secondary"
            disabled={!freeText.trim() || disabled}
            onClick={submitFreeText}
            icon={<ArrowRight size={16} aria-hidden="true" />}
          >
            提交补充
          </Button>
        </div>
      )}

      <button className="followup-prompt__skip" type="button" onClick={onSkip} disabled={disabled}>
        {directionDeferred ? "稍后补充，保留待复核状态" : "暂时跳过，查看当前就医方向"}
      </button>
      <p className="followup-prompt__note">{directionDeferred ? "稍后补充不会解除待复核状态，确认前不进行资源排序。" : "回答后会重新计算路径；跳过则保留当前一般性方向。"}</p>
    </section>
  );
}
