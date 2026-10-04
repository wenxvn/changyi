import { useEffect, useState } from "react";
import { doctorPhotoVariants } from "../../utils/doctorPhotos";

interface DoctorAvatarProps {
  name?: string;
  photoUrl?: string;
  className?: string;
  size?: "default" | "large";
}

export function DoctorAvatar({ name, photoUrl, className, size = "default" }: DoctorAvatarProps) {
  const [failedSource, setFailedSource] = useState<string | null>(null);
  const [failedVariant, setFailedVariant] = useState<string | null>(null);
  const [loaded, setLoaded] = useState<{ url: string | undefined; variants: Awaited<ReturnType<typeof doctorPhotoVariants>> }>({ url: undefined, variants: null });
  useEffect(() => {
    if (!photoUrl) return;
    let active = true;
    doctorPhotoVariants(photoUrl).then(variants => {
      if (active) setLoaded({ url: photoUrl, variants });
    }).catch(() => { if (active) setLoaded({ url: photoUrl, variants: null }); });
    return () => { active = false; };
  }, [photoUrl]);
  const variants = failedVariant === photoUrl ? null : loaded.variants;
  const initial = name?.slice(0, 1) || "医";
  const classes = [
    "doctor-index-avatar",
    size === "large" ? "doctor-index-avatar--large" : "",
    className ?? "",
  ].filter(Boolean).join(" ");

  if (!photoUrl || failedSource === photoUrl || loaded.url !== photoUrl) {
    return <div className={classes} aria-hidden="true">{initial}</div>;
  }

  return (
    <div className={`${classes} doctor-index-avatar--photo`} aria-hidden="true">
      <img
        src={variants?.medium ?? photoUrl}
        srcSet={variants ? `${variants.small} 80w, ${variants.medium} 160w, ${variants.large} 320w` : undefined}
        sizes={size === "large" ? "128px" : "64px"}
        alt=""
        loading="lazy"
        decoding="async"
        onError={() => variants ? setFailedVariant(photoUrl) : setFailedSource(photoUrl)}
      />
    </div>
  );
}
