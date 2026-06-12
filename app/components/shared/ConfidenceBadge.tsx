import { ConfidenceTier } from "@/app/types";

interface ConfidenceBadgeProps {
  tier: ConfidenceTier;
  size?: "sm" | "md";
}

const confidenceConfig: Record<
  ConfidenceTier,
  { bg: string; text: string; border: string; icon: string }
> = {
  High: {
    bg: "bg-[--high-bg]",
    text: "text-[--high]",
    border: "border-[--high-border]",
    icon: "●",
  },
  Medium: {
    bg: "bg-[--medium-bg]",
    text: "text-[--medium]",
    border: "border-[--medium-border]",
    icon: "◐",
  },
  Low: {
    bg: "bg-[--low-bg]",
    text: "text-[--low]",
    border: "border-[--low-border]",
    icon: "○",
  },
};

export function ConfidenceBadge({ tier, size = "md" }: ConfidenceBadgeProps) {
  const config = confidenceConfig[tier];
  const sizeClass = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-semibold ${sizeClass} ${config.bg} ${config.text} ${config.border}`}
    >
      <span className="text-xs">{config.icon}</span>
      {tier}
    </span>
  );
}
