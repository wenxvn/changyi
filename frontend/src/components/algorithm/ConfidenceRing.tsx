import "./ConfidenceRing.css";

interface ConfidenceRingProps {
  confidence: number; // 0-100
  label?: string;
  size?: number;
  showPercentage?: boolean;
  className?: string;
}

export function ConfidenceRing({
  confidence,
  label = "置信度",
  size = 120,
  showPercentage = true,
  className = ""
}: ConfidenceRingProps) {
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (confidence / 100) * circumference;

  // 根据置信度选择颜色
  const getColor = (conf: number) => {
    if (conf >= 80) return "var(--status-success)";
    if (conf >= 60) return "var(--status-info)";
    if (conf >= 40) return "var(--status-warning)";
    return "var(--status-danger)";
  };

  const color = getColor(confidence);

  return (
    <div className={`confidence-ring ${className}`}>
      <svg width={size} height={size} className="confidence-ring__svg">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--surface-raised)"
          strokeWidth={strokeWidth}
        />

        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          className="confidence-ring__progress"
        />
      </svg>

      <div className="confidence-ring__content">
        {showPercentage && (
          <div className="confidence-ring__percentage" style={{ color }}>
            {Math.round(confidence)}%
          </div>
        )}
        <div className="confidence-ring__label">{label}</div>
      </div>
    </div>
  );
}
