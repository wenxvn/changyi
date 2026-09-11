import { ExternalLink, Navigation } from "lucide-react";
import { buildAmapNavigationUrl, type AmapNavigationTarget } from "../../utils/navigation";

interface AmapNavigationLinkProps {
  target: AmapNavigationTarget;
  label?: string;
  className?: string;
  disabledLabel?: string;
}

export function AmapNavigationLink({
  target,
  label = "高德导航",
  className = "",
  disabledLabel = "暂无地址",
}: AmapNavigationLinkProps) {
  const href = buildAmapNavigationUrl(target);
  const classes = `${className}${className ? " " : ""}amap-navigation-link`;
  if (!href) {
    return (
      <button className={classes} type="button" disabled aria-disabled="true">
        <Navigation size={14} aria-hidden="true" /> {disabledLabel}
      </button>
    );
  }
  return (
    <a className={classes} href={href} target="_blank" rel="noopener noreferrer">
      <Navigation size={14} aria-hidden="true" /> {label} <ExternalLink size={12} aria-hidden="true" />
    </a>
  );
}
