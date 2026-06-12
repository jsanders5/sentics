interface ScoreDisplayProps {
  score: number;
  max?: number;
}

function getScoreColor(score: number): string {
  if (score >= 85) return "text-[#58A6FF]"; // Bright blue
  if (score >= 70) return "text-[--high]"; // Green
  if (score >= 55) return "text-[--medium]"; // Amber
  return "text-[--low]"; // Gray
}

function getScoreBarColor(score: number): string {
  if (score >= 85) return "bg-[#58A6FF]";
  if (score >= 70) return "bg-[--high]";
  if (score >= 55) return "bg-[--medium]";
  return "bg-[--low]";
}

export function ScoreDisplay({ score, max = 100 }: ScoreDisplayProps) {
  const percentage = (score / max) * 100;
  const colorClass = getScoreColor(score);
  const barColorClass = getScoreBarColor(score);

  return (
    <div className="flex flex-col items-start gap-1.5">
      <span className={`font-mono text-sm font-semibold ${colorClass}`}>
        {score.toFixed(1)}
      </span>
      <div className="h-1 w-8 overflow-hidden rounded-full bg-[--bg-surface]">
        <div
          className={`h-full transition-all ${barColorClass}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}
