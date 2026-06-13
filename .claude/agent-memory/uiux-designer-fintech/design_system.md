---
name: design-system
description: Visual design tokens — dark-first palette, typography scale, spacing, badge specs for confidence/horizon/score
metadata:
  type: project
---

## Color Palette (dark-first, WCAG 2.1 AA)

NOTE (verified 2026-06-12 against app/globals.css): the SHIPPED palette is deep-navy, NOT the GitHub-dark values that were originally drafted below. Trust globals.css. Shipped tokens:
- Page bg:   #0a0e27 (--bg-base)  | Surface: #111629 (--bg-surface) | Raised: #1a1f3a | Hover: #232d47
- Border:    #2a3456 (--border) / #3a4566 (--border-light)
- Text:      #ffffff primary / #a1a8c1 secondary / #7a8299 muted (muted contrast borderline — see overhaul §7)
- Direction: bullish #10b981 / bearish #ef4444 / neutral #6b7280 (+ -bg/-border rgba tokens)
- Confidence: High #10b981 / Med #f59e0b / Low #6b7280
- Horizon:   Short #ef4444 / Medium #f97316 / Long #3b82f6
- Accent:    #06b6d4 cyan (--accent); also a separate blue #3b82f6 for Long — THREE blues compete
- Light mode via @media prefers-color-scheme (accent #0891b2)

### Overhaul recommendation (2026-06-12): reserve green/red for DIRECTION ONLY.
Confidence → neutral filled-dot scale (●●●/●●○/●○○). Horizon → neutral outlined pill, no color (kills the red=Short vs red=Bearish collision, and green=High vs green=Bullish collision). Collapse the three blues to one accent (#3B82F6), retire cyan.

### (Original draft GitHub-dark values — NOT shipped, kept for reference only)
- Page bg dark:   #0D1117
- Card bg dark:   #161B22
- Card hover:     #1C2128
- Border:         #30363D

### Text
- Primary:        #E6EDF3   (not pure white — reduces eye fatigue)
- Secondary:      #8B949E
- Tertiary/muted: #6E7681   (only for non-critical info, use sparingly)

### Accent
- Brand blue:     #1F6FEB   (primary CTAs, links, focus rings)
- Focus ring:     #388BFD4D (blue at 30% opacity)

### Semantic — Confidence Tiers (also maps to entry quality)
- High / Strong:       #3FB950  (green)  — text + left border
- Medium / Moderate:   #D29922  (amber)  — text + left border
- Low / Speculative:   #8B949E  (gray)   — text + left border

### Semantic — Time Horizons
- Short  (1–7d):   #F85149  (red, urgency)
- Medium (1–4wk):  #FFA657  (orange)
- Long   (1–3mo):  #79C0FF  (blue, calm)

### Status
- Staleness banner bg:   #2D2208  (dark amber)
- Staleness banner text: #FFA657
- Staleness banner bdr:  #7D4E00
- Low signal banner:     #0D2340 / #79C0FF
- Passing threshold bg:  #0D1F12 / #3FB950 border at 40% opacity
- Macro adjustment icon: #FFA657

### Score color ramp (0–100)
- 0–39:   #6E7681  (gray, below threshold)
- 40–54:  #8B949E  (muted gray)
- 55–69:  #D29922  (amber, passing)
- 70–84:  #3FB950  (green, strong)
- 85–100: #58A6FF  (blue, exceptional — rare)

## Typography

### Scale (uses Geist Sans / Geist Mono from layout.tsx)
- Dashboard title:   24px / 700 / Geist Sans / #E6EDF3
- Section heading:   14px / 600 / Geist Sans / #8B949E / UPPERCASE + letter-spacing: 0.06em
- Table header:      12px / 600 / Geist Sans / #8B949E / UPPERCASE
- Table body:        14px / 400 / Geist Sans / #E6EDF3
- Score/number:      14px / 600 / Geist Mono / monospace (for alignment)
- Rationale body:    15px / 400 / Geist Sans / #C9D1D9 / line-height: 1.6
- Disclaimer text:   12px / 400 / Geist Sans / #6E7681 / line-height: 1.5
- Badge text:        11px / 600 / Geist Sans / UPPERCASE

## Spacing Scale (Tailwind 4 compatible)
- 4px   (gap-1)  — icon-to-text gaps
- 8px   (gap-2)  — intra-component
- 12px  (gap-3)  — card padding (compact)
- 16px  (gap-4)  — standard card padding
- 24px  (gap-6)  — section spacing
- 32px  (gap-8)  — panel padding

## Component Specs

### ConfidenceBadge
- High:    bg #0D1F12, text #3FB950, border #1A3D22, icon "●" (filled circle)
- Medium:  bg #1F1800, text #D29922, border #3D2D00, icon "◐" (half circle)
- Low:     bg #161B22, text #8B949E, border #30363D, icon "○" (empty circle)
- Size: px-2 py-0.5, rounded-full, text-[11px] font-semibold uppercase
- Always include text label (never icon-only — color blind safety)

### HorizonBadge
- Short:   bg #1F0C0C, text #F85149
- Medium:  bg #1F1200, text #FFA657
- Long:    bg #0D1A2D, text #79C0FF
- Same size as ConfidenceBadge

### ScoreDisplay (table row)
- Monospace number (e.g., "78") left-padded to 2 digits
- Small filled bar underneath (4px tall, 32px wide max-width)
- Bar fill = score/100 * 32px
- Bar color follows score color ramp above

### CategoryMomentumCard
- Passing (>=55): left border 3px solid #3FB950, bg #0D1F12
- Failing (<55):  left border 3px solid #30363D, bg #161B22
- Macro adjusted: info icon (ⓘ) in #FFA657 with tooltip
- Directional arrow: ▲ #3FB950 / ▼ #F85149 / — #8B949E
- Momentum score: Geist Mono, 20px, color follows score ramp
