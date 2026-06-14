import { Direction } from "@/app/types";

interface DirectionBadgeProps {
  direction: Direction;
  size?: "sm" | "md" | "lg";
}

const directionConfig: Record<Direction, { bg: string; text: string; border: string; icon: string }> = {
  Bullish: {
    bg: "bg-[--bullish]/10",
    text: "text-[--bullish]",
    border: "border-[--bullish]/30",
    icon: "▲",
  },
  Bearish: {
    bg: "bg-[--bearish]/10",
    text: "text-[--bearish]",
    border: "border-[--bearish]/30",
    icon: "▼",
  },
  Neutral: {
    bg: "bg-[--neutral-dir]/10",
    text: "text-[--neutral-dir]",
    border: "border-[--neutral-dir]/30",
    icon: "→",
  },
};

export function DirectionBadge({ direction, size = "md" }: DirectionBadgeProps) {
  const config = directionConfig[direction];
  const sizeClass =
    size === "lg"
      ? "px-3 py-1.5 text-base"
      : size === "sm"
      ? "px-2 py-1 text-xs"
      : "px-2.5 py-1.5 text-sm";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-bold ${sizeClass} ${config.bg} ${config.text} ${config.border} whitespace-nowrap`}
    >
      <span>{config.icon}</span>
      {direction}
    </span>
  );
}
