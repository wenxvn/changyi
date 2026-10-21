import { useEffect, useState } from "react";
import { ChevronRight } from "lucide-react";

interface DepartmentCandidate {
  department: string;
  score?: number | null;
  source?: string;
}

interface DepartmentRouteBarProps {
  departments: DepartmentCandidate[];
  highlight?: string | null;
  maxBars?: number;
  onSelect?: (department: string) => void;
}

export function DepartmentRouteBar({
  departments,
  highlight,
  maxBars = 4,
  onSelect,
}: DepartmentRouteBarProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const validDepartments = departments
    .filter((dept) => dept && typeof dept.department === "string" && dept.department.trim())
    .slice(0, maxBars);

  if (validDepartments.length === 0) {
    return (
      <div className="department-route-bar department-route-bar--empty">
        <span className="department-route-bar__empty-message">等待科室方向…</span>
      </div>
    );
  }

  // Normalize scores for display (0-100%)
  const scores = validDepartments.map((dept) => dept.score ?? 0);
  const maxScore = Math.max(...scores, 1);
  const normalizedDepts = validDepartments.map((dept) => ({
    ...dept,
    displayScore: ((dept.score ?? 0) / maxScore) * 100,
  }));

  const primaryDept = normalizedDepts[0];
  const secondaryDepts = normalizedDepts.slice(1);

  return (
    <div className="department-route-bar">
      {/* Primary department */}
      <div
        className={`department-route-bar__primary ${highlight === primaryDept.department ? "is-highlighted" : ""} ${mounted ? "is-mounted" : ""}`}
        onClick={() => onSelect?.(primaryDept.department)}
        role={onSelect ? "button" : undefined}
        tabIndex={onSelect ? 0 : undefined}
      >
        <div className="department-route-bar__header">
          <strong className="department-route-bar__name">{primaryDept.department}</strong>
          <span className="department-route-bar__score">{Math.round(primaryDept.displayScore)}%</span>
        </div>
        <div className="department-route-bar__track">
          <div
            className="department-route-bar__fill department-route-bar__fill--primary"
            style={{ width: `${primaryDept.displayScore}%` }}
          />
        </div>
        {primaryDept.source === "population_context" ? (
          <small className="department-route-bar__note">人群适用入口</small>
        ) : null}
      </div>

      {/* Secondary departments */}
      {secondaryDepts.length > 0 ? (
        <div className="department-route-bar__secondary-group">
          <span className="department-route-bar__secondary-label">其他可能</span>
          {secondaryDepts.map((dept, index) => (
            <div
              key={dept.department}
              className={`department-route-bar__secondary ${highlight === dept.department ? "is-highlighted" : ""} ${mounted ? "is-mounted" : ""}`}
              onClick={() => onSelect?.(dept.department)}
              role={onSelect ? "button" : undefined}
              tabIndex={onSelect ? 0 : undefined}
              style={{ animationDelay: `${(index + 1) * 100}ms` }}
            >
              <div className="department-route-bar__secondary-header">
                <span className="department-route-bar__name">{dept.department}</span>
                <span className="department-route-bar__score">{Math.round(dept.displayScore)}%</span>
              </div>
              <div className="department-route-bar__track department-route-bar__track--secondary">
                <div
                  className="department-route-bar__fill department-route-bar__fill--secondary"
                  style={{ width: `${dept.displayScore}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {onSelect ? (
        <button
          type="button"
          className="department-route-bar__expand"
          onClick={() => {}}
        >
          <span>查看详细依据</span>
          <ChevronRight size={14} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
}
