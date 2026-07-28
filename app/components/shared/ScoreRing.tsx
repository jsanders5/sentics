interface ScoreRingProps {
  score: number;
  max?: number;
  size?: number;
  label?: string;
  title?: string;
}

// Score is a magnitude (signal strength), not a direction — so it keeps a
// blue→green→amber scale independent of the Bullish/Bearish color language.
function scoreColor(score: number): string {
  if (score >= 85) return "var(--score-elite)";
  if (score >= 70) return "var(--high)";
  if (score >= 55) return "var(--medium)";
  return "var(--text-muted)";
}

export function ScoreRing({ score, max = 100, size = 52, label, title }: ScoreRingProps) {
  const stroke = 4;
  const r = (size - stroke) / 2;
  const circumference = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, score / max));
  const dash = circumference * pct;
  const color = scoreColor(score);

  return (
    <div className="flex flex-col items-center gap-1" title={title}>
      <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--bg-raised)" strokeWidth={stroke} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circumference}`}
            style={{ transition: "stroke-dasharray 500ms cubic-bezier(0.4,0,0.2,1)" }}
          />
        </svg>
        <span className="absolute font-mono font-bold" style={{ color, fontSize: size * 0.28 }}>
          {Math.round(score)}
        </span>
      </div>
      {label && (
        <span className="text-[10px] uppercase tracking-wider text-[--text-muted]">{label}</span>
      )}
    </div>
  );
}
