import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Button } from "../ui/Button";
import type { FollowupAnswer, FollowupPayload, FollowupQuestion } from "../../types/api";

interface FollowupPromptProps {
  followup: FollowupPayload;
  stepNumber: number;
  onAnswer: (question: FollowupQuestion, answer: FollowupAnswer) => void;
  onSkip: () => void;
  disabled?: boolean;
  directionDeferred?: boolean;
}

/**
 * The follow-up question is the primary action on the result screen: it sits
 * above the result card so the next step is never below the fold.
 */
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
        <span className="followup-prompt__badge">还需要一步 · 补充信息</span>
        <span className="followup-prompt__step">第 {stepNumber} 问 / 共 {Math.max(followup.questions.length, stepNumber)} 问</span>
      </div>
      <h2 id="followup-title">{question.question}</h2>
      {primarySlot ? (
        <p className="followup-prompt__slot" data-testid="followup-slot-link">
          本题主要补充：{primarySlot.replace(/^缺少/, "")}
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

      <div className="followup-prompt__footer">
        <button className="followup-prompt__skip" type="button" onClick={onSkip} disabled={disabled}>
          {directionDeferred ? "稍后补充，保留待复核状态" : "暂时跳过，查看当前就医方向"}
        </button>
      </div>
    </section>
  );
}
