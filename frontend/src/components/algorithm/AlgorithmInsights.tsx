import { Brain, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import "./AlgorithmInsights.css";

interface AlgorithmInsightsProps {
  extractedSymptoms: string[];
  bodySystems: string[];
  redFlags: string[];
  analysisSteps?: {
    step: string;
    result: string;
  }[];
  className?: string;
}

export function AlgorithmInsights({
  extractedSymptoms,
  bodySystems,
  redFlags,
  analysisSteps = [],
  className = ""
}: AlgorithmInsightsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={`algorithm-insights ${className}`}>
      <div className="algorithm-insights__header">
        <div className="algorithm-insights__header-content">
          <Brain size={24} strokeWidth={1.5} />
          <h3>系统理解了什么？</h3>
        </div>
      </div>

      <div className="algorithm-insights__summary">
        {extractedSymptoms.length > 0 && (
          <div className="algorithm-insights__item">
            <span className="algorithm-insights__label">症状关键词：</span>
            <span className="algorithm-insights__value">
              {extractedSymptoms.join("、")}
            </span>
          </div>
        )}

        {bodySystems.length > 0 && (
          <div className="algorithm-insights__item">
            <span className="algorithm-insights__label">相关身体系统：</span>
            <span className="algorithm-insights__value">
              {bodySystems.join("、")}
            </span>
          </div>
        )}

        {redFlags.length > 0 && (
          <div className="algorithm-insights__item algorithm-insights__item--warning">
            <span className="algorithm-insights__label">检测到的警示信号：</span>
            <span className="algorithm-insights__value">
              {redFlags.join("、")}
            </span>
          </div>
        )}
      </div>

      {analysisSteps.length > 0 && (
        <>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="algorithm-insights__toggle"
          >
            {isExpanded ? "收起详细分析" : "展开查看完整分析"}
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {isExpanded && (
            <div className="algorithm-insights__details">
              {analysisSteps.map((step, index) => (
                <div key={index} className="algorithm-insights__step">
                  <div className="algorithm-insights__step-name">{step.step}</div>
                  <div className="algorithm-insights__step-result">{step.result}</div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
