"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { formatAgo, isStale } from "@/app/lib/freshness";

interface HeaderProps {
  timestamp?: string | null;
  onRefresh?: () => void;
  refreshing?: boolean;
}

const navLinks = [
  { href: "/", label: "Dashboard" },
  { href: "/trending", label: "Trending" },
];

export function Header({ timestamp, onRefresh, refreshing }: HeaderProps) {
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const pathname = usePathname();
  const stale = isStale(timestamp);
  const freshness = formatAgo(timestamp);

  return (
    <>
      <header
        className="sticky top-0 z-40"
        style={{
          backgroundColor: 'rgba(10, 14, 39, 0.72)',
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          borderBottom: '1px solid var(--border)',
        }}
      >
        {/* Top bar: branding + actions */}
        <div className="flex items-center justify-between px-4 md:px-8 py-3 md:py-4">
          <div className="flex items-center gap-3 md:gap-4">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight" style={{ color: 'var(--accent)' }}>
              Sentics
            </h1>
            <div className="hidden md:block w-px h-8" style={{ backgroundColor: 'var(--border)' }} />
            <p className="hidden md:block text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-secondary)' }}>
              Technical Screener · Top 25
            </p>
          </div>

          <div className="flex items-center gap-3 md:gap-4">
            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full border"
              style={{
                backgroundColor: stale ? 'var(--stale-bg)' : 'var(--bg-surface)',
                borderColor: stale ? 'var(--stale-border)' : 'var(--border)',
              }}
              title={stale ? "Data is stale — pipeline runs once daily at 15:00 UTC" : "Pipeline runs once daily at 15:00 UTC"}
            >
              <div
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: stale ? 'var(--stale)' : 'var(--text-muted)' }}
              />
              <span
                className="text-xs font-medium whitespace-nowrap"
                style={{ color: stale ? 'var(--stale)' : 'var(--text-muted)' }}
              >
                {freshness}
              </span>
            </div>
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={refreshing}
                title="Re-run the analysis pipeline"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold text-xs uppercase tracking-wider hover:border-[--accent] transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                style={{ backgroundColor: 'var(--bg-surface)', color: 'var(--accent)', border: '1px solid var(--border)' }}
              >
                <span className={refreshing ? "inline-block animate-spin" : "inline-block"} aria-hidden>↻</span>
                <span className="hidden sm:inline">{refreshing ? "Running…" : "Refresh"}</span>
              </button>
            )}
            <button
              onClick={() => setShowDisclaimer(true)}
              className="px-3 py-1.5 rounded-lg font-semibold text-xs uppercase tracking-wider hover:opacity-80 transition-all"
              style={{ backgroundColor: 'var(--bg-surface)', color: 'var(--accent)', border: '1px solid var(--border)' }}
            >
              Disclaimer
            </button>
          </div>
        </div>

        {/* Nav bar */}
        <div className="flex items-center gap-1 px-4 md:px-8 pb-0" style={{ borderTop: '1px solid var(--border)' }}>
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className="relative px-3 py-2.5 text-sm font-medium transition-colors"
                style={{ color: isActive ? 'var(--accent)' : 'var(--text-secondary)' }}
              >
                {link.label}
                {isActive && (
                  <span
                    className="absolute bottom-0 left-0 right-0 h-0.5 rounded-t"
                    style={{ backgroundColor: 'var(--accent)' }}
                  />
                )}
              </Link>
            );
          })}
        </div>
      </header>

      {showDisclaimer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div
            className="max-w-2xl w-full rounded-xl border p-8 max-h-[80vh] overflow-y-auto shadow-lg"
            style={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border)' }}
          >
            <h2 className="text-2xl font-bold mb-6" style={{ color: 'var(--text-primary)' }}>Trading Disclaimer</h2>
            <div className="space-y-5 text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              <div>
                <p className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Not Investment Advice</p>
                <p>Sentics is not a registered investment adviser, broker-dealer, or commodity trading advisor, and nothing here is personalized to you. All analysis, directional readings, scores, and trade-plan levels are general, automated, educational information published identically to all users — not a recommendation, solicitation, or offer to buy, sell, or hold any crypto asset or security. You are solely responsible for your own decisions.</p>
              </div>
              <div>
                <p className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Trade-Plan Levels</p>
                <p>Entry, target, and stop levels are illustrative outputs of an automated technical model based on past price data. They are not predictions or price targets, carry no warranty of accuracy, and frequently fail. They do not account for your financial situation, objectives, or risk tolerance.</p>
              </div>
              <div>
                <p className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Short Selling</p>
                <p>Where a &ldquo;short&rdquo; framing is shown, be aware that short selling carries risk of unlimited loss, requires margin or derivatives on a third-party venue, and exposes you to borrow costs, funding rates, margin calls, and forced liquidation. Sentics offers no derivatives and executes nothing.</p>
              </div>
              <div>
                <p className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Regulatory Status of Crypto Assets</p>
                <p>The legal classification of many crypto assets is unsettled, and some may be deemed securities by regulators or courts. This may affect their availability, value, and legality in your jurisdiction.</p>
              </div>
              <div>
                <p className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Market Risk</p>
                <p>Cryptocurrency markets are highly volatile and speculative. All investments carry risk, including loss of principal. Past performance does not guarantee future results.</p>
              </div>
              <div>
                <p className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>AI-Generated Content</p>
                <p>Rationales are generated using AI and may contain inaccuracies. Always conduct independent research before making any investment decisions.</p>
              </div>
              <div>
                <p className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Meme Coins</p>
                <p>Analysis of meme coins includes elevated risk of manipulation and loss. These are speculative and not recommended for risk-averse investors.</p>
              </div>
              <div className="pt-2" style={{ borderTop: '1px solid var(--border)' }}>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  We make no warranties about the accuracy, timeliness, or completeness of any information provided.
                </p>
              </div>
            </div>
            <div className="mt-8">
              <button
                onClick={() => setShowDisclaimer(false)}
                className="w-full rounded-lg px-4 py-3 font-semibold text-white hover:opacity-90 transition-opacity"
                style={{ backgroundColor: 'var(--accent)' }}
              >
                I Understand
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
