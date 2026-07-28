"use client";

import { ErrorBoundary } from "@/app/components/ErrorBoundary";
import { Header } from "@/app/components/layout/Header";
import { METRICS, MetricGroup } from "@/app/lib/metrics";

const GROUP_ORDER: MetricGroup[] = ["Technical", "Trade levels", "Social", "Market"];
const GROUP_BLURB: Record<MetricGroup, string> = {
  Technical: "Derived by Sentics from price/volume history. Descriptions of the indicators — not forecasts or advice.",
  "Trade levels": "Illustrative levels from recent price structure. Not predictions, recommendations, or advice.",
  Social: "From LunarCrush. Descriptive context on the crypto conversation — noisy, often lagging, and gameable.",
  Market: "Reference market data from CoinGecko.",
};

export default function GlossaryPage() {
  return (
    <ErrorBoundary>
      <div className="flex h-screen flex-col" style={{ backgroundColor: "var(--bg-base)" }}>
        <Header />
        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="w-full max-w-3xl mx-auto flex flex-col flex-1 overflow-y-auto p-4 md:p-6">
            <h2 className="text-lg font-bold text-[--text-primary]">Glossary</h2>
            <p className="text-xs leading-snug mt-1 mb-2" style={{ color: "var(--text-muted)" }}>
              What every number on Sentics means, where it comes from, and its limits. Sentics is a
              technical + social <span className="font-semibold">screener</span> — these are descriptive
              readings, <span className="font-semibold">not trade signals or advice</span>.
            </p>

            {GROUP_ORDER.map((group) => {
              const items = METRICS.filter((m) => m.group === group);
              if (items.length === 0) return null;
              return (
                <section key={group} className="mt-6">
                  <h3 className="text-sm font-semibold text-[--text-primary]">{group}</h3>
                  <p className="text-xs italic mb-3" style={{ color: "var(--text-muted)" }}>{GROUP_BLURB[group]}</p>
                  <div className="space-y-3">
                    {items.map((m) => (
                      <div
                        key={m.key}
                        className="rounded-lg border p-3"
                        style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}
                      >
                        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                          <span className="font-semibold text-[--text-primary]">{m.label}</span>
                          {m.scale && (
                            <span className="font-mono text-[11px] text-[--text-secondary]">{m.scale}</span>
                          )}
                          <span
                            className="ml-auto rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wider"
                            style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
                          >
                            {m.source}
                          </span>
                        </div>
                        <p className="text-sm leading-relaxed text-[--text-secondary] mt-1.5">{m.full}</p>
                        {m.caveat && (
                          <p className="text-xs italic mt-1.5" style={{ color: "var(--stale)" }}>
                            ⚠ {m.caveat}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              );
            })}

            <p className="text-[11px] italic mt-8 mb-2" style={{ color: "var(--text-muted)" }}>
              Educational analysis only — not financial advice. Sentics is not a registered investment
              adviser or broker-dealer.
            </p>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
