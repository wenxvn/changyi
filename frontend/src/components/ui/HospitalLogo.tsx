import { useState } from "react";
import { Building2 } from "lucide-react";

interface HospitalLogoProps {
  hospitalId?: number;
  className?: string;
  size?: "default" | "preview";
}

/** Compact retained icons exist for catalog hospital ids 1..21. */
const KNOWN_ICON_IDS = new Set(Array.from({ length: 21 }, (_, index) => index + 1));

export function HospitalLogo({ hospitalId, className, size = "default" }: HospitalLogoProps) {
  const [failed, setFailed] = useState(false);
  const classes = [
    "resource-index-card__mark",
    "hospital-logo",
    size === "preview" ? "hospital-logo--preview" : "",
    className ?? "",
  ].filter(Boolean).join(" ");

  const id = typeof hospitalId === "number" && KNOWN_ICON_IDS.has(hospitalId) ? hospitalId : null;
  const src = id === null || failed ? null : `/static/images/hospitals/icons/hospital_${id}.png`;

  if (!src) {
    return (
      <div className={classes} aria-hidden="true">
        <Building2 size={20} strokeWidth={1.5} />
      </div>
    );
  }

  return (
    <div className={classes} aria-hidden="true">
      <img
        src={src}
        alt=""
        loading="lazy"
        decoding="async"
        onError={() => setFailed(true)}
      />
    </div>
  );
}
