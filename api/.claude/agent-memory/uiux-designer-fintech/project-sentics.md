---
name: project-sentics
description: Sentics trading intelligence dashboard — architecture, design decisions, and active redesign context
metadata:
  type: project
---

Sentics is a dark-navy Next.js + Tailwind dashboard at `/Users/jake/wb/git/sentics` (frontend root) backed by a FastAPI backend at `/Users/jake/wb/git/sentics/api`.

## Active redesign (as of 2026-06-12)

Removing the category concept entirely. Pipeline now outputs top 25 cryptos by market cap with:
- Direction: Bullish / Bearish / Neutral (NEW — replaces category as primary signal)
- Timeframe: Short / Medium / Long
- Confidence: High / Medium / Low
- Score, RSI, Volume Ratio, Technical Score, Rationale, Key Signals, Price

**Why:** Category momentum scoring was Agent 1 output. The new pipeline skips category filtering and evaluates the top 25 directly.

**How to apply:** All design decisions assume category is gone. Never propose category-based UI patterns for this project.

## CSS theme

Dark navy: `--bg-base: #0a0e27`, `--bg-surface: #111629`, `--bg-raised: #1a1f3a`
Cyan accent: `--accent: #06b6d4`
Confidence: green (`--high: #10b981`), amber (`--medium: #f59e0b`), gray (`--low: #6b7280`)
Timeframe: red (`--short: #ef4444`), orange (`--medium-h: #f97316`), blue (`--long: #3b82f6`)
Direction (proposed new): bullish `#22c55e`, bearish `#f43f5e`, neutral `#64748b`

Direction colors are intentionally distinct from existing confidence/timeframe colors to avoid same-row color collisions.

## Known bugs in current codebase

- `--low-signal-bg` and `--low-signal-text` referenced in `page.tsx` lines 144-147 but not defined in `globals.css` — the low-signal banner is currently broken/invisible
- `tbody td` in `globals.css` line 118 sets `border-left: 4px solid transparent` which conflicts with Tailwind `border-l-4` on `<tr>` elements
- `thead sticky top: 73px` in `globals.css` line 89 is hardcoded to current header height — will need updating if header is compacted

## Files to delete (category removal)

- `app/components/panels/CategoryPanel.tsx`
- `app/components/panels/CategoryMomentumCard.tsx`
- `app/hooks/useCategories.ts`

## Design decisions made

- Left border on table rows should switch from confidence to direction (direction is more actionable as primary visual signal)
- Header should compact from 73px to 56px to give more table viewport
- Filter bar should use pill-toggle chips instead of `<select>` dropdowns (3-4 options per filter = chips are faster)
- Mobile table should show only 4 columns: #, Asset, Direction (icon only), Score
- Merged Symbol+Name into single "Asset" column (bold mono symbol, muted name below)
- Drawer direction "hero" block: colored background matching direction, large text verdict
- Drawer width: increase from `md:w-96` (384px) to `md:w-[420px]`

## Implementation order agreed

1. types/index.ts — add Direction type, update Candidate/FilterState/SortKey
2. DirectionBadge.tsx — new component, additive
3. useFilterState.ts — replace category filter with direction
4. FilterBar.tsx — direction chips, remove category dropdown
5. CandidatesTable + CandidateRow — new columns, direction badge, merged asset cell
6. CandidateDetailDrawer — direction hero, remove category_momentum
7. Header.tsx — compact + staleness-aware indicator
8. globals.css — direction variables, fix border-left conflict, fix thead sticky top
9. Delete dead files, clean up page.tsx
