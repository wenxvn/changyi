import { useEffect, useRef, useState } from "react";
import { Mic, MicOff, Square } from "lucide-react";

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};

interface SpeechInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
  className?: string;
}

function getRecognitionCtor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === "undefined") return null;
  const scoped = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  return scoped.SpeechRecognition ?? scoped.webkitSpeechRecognition ?? null;
}

export function SpeechInput({ onTranscript, disabled, className }: SpeechInputProps) {
  const [listening, setListening] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const supported = Boolean(getRecognitionCtor());

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
    };
  }, []);

  if (!supported) {
    return (
      <span
        className={["speech-input speech-input--unsupported", className ?? ""].filter(Boolean).join(" ")}
        title="当前浏览器不支持语音输入"
      >
        <MicOff size={15} aria-hidden="true" />
        <span>当前浏览器不支持语音输入</span>
      </span>
    );
  }

  function stopListening() {
    recognitionRef.current?.stop();
    setListening(false);
  }

  function startListening() {
    if (disabled || listening) return;
    const Ctor = getRecognitionCtor();
    if (!Ctor) {
      setMessage("当前浏览器不支持语音输入");
      return;
    }
    const recognition = new Ctor();
    recognition.lang = "zh-CN";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const parts: string[] = [];
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        if (result.isFinal) parts.push(result[0].transcript);
      }
      const transcript = parts.join("").trim();
      if (transcript) onTranscript(transcript);
    };
    recognition.onerror = () => {
      setMessage("没有听清，请重试或手动输入");
      setListening(false);
    };
    recognition.onend = () => {
      setListening(false);
    };
    recognitionRef.current = recognition;
    setMessage(null);
    setListening(true);
    try {
      recognition.start();
    } catch {
      setListening(false);
      setMessage("语音输入暂时不可用");
    }
  }

  return (
    <span className={["speech-input", className ?? ""].filter(Boolean).join(" ")}>
      <button
        type="button"
        className="speech-input__button"
        onClick={() => (listening ? stopListening() : startListening())}
        disabled={disabled}
        aria-pressed={listening}
        aria-label={listening ? "停止语音输入" : "语音输入"}
      >
        {listening ? <Square size={14} aria-hidden="true" /> : <Mic size={14} aria-hidden="true" />}
        {listening ? "正在聆听…" : "语音输入"}
      </button>
      {message ? <span className="speech-input__hint" role="status">{message}</span> : null}
      {listening ? <span className="speech-input__hint" role="status">说完后请人工检查文字，再点击分析。</span> : null}
    </span>
  );
}
