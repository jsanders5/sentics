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
    bg: "bg-[--high]/10",
    text: "text-[--high]",
    border: "border-[--high]/30",
    icon: "●",
  },
  Medium: {
    bg: "bg-[--medium]/10",
    text: "text-[--medium]",
    border: "border-[--medium]/30",
    icon: "◐",
  },
  Low: {
    bg: "bg-[--low]/10",
    text: "text-[--low]",
    border: "border-[--low]/30",
    icon: "○",
  },
};

export function ConfidenceBadge({ tier, size = "md" }: ConfidenceBadgeProps) {
  const config = confidenceConfig[tier];
  const sizeClass = size === "sm" ? "px-2 py-1 text-xs" : "px-3 py-1.5 text-sm";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-bold ${sizeClass} ${config.bg} ${config.text} ${config.border} whitespace-nowrap`}
    >
      <span className="text-xs">{config.icon}</span>
      {tier}
    </span>
  );
}
