import { useState } from "react";
import { ChevronDown, ChevronUp, Tags } from "lucide-react";
import type { TriagePayload } from "../../types/api";

interface AlgorithmEvidenceProps {
  result: TriagePayload;
  previousTags?: string[];
  previousDepts?: string[];
  pathUpdated?: boolean;
}

export function AlgorithmEvidence({
  result,
  previousTags,
  previousDepts,
  pathUpdated,
}: AlgorithmEvidenceProps) {
  const [expanded, setExpanded] = useState(false);

  const symptomTags = (result.triage?.symptom_tags ?? [])
    .filter((item) => item && typeof item.tag === "string")
    .slice(0, 10);

  const deptCandidates = Array.isArray(result.htriage_analysis?.department_candidates)
    ? result.htriage_analysis.department_candidates
        .filter((item) => item && typeof item.department === "string")
        .slice(0, 5)
    : [];

  const redFlags = (result.triage?.red_flag_tags ?? []).filter(Boolean);
  const reasons = (result.triage?.reasons ?? []).filter(Boolean);
  const missing = (result.triage?.followup?.missing_slots ?? []).filter(Boolean);

  const prevTagSet = new Set(previousTags ?? []);
  const prevDeptSet = new Set(previousDepts ?? []);

  const hasEvidence =
    symptomTags.length > 0 ||
    deptCandidates.length > 0 ||
    redFlags.length > 0 ||
    reasons.length > 0 ||
    missing.length > 0;

  if (!hasEvidence) {
    return null;
  }

  return (
    <details
      className="algorithm-evidence"
      open={expanded}
      onToggle={(e) => setExpanded(e.currentTarget.open)}
    >
      <summary className="algorithm-evidence__trigger">
        <span className="algorithm-evidence__trigger-text">
          {expanded ? "收起算法依据" : "查看算法依据"}
        </span>
        {expanded ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
      </summary>

      <div className="algorithm-evidence__content">
        {/* Symptom Tags */}
        {symptomTags.length > 0 ? (
          <section className="algorithm-evidence__section">
            <h4 className="algorithm-evidence__heading">
              <Tags size={14} aria-hidden="true" />
              识别到的症状词
            </h4>
            <ul className="algorithm-evidence__tag-list">
              {symptomTags.map((item) => (
                <li
                  key={item.tag}
                  className={pathUpdated && !prevTagSet.has(item.tag) && (previousTags?.length ?? 0) > 0 ? "is-new" : ""}
                >
                  <strong>{item.tag}</strong>
                  {item.matched_terms && item.matched_terms.length > 0 ? (
                    <span className="algorithm-evidence__tag-matches">
                      匹配：{item.matched_terms.slice(0, 3).join("、")}
                    </span>
                  ) : null}
                  {item.body_system ? (
                    <span className="algorithm-evidence__tag-system">{item.body_system}</span>
                  ) : null}
                  {pathUpdated && !prevTagSet.has(item.tag) && (previousTags?.length ?? 0) > 0 ? (
                    <small className="algorithm-evidence__tag-badge">补充后新增</small>
                  ) : null}
                </li>
              ))}
            </ul>
            <p className="algorithm-evidence__disclaimer">
              仅展示服务端已识别的原文证据；人口词不计为症状，未经临床校准。
            </p>
          </section>
        ) : null}

        {/* Department Candidates */}
        {deptCandidates.length > 0 ? (
          <section className="algorithm-evidence__section">
            <h4 className="algorithm-evidence__heading">科室候选依据</h4>
            <ul className="algorithm-evidence__dept-list">
              {deptCandidates.map((item) => (
                <li
                  key={item.department}
                  className={pathUpdated && !prevDeptSet.has(item.department) && (previousDepts?.length ?? 0) > 0 ? "is-new" : ""}
                >
                  <strong>{item.department}</strong>
                  {item.score !== null && item.score !== undefined ? (
                    <span className="algorithm-evidence__dept-score">{item.score.toFixed(2)}</span>
                  ) : null}
                  {item.source === "population_context" ? (
                    <span className="algorithm-evidence__dept-source">人群适用入口，非疾病判断</span>
                  ) : item.source ? (
                    <span className="algorithm-evidence__dept-source">来源：{item.source}</span>
                  ) : null}
                  {pathUpdated && !prevDeptSet.has(item.department) && (previousDepts?.length ?? 0) > 0 ? (
                    <small className="algorithm-evidence__dept-badge">补充后新增</small>
                  ) : null}
                </li>
              ))}
            </ul>
            <p className="algorithm-evidence__disclaimer">
              相对支持度未经临床校准，不代表患病概率；最终以医生面诊为准。
            </p>
          </section>
        ) : null}

        {/* Red Flags */}
        {redFlags.length > 0 ? (
          <section className="algorithm-evidence__section algorithm-evidence__section--warning">
            <h4 className="algorithm-evidence__heading">风险信号</h4>
            <ul className="algorithm-evidence__flag-list">
              {redFlags.map((flag) => (
                <li key={flag}>{flag}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {/* Reasons */}
        {reasons.length > 0 ? (
          <section className="algorithm-evidence__section">
            <h4 className="algorithm-evidence__heading">判断原因</h4>
            <ul className="algorithm-evidence__reason-list">
              {reasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {/* Missing Information */}
        {missing.length > 0 ? (
          <section className="algorithm-evidence__section algorithm-evidence__section--info">
            <h4 className="algorithm-evidence__heading">待补充信息</h4>
            <ul className="algorithm-evidence__missing-list">
              {missing.map((slot, index) => (
                <li key={index}>{slot}</li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </details>
  );
}
