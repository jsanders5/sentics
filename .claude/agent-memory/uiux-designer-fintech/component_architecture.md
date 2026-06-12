---
name: component-architecture
description: Full component map for the three-panel dashboard, interaction patterns, and Phase 2 extension slots
metadata:
  type: project
---

## Component Tree

```
app/
  layout.tsx              (existing — adds Geist fonts)
  page.tsx                (replace with DashboardPage)
  globals.css             (extend with design tokens)

components/
  layout/
    DashboardLayout.tsx   (three-panel grid: CategoryPanel | CandidatesTable | DetailDrawer)
    Header.tsx            (logo, disclaimer trigger, last-updated timestamp)
    Footer.tsx            (disclaimer links, legal copy)

  panels/
    CategoryPanel.tsx     (left panel — list of CategoryMomentumCards)
    CategoryMomentumCard.tsx
    FilterBar.tsx         (dropdowns: horizon, category, confidence + clear button)
    StalenessBar.tsx      (yellow banner — shown if data > 7h old)
    LowSignalBanner.tsx   (blue banner — shown if < 5 candidates)

  table/
    CandidatesTable.tsx   (sortable table with all 25 candidates)
    CandidateRow.tsx      (single row — click to open drawer)
    TableHeader.tsx       (sortable column headers)
    EmptyState.tsx        (no candidates match filters)

  detail/
    CandidateDetailDrawer.tsx  (right side-drawer on desktop, full-screen on mobile)
    DrawerHeader.tsx           (symbol, name, category, badges)
    RationaleSection.tsx       (AI rationale text + per-rationale disclaimer)
    SignalsBreakdown.tsx       (RSI, volume ratio, MA positioning — mini charts or bars)
    OnChainSection.tsx         (on-chain signals or "not available" state)
    PreTradeReference.tsx      (resistance zone, invalidation, ATR, R:R — bordered container)
    NewsHeadline.tsx            (latest headline + link)
    ProtocolEventFlag.tsx       (event badge if present)
    MemeCoinWarning.tsx         (warning if is_meme_coin)
    DisclaimerBlock.tsx         (per-rationale + crypto-specific disclaimers)

  shared/
    ConfidenceBadge.tsx    (High/Medium/Low with color + text)
    HorizonBadge.tsx       (Short/Medium/Long with color)
    ScoreDisplay.tsx       (number + mini bar)
    EntryTypeBadge.tsx     (Breakout/Retest/Dip-Buy)
    EntryQualityBadge.tsx  (Strong/Moderate/Speculative)
    Skeleton.tsx           (loading skeleton shapes)
    Tooltip.tsx            (hover tooltip for macro adjustments, meme cap, etc.)

  modals/
    DisclaimerModal.tsx    (first-visit modal — "I understand" required, no X close)
```

## Key Interaction Patterns

### Sorting
- Click column header to sort ASC; click again for DESC; third click resets
- Sort state stored in URL query params (?sort=score&dir=desc) for shareability
- Default sort: score DESC (highest conviction first)

### Filtering
- Client-side (300ms SLA from PRD)
- State in URL query params for shareability
- Applied as AND logic across all active filters
- Category panel click sets the category filter (same state)

### Detail Drawer
- Opens on row click; desktop = right drawer (384px wide); mobile = full-screen
- URL updates to /?candidate=BTC for deep-linking
- Escape or click-outside closes; table scroll position preserved (use ScrollRestoration or manual scrollY save)
- Tab trapping inside open drawer for accessibility

### Disclaimer Modal
- Shown if `sessionStorage.getItem('disclaimer-acknowledged')` is null
- No X button — user must click "I understand"
- Sets sessionStorage on dismiss (not localStorage — re-shows each session intentionally per legal requirement interpretation; confirm with legal)
- Trap focus inside modal while open

## Phase 2 Extension Slots

### In DashboardLayout.tsx
- Add `assetClassTabs` slot above CategoryPanel for "All / Crypto / Equities" tab switcher
- Add `watchlistPanel` slot below CategoryPanel (collapsible, initially hidden)

### In CandidatesTable.tsx
- Add `assetClass` column (hidden in Phase 1, shown in Phase 2 when mixed)
- Add `sector` column alias for `category` to work with GICS sectors

### In CandidateDetailDrawer.tsx
- Add `FundamentalsSection` component slot (Phase 2 equities: revenue growth, D/E ratio)
- Add `InsiderSignalSection` slot (Phase 2 equities: Form 4 filings)
- Add `WatchlistButton` slot in DrawerHeader (Phase 2: requires auth)

### In Header.tsx
- Add `AuthButton` slot (Phase 2: Login / Sign Up)
- Add `NotificationBell` slot (Phase 2: alerts)

### New routes for Phase 2
- `/account` — user account management
- `/watchlist` — saved candidates
- `/history` — historical pipeline runs
- `/admin` — pipeline monitoring (internal)
