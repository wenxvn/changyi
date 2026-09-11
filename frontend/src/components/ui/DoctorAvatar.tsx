import { useState } from "react";

interface DoctorAvatarProps {
  name?: string;
  photoUrl?: string;
  className?: string;
  size?: "default" | "large";
}

export function DoctorAvatar({ name, photoUrl, className, size = "default" }: DoctorAvatarProps) {
  const [failed, setFailed] = useState(false);
  const initial = name?.slice(0, 1) || "医";
  const classes = [
    "doctor-index-avatar",
    size === "large" ? "doctor-index-avatar--large" : "",
    className ?? "",
  ].filter(Boolean).join(" ");

  if (!photoUrl || failed) {
    return <div className={classes} aria-hidden="true">{initial}</div>;
  }

  return (
    <div className={`${classes} doctor-index-avatar--photo`} aria-hidden="true">
      <img
        src={photoUrl}
        alt=""
        loading="lazy"
        decoding="async"
        onError={() => setFailed(true)}
      />
    </div>
  );
}
