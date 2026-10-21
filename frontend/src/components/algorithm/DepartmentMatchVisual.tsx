import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import "./DepartmentMatchVisual.css";

interface DepartmentCandidate {
  name: string;
  score: number;
  reasoning: string[];
}

interface DepartmentMatchVisualProps {
  candidates: DepartmentCandidate[];
  symptomTags?: string[];
  title?: string;
  /** When false, every row is a plain alternative (no "主要方向" badge). */
  highlightPrimary?: boolean;
  className?: string;
}

/**
 * Ranked department directions. Candidate scores are deliberately not shown as
 * percentages: they are relative match scores, not calibrated probabilities.
 */
export function DepartmentMatchVisual({
  candidates,
  symptomTags = [],
  title = "建议科室方向",
  highlightPrimary = true,
  className = ""
}: DepartmentMatchVisualProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const topCandidates = candidates.slice(0, 3);

  return (
    <div className={`department-match-visual ${className}`.trim()}>
      <div className="department-match-visual__header">
        <h3>{title}</h3>
        {symptomTags.length > 0 ? (
          <p className="department-match-visual__basis">
            依据：{symptomTags.slice(0, 5).join("、")}
          </p>
        ) : null}
      </div>

      <ol className="department-match-visual__list">
        {topCandidates.map((candidate, index) => {
          const isExpanded = expandedIndex === index;
          const isPrimary = highlightPrimary && index === 0;

          return (
            <li
              key={candidate.name}
              className={`department-match-visual__item${isPrimary ? " department-match-visual__item--primary" : ""}`}
            >
              <button
                type="button"
                onClick={() => setExpandedIndex(isExpanded ? null : index)}
                className="department-match-visual__item-header"
                aria-expanded={isExpanded}
              >
                <span className="department-match-visual__item-name">
                  {isPrimary ? <span className="department-match-visual__badge">主要方向</span> : highlightPrimary ? <span className="department-match-visual__badge department-match-visual__badge--muted">备选</span> : null}
                  {candidate.name}
                </span>
                {isExpanded ? <ChevronUp size={17} aria-hidden="true" /> : <ChevronDown size={17} aria-hidden="true" />}
              </button>

              {isExpanded ? (
                <div className="department-match-visual__item-details">
                  {candidate.reasoning.length > 0 ? (
                    <ul>
                      {candidate.reasoning.map((reason) => <li key={reason}>{reason}</li>)}
                    </ul>
                  ) : (
                    <p>来自服务端返回的科室候选；候选分只是相对排序，未经临床校准。</p>
                  )}
                </div>
              ) : null}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
