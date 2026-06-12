import { TimeHorizon } from "@/app/types";

interface HorizonBadgeProps {
  horizon?: TimeHorizon;
  size?: "sm" | "md";
}

const horizonConfig: Record<
  TimeHorizon,
  { bg: string; text: string; border: string }
> = {
  Short: {
    bg: "bg-[--short]/10",
    text: "text-[--short]",
    border: "border-[--short]/30",
  },
  Medium: {
    bg: "bg-[--medium-h]/10",
    text: "text-[--medium-h]",
    border: "border-[--medium-h]/30",
  },
  Long: {
    bg: "bg-[--long]/10",
    text: "text-[--long]",
    border: "border-[--long]/30",
  },
};

export function HorizonBadge({ horizon = "Medium", size = "md" }: HorizonBadgeProps) {
  const config = horizonConfig[horizon];
  const sizeClass = size === "sm" ? "px-2 py-1 text-xs" : "px-3 py-1.5 text-sm";

  return (
    <span
      className={`inline-flex items-center rounded-full border font-bold ${sizeClass} ${config.bg} ${config.text} ${config.border} whitespace-nowrap`}
    >
      {horizon}
    </span>
  );
}
