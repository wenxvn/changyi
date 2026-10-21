import { FlaskConical } from "lucide-react";

export interface ExampleSymptom {
  id: "routine" | "vague" | "emergency";
  label: string;
  badge: string;
  description: string;
  condition: string;
}

/**
 * Shortcut descriptions. Each chip only prefills the symptom text and still
 * goes through the real /api/v1 triage request — never a hardcoded result.
 */
export const exampleSymptoms: ExampleSymptom[] = [
  {
    id: "routine",
    label: "皮肤瘙痒",
    badge: "常见",
    description: "信息较明确",
    condition: "最近皮肤一直很痒，大概一周，没有呼吸困难，也没有发烧",
  },
  {
    id: "vague",
    label: "反复头晕",
    badge: "常见",
    description: "可能需要补充",
    condition: "最近总是头晕",
  },
  {
    id: "emergency",
    label: "胸痛伴气短",
    badge: "紧急",
    description: "优先看安全提示",
    condition: "胸口压榨样疼痛，喘不过气，还一直冒冷汗",
  },
];

interface ExampleSymptomChipsProps {
  onSelect: (example: ExampleSymptom) => void;
  disabled?: boolean;
}

export function ExampleSymptomChips({ onSelect, disabled = false }: ExampleSymptomChipsProps) {
  return (
    <div className="example-symptoms" data-testid="example-symptoms">
      <div className="example-symptoms__label">
        <FlaskConical size={14} aria-hidden="true" />
        <span>可以这样描述</span>
        <small>点击后仍由真实服务计算</small>
      </div>
      <div className="example-symptoms__row" role="group" aria-label="示例症状快捷入口">
        {exampleSymptoms.map((example) => (
          <button
            key={example.id}
            type="button"
            className="example-symptom"
            data-testid={`example-${example.id}`}
            disabled={disabled}
            onClick={() => onSelect(example)}
          >
            <span className="example-symptom__badge">{example.badge}</span>
            <strong>{example.label}</strong>
            <small>{example.description}</small>
          </button>
        ))}
      </div>
    </div>
  );
}
