import { ConfidenceTier } from "@/app/types";

interface ConfidenceBadgeProps {
  tier: ConfidenceTier;
  size?: "sm" | "md";
}

// Confidence uses a neutral cyan accent scale — green/red are reserved for Direction.
const confidenceConfig: Record<
  ConfidenceTier,
  { bg: string; text: string; border: string; icon: string }
> = {
  High: {
    bg: "bg-[--conf-high-bg]",
    text: "text-[--conf-high]",
    border: "border-[--conf-high-border]",
    icon: "●",
  },
  Medium: {
    bg: "bg-[--conf-medium-bg]",
    text: "text-[--conf-medium]",
    border: "border-[--conf-medium-border]",
    icon: "◐",
  },
  Low: {
    bg: "bg-[--conf-low-bg]",
    text: "text-[--conf-low]",
    border: "border-[--conf-low-border]",
    icon: "○",
  },
};

export function ConfidenceBadge({ tier, size = "md" }: ConfidenceBadgeProps) {
  const config = confidenceConfig[tier];
  const sizeClass = size === "sm" ? "px-4 py-2 text-xs" : "px-5 py-2.5 text-sm";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-bold ${sizeClass} ${config.bg} ${config.text} ${config.border} whitespace-nowrap`}
    >
      <span className="text-xs">{config.icon}</span>
      {tier}
    </span>
  );
}
