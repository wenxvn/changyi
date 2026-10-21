import { AlertTriangle, Info, Clock, CheckCircle } from "lucide-react";
import type { TriageStatus } from "../../types/api";
import "./SafetyGateVisual.css";

interface SafetyGateVisualProps {
  status: TriageStatus;
  redFlags: string[];
  className?: string;
}

const safetyConfig = {
  EMERGENCY: {
    tone: "danger",
    icon: AlertTriangle,
    label: "需要优先评估",
    description: "描述中出现需要立即处理的危险信号。",
  },
  URGENT: {
    tone: "warning",
    icon: Clock,
    label: "建议尽快评估",
    description: "建议在较短时间内获得专业医疗评估。",
  },
  ROUTINE: {
    tone: "success",
    icon: CheckCircle,
    label: "未提示立即急诊",
    description: "可以继续了解合适的就医方向。",
  },
  INSUFFICIENT_INFORMATION: {
    tone: "neutral",
    icon: Info,
    label: "需要补充信息",
    description: "当前描述还不足以给出确定的就医方向。",
  },
} as const;

/**
 * Compact Safety Gate strip. It only restates the server-returned status and
 * risk words: no invented confidence score and no decorative orb.
 */
export function SafetyGateVisual({ status, redFlags, className = "" }: SafetyGateVisualProps) {
  const config = safetyConfig[status];
  const Icon = config.icon;

  return (
    <div className={`safety-gate-visual safety-gate-visual--${config.tone} ${className}`.trim()}>
      <span className="safety-gate-visual__icon" aria-hidden="true">
        <Icon size={20} strokeWidth={1.7} />
      </span>
      <div className="safety-gate-visual__content">
        <strong className="safety-gate-visual__label">{config.label}</strong>
        <span className="safety-gate-visual__description">{config.description}</span>
      </div>
      {redFlags.length > 0 ? (
        <ul className="safety-gate-visual__reasons" aria-label="识别到的风险信号">
          {redFlags.slice(0, 4).map((flag) => <li key={flag}>{flag}</li>)}
        </ul>
      ) : null}
    </div>
  );
}
