import { TimeHorizon } from "@/app/types";

interface HorizonBadgeProps {
  horizon?: TimeHorizon;
  size?: "sm" | "md";
}

// Horizon is ordinal time, not good/bad — rendered as a neutral slate badge.
// The label (and an optional range) carries the meaning, no color coding.
const horizonRange: Record<TimeHorizon, string> = {
  Short: "1-7d",
  Medium: "1-4w",
  Long: "1-3mo",
};

export function HorizonBadge({ horizon = "Medium", size = "md" }: HorizonBadgeProps) {
  const sizeClass = size === "sm" ? "px-2 py-1 text-xs" : "px-3 py-1.5 text-sm";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-semibold bg-[--horizon-bg] text-[--horizon-fg] border-[--horizon-border] ${sizeClass} whitespace-nowrap`}
    >
      {horizon}
      <span className="text-[--text-muted] font-normal">{horizonRange[horizon]}</span>
    </span>
  );
}
