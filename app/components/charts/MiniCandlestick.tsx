import { Candle } from "@/app/types";

interface MiniCandlestickProps {
  candles: Candle[];
  width?: number;
  height?: number;
  className?: string;
}

/**
 * Compact SVG candlestick for the card — no axes/labels, just wicks + bodies
 * colored by up/down day. Hand-rolled (no chart lib) to keep it tiny. The viewBox
 * scales to the card width via width="100%" + preserveAspectRatio="none"; wicks use
 * non-scaling-stroke so they stay crisp regardless of card width.
 */
export function MiniCandlestick({ candles, width = 240, height = 52, className }: MiniCandlestickProps) {
  if (!candles || candles.length === 0) return null;

  const pad = 2;
  const innerH = height - pad * 2;
  let max = Math.max(...candles.map((c) => c.h));
  let min = Math.min(...candles.map((c) => c.l));
  if (!Number.isFinite(max) || !Number.isFinite(min)) return null;
  if (max === min) {
    // Flat series — nudge the range so there's something to draw.
    max += 1;
    min -= 1;
  }

  const range = max - min;
  const y = (v: number) => pad + ((max - v) / range) * innerH;

  const n = candles.length;
  const slot = width / n;
  const bodyW = Math.max(1, slot * 0.62);

  return (
    <svg
      width="100%"
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className={className}
      role="img"
      aria-label={`Price candlestick chart, last ${n} daily candles`}
    >
      {candles.map((c, i) => {
        const cx = i * slot + slot / 2;
        const up = c.c >= c.o;
        const color = up ? "var(--bullish)" : "var(--bearish)";
        const bodyTop = Math.min(y(c.o), y(c.c));
        const bodyH = Math.max(1, Math.abs(y(c.c) - y(c.o)));
        return (
          <g key={i}>
            <line
              x1={cx}
              x2={cx}
              y1={y(c.h)}
              y2={y(c.l)}
              stroke={color}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
            <rect x={cx - bodyW / 2} y={bodyTop} width={bodyW} height={bodyH} fill={color} />
          </g>
        );
      })}
    </svg>
  );
}
