import { useId } from "react";
import type { AgentStage } from "./types";

export function AgentFallback({ stage, isStatic = false }: { stage: AgentStage; isStatic?: boolean }) {
  const rawId = useId();
  const id = rawId.replace(/:/g, "");

  return (
    <svg
      className={`care-agent__fallback${isStatic ? " care-agent__fallback--static" : ""}`}
      viewBox="0 0 240 240"
      role="img"
      aria-label={`抽象光球视觉反馈：${stage}`}
      focusable="false"
    >
      <defs>
        <radialGradient id={`${id}-orb`} cx="35%" cy="28%" r="72%">
          <stop offset="0%" stopColor="var(--agent-highlight)" />
          <stop offset="45%" stopColor="var(--agent-core)" />
          <stop offset="100%" stopColor="var(--accent-primary)" />
        </radialGradient>
        <radialGradient id={`${id}-halo`}>
          <stop offset="0%" stopColor="var(--agent-core)" stopOpacity=".22" />
          <stop offset="100%" stopColor="var(--agent-core)" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle className="care-agent__halo" cx="120" cy="120" r="112" fill={`url(#${id}-halo)`} />
      <g className="care-agent__orbit care-agent__orbit--back" fill="none" stroke="var(--agent-orbit)">
        <ellipse cx="120" cy="120" rx="93" ry="37" transform="rotate(-28 120 120)" />
      </g>
      <circle className="care-agent__orb" cx="120" cy="120" r="59" fill={`url(#${id}-orb)`} />
      <circle className="care-agent__orb-glint" cx="98" cy="94" r="15" fill="white" fillOpacity=".34" />
      <g className="care-agent__orbit care-agent__orbit--front" fill="none" stroke="var(--agent-orbit)">
        <ellipse cx="120" cy="120" rx="88" ry="33" transform="rotate(34 120 120)" />
      </g>
      <circle className="care-agent__particle care-agent__particle--one" cx="35" cy="77" r="3.5" />
      <circle className="care-agent__particle care-agent__particle--two" cx="197" cy="164" r="2.5" />
      <circle className="care-agent__particle care-agent__particle--three" cx="65" cy="205" r="2" />
    </svg>
  );
}
