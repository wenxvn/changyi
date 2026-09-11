import { ArrowDown, CircleCheck, CircleDot, Route, ShieldCheck } from "lucide-react";

const pathSteps = [
  { label: "症状", caption: "当前描述", state: "active" },
  { label: "安全门", caption: "先看风险", state: "soft" },
  { label: "就医方向", caption: "了解下一步", state: "soft" },
  { label: "资源路径", caption: "找到可用资源", state: "soft" },
] as const;

export function CarePath() {
  return (
    <div className="care-path" aria-label="症状到就医路径的产品流程示意">
      <div className="care-path__orb care-path__orb--one" />
      <div className="care-path__orb care-path__orb--two" />
      <div className="care-path__header">
        <span className="eyebrow eyebrow--muted">就医路径示意</span>
        <Route size={16} strokeWidth={1.7} aria-hidden="true" />
      </div>
      <div className="care-path__rail">
        {pathSteps.map((step, index) => (
          <div className="care-path__step" key={step.label}>
            <div className={`care-path__node care-path__node--${step.state}`}>
              {index === 0 ? (
                <CircleDot size={18} strokeWidth={1.7} aria-hidden="true" />
              ) : index === 1 ? (
                <ShieldCheck size={18} strokeWidth={1.7} aria-hidden="true" />
              ) : index === pathSteps.length - 1 ? (
                <CircleCheck size={18} strokeWidth={1.7} aria-hidden="true" />
              ) : (
                <span className="care-path__node-dot" />
              )}
            </div>
            <div>
              <p>{step.label}</p>
              <span>{step.caption}</span>
            </div>
            {index < pathSteps.length - 1 ? (
              <ArrowDown className="care-path__arrow" size={15} strokeWidth={1.5} aria-hidden="true" />
            ) : null}
          </div>
        ))}
      </div>
      <div className="care-path__footer">
        <span className="care-path__pulse" />
        <span>从安全开始，让路径逐步清晰</span>
      </div>
    </div>
  );
}
