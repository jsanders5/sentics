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
    bg: "bg-[--short-bg]",
    text: "text-[--short]",
    border: "border-[--short]",
  },
  Medium: {
    bg: "bg-[--medium-h-bg]",
    text: "text-[--medium-h]",
    border: "border-[--medium-h]",
  },
  Long: {
    bg: "bg-[--long-bg]",
    text: "text-[--long]",
    border: "border-[--long]",
  },
};

export function HorizonBadge({ horizon = "Medium", size = "md" }: HorizonBadgeProps) {
  const config = horizonConfig[horizon];
  const sizeClass = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm";

  return (
    <span
      className={`inline-flex items-center rounded-full border font-semibold ${sizeClass} ${config.bg} ${config.text} ${config.border}`}
    >
      {horizon}
    </span>
  );
}
