import { useEffect, useState } from "react";
import { ArrowRight, CircleHelp, History } from "lucide-react";
import { Button } from "../ui/Button";
import type { FollowupAnswer, FollowupPayload, FollowupQuestion } from "../../types/api";

interface FollowupPromptProps {
  followup: FollowupPayload;
  stepNumber: number;
  onAnswer: (question: FollowupQuestion, answer: FollowupAnswer) => void;
  onSkip: () => void;
  disabled?: boolean;
}

export function FollowupPrompt({
  followup,
  stepNumber,
  onAnswer,
  onSkip,
  disabled = false,
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

  return (
    <section className="followup-prompt" aria-labelledby="followup-title" data-testid="followup-prompt">
      <div className="followup-prompt__topline">
        <span className="eyebrow"><CircleHelp size={14} aria-hidden="true" /> 自适应追问 · <span>需要补充信息</span></span>
        <span className="followup-prompt__step">第 {stepNumber} 问 / 共 {Math.max(followup.questions.length, stepNumber)} 问</span>
      </div>
      <p className="followup-prompt__why">
        <History size={14} aria-hidden="true" />
        为什么现在问：当前信息不足以稳定给出科室方向，补充后路径会重新计算。
      </p>
      <h2 id="followup-title">{question.question}</h2>
      {question.reason ? <p className="followup-prompt__reason">{question.reason}</p> : null}

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
        暂时跳过，查看当前就医方向
      </button>
      <p className="followup-prompt__note">回答后会重新计算路径；跳过则保留当前一般性方向。</p>
    </section>
  );
}
