import { useState } from "react";
import { CircleCheck, CircleDot, Route, ShieldCheck, Stethoscope, MapPinned } from "lucide-react";

const pathSteps = [
  { label: "症状", caption: "用自己的话描述不适", icon: CircleDot, depth: 0 },
  { label: "安全门", caption: "优先识别危险信号", icon: ShieldCheck, depth: 1 },
  { label: "就医方向", caption: "整理科室与下一步", icon: Stethoscope, depth: 2 },
  { label: "资源路径", caption: "医院 · 医生 · 导航", icon: MapPinned, depth: 1 },
  { label: "到院行动", caption: "带着依据去就医", icon: CircleCheck, depth: 0 },
] as const;

export function CarePath() {
  const [active, setActive] = useState(0);

  return (
    <div className="care-path" aria-label="症状到就医路径的产品流程示意">
      <div className="care-path__orb care-path__orb--one" />
      <div className="care-path__orb care-path__orb--two" />
      <div className="care-path__header">
        <span className="eyebrow eyebrow--muted">Care Routing Path</span>
        <Route size={16} strokeWidth={1.7} aria-hidden="true" />
      </div>
      <div className="care-path__stage" role="list">
        <svg className="care-path__connectors" viewBox="0 0 280 320" aria-hidden="true" preserveAspectRatio="none">
          <path className="care-path__flow" d="M40 36 C40 70, 70 78, 70 110 S110 150, 110 184 S150 220, 150 254 S190 290, 200 300" />
        </svg>
        {pathSteps.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === active;
          const isDone = index < active;
          return (
            <button
              type="button"
              role="listitem"
              key={step.label}
              className={[
                "care-path__step",
                `care-path__step--d${step.depth}`,
                isActive ? "is-active" : "",
                isDone ? "is-done" : "",
              ].filter(Boolean).join(" ")}
              style={{ "--i": index } as React.CSSProperties}
              onMouseEnter={() => setActive(index)}
              onFocus={() => setActive(index)}
              onClick={() => setActive(index)}
            >
              <div className={`care-path__node${isActive ? " care-path__node--active" : isDone ? " care-path__node--done" : " care-path__node--soft"}`}>
                <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
              </div>
              <div className="care-path__copy">
                <p>{step.label}</p>
                <span>{step.caption}</span>
              </div>
            </button>
          );
        })}
      </div>
      <div className="care-path__footer">
        <span className="care-path__pulse" />
        <span>从安全开始 · 悬停查看每一步</span>
      </div>
    </div>
  );
}
