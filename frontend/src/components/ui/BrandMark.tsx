interface BrandMarkProps {
  compact?: boolean;
}

export function BrandMark({ compact = false }: BrandMarkProps) {
  return (
    <span className={`brand-mark${compact ? " brand-mark--compact" : ""}`} aria-hidden="true">
      <svg viewBox="0 0 40 40" role="presentation">
        <path d="M11 27.5c4.4 4.2 11.7 4.1 16.1-.3 4.5-4.5 4.5-11.7.1-16.1-4.3-4.3-11.3-4.3-15.6-.2" />
        <path d="M12.1 27.6 27.9 12" />
        <circle cx="11" cy="27.6" r="2.5" />
        <circle cx="28.1" cy="11" r="2.5" />
      </svg>
    </span>
  );
}
