import { useRef, type FormEvent, type KeyboardEvent } from "react";
import { ArrowRight, LoaderCircle } from "lucide-react";
import { Button } from "../ui/Button";
import { SpeechInput } from "../ui/SpeechInput";

export interface SymptomComposerProps {
  id: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  label?: string;
  placeholder?: string;
  submitLabel: string;
  busyLabel?: string;
  disabled?: boolean;
  loading?: boolean;
  rows?: number;
  variant?: "home" | "workspace";
  onFocusChange?: (focused: boolean) => void;
}

const MAX_LENGTH = 2000;

export function SymptomComposer({
  id,
  value,
  onChange,
  onSubmit,
  label = "症状描述",
  placeholder = "例如：最近总是头晕，大概有几天了。",
  submitLabel,
  busyLabel = "正在等待系统响应",
  disabled = false,
  loading = false,
  rows = 4,
  variant = "workspace",
  onFocusChange,
}: SymptomComposerProps) {
  const formRef = useRef<HTMLFormElement | null>(null);
  const isDisabled = disabled || loading;

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      formRef.current?.requestSubmit();
    }
  };

  const appendTranscript = (transcript: string) => {
    const separator = value.trim() && !/[。！？.!?]$/.test(value.trim()) ? "。" : "";
    onChange(`${value}${separator}${transcript}`.slice(0, MAX_LENGTH));
  };

  return (
    <form
      ref={formRef}
      className={`symptom-composer symptom-composer--${variant}`}
      onSubmit={onSubmit}
      data-testid="symptom-composer"
    >
      <label htmlFor={id} className="symptom-composer__label">{label}</label>
      <textarea
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => onFocusChange?.(true)}
        onBlur={() => onFocusChange?.(false)}
        placeholder={placeholder}
        rows={rows}
        maxLength={MAX_LENGTH}
        disabled={isDisabled}
        aria-describedby={`${id}-hint ${id}-counter`}
        data-testid="symptom-input"
      />
      <div className="symptom-composer__hint" id={`${id}-hint`}>
        文字描述或语音输入均可；只需描述不适，不必填写姓名等身份信息。按 Ctrl/⌘ + Enter 提交。
      </div>
      <div className="symptom-composer__footer">
        <div className="symptom-composer__tools">
          <SpeechInput disabled={isDisabled} onTranscript={appendTranscript} />
          <span className="character-count" id={`${id}-counter`} aria-live="off">{value.length} / {MAX_LENGTH}</span>
        </div>
        <Button
          type="submit"
          className="symptom-composer__submit"
          disabled={!value.trim() || isDisabled}
          aria-busy={loading}
          icon={loading
            ? <LoaderCircle className="spin" size={18} aria-hidden="true" />
            : <ArrowRight size={18} strokeWidth={1.8} aria-hidden="true" />}
        >
          {loading ? busyLabel : submitLabel}
        </Button>
      </div>
    </form>
  );
}
