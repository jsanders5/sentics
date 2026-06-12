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
  if (score >= 55) return "▲";
  if (score >= 40) return "●";
  return "▼";
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
  const isBullish = category.momentum_score >= 55;

  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-lg border p-3 transition-all ${
        isSelected
          ? "border-[--accent] bg-[--bg-raised] ring-2 ring-[--accent]"
          : "border-[--border] bg-[--bg-surface] hover:bg-[--bg-raised]"
      }`}
    >
      <div className="space-y-2">
        {/* Category name and arrow */}
        <div className="flex items-center justify-between">
          <h3 className="font-sans text-sm font-medium text-[--text-primary]">
            {category.name}
          </h3>
          <div className="flex items-center gap-1">
            <span className={`text-lg font-bold ${arrowColor}`}>{arrow}</span>
            {category.macro_adjustment !== 0 && (
              <span
                title={`Macro adjustment: ${category.macro_adjustment > 0 ? "+" : ""}${category.macro_adjustment.toFixed(1)}`}
                className="text-xs text-[--text-muted] cursor-help"
              >
                ⓘ
              </span>
            )}
          </div>
        </div>

        {/* Score */}
        <div className="font-mono text-lg font-semibold text-[--text-primary]">
          {category.momentum_score.toFixed(1)}
        </div>

        {/* Score bar */}
        <div className="h-1 w-full overflow-hidden rounded-full bg-[--bg-raised]">
          <div
            className={`h-full transition-all ${barColor}`}
            style={{
              width: `${Math.min(category.momentum_score, 100)}%`,
            }}
          />
        </div>
      </div>
    </button>
  );
}
