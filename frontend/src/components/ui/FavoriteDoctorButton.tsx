import { Heart } from "lucide-react";

export function FavoriteDoctorButton({
  doctorId,
  active,
  onToggle,
  compact = false,
}: {
  doctorId: number;
  active: boolean;
  onToggle: (doctorId: number) => void;
  compact?: boolean;
}) {
  return (
    <button
      type="button"
      className={`favorite-doctor-button${active ? " is-active" : ""}${compact ? " favorite-doctor-button--compact" : ""}`}
      aria-pressed={active}
      aria-label={active ? "取消收藏该医生" : "收藏该医生"}
      title={active ? "取消收藏" : "收藏医生"}
      onClick={(event) => {
        event.stopPropagation();
        onToggle(doctorId);
      }}
    >
      <Heart size={compact ? 14 : 16} fill={active ? "currentColor" : "none"} aria-hidden="true" />
      {!compact ? <span>{active ? "已收藏" : "收藏"}</span> : null}
    </button>
  );
}
