import { Category } from "@/app/types";

interface CategoryMomentumCardProps {
  category: Category;
  isSelected?: boolean;
  onClick?: () => void;
}

function getMomentumColor(score: number): string {
  if (score >= 55) return "bg-[--high]";
  if (score >= 40) return "bg-[--medium]";
  return "bg-[--low]";
}

function getMomentumArrow(score: number): string {
  if (score >= 55) return "↑";
  if (score >= 40) return "→";
  return "↓";
}

function getMomentumArrowColor(score: number): string {
  if (score >= 55) return "text-[--high]";
  if (score >= 40) return "text-[--medium]";
  return "text-[--low]";
}

export function CategoryMomentumCard({
  category,
  isSelected = false,
  onClick,
}: CategoryMomentumCardProps) {
  const barColor = getMomentumColor(category.momentum_score);
  const arrow = getMomentumArrow(category.momentum_score);
  const arrowColor = getMomentumArrowColor(category.momentum_score);

  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-xl border transition-smooth group ${
        isSelected
          ? "border-[--accent] bg-[--accent]/10 ring-2 ring-[--accent]/50"
          : "border-[--border] bg-[--bg-surface] hover:border-[--accent]/30 hover:bg-[--bg-raised]"
      }`}
    >
      <div className="p-4 space-y-3">
        {/* Header: Category name and arrow */}
        <div className="flex items-start justify-between">
          <h3 className="font-sans text-sm font-bold text-[--text-primary] leading-tight">
            {category.name}
          </h3>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <span className={`text-base font-bold ${arrowColor}`}>
              {arrow}
            </span>
            {category.macro_adjustment !== 0 && (
              <span
                title={`Macro adjustment: ${category.macro_adjustment > 0 ? "+" : ""}${category.macro_adjustment.toFixed(1)}`}
                className="text-xs text-[--text-muted] cursor-help opacity-60 group-hover:opacity-100 transition-smooth"
              >
                ⓘ
              </span>
            )}
          </div>
        </div>

        {/* Score in monospace */}
        <div className="font-mono text-xl font-bold text-[--text-primary] tracking-tight">
          {category.momentum_score.toFixed(1)}
        </div>

        {/* Progress bar */}
        <div className="h-2 w-full overflow-hidden rounded-full bg-[--bg-surface]">
          <div
            className={`h-full transition-all rounded-full ${barColor}`}
            style={{
              width: `${Math.min(category.momentum_score, 100)}%`,
            }}
          />
        </div>

        {/* Footer: Category signal */}
        <div className="text-xs font-semibold text-[--text-muted] uppercase tracking-wider">
          {category.momentum_score >= 55 && "Strong"}
          {category.momentum_score >= 40 && category.momentum_score < 55 && "Active"}
          {category.momentum_score < 40 && "Weak"}
        </div>
      </div>
    </button>
  );
}
