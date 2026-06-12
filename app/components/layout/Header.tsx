"use client";

import { useState } from "react";

interface HeaderProps {
  timestamp?: string | null;
}

function formatTime(isoString?: string | null): string {
  if (!isoString) return "Unknown";
  const date = new Date(isoString);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function getHoursAgo(isoString?: string | null): number {
  if (!isoString) return 0;
  const date = new Date(isoString);
  const now = new Date();
  return Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
}

export function Header({ timestamp }: HeaderProps) {
  const [showDisclaimer, setShowDisclaimer] = useState(false);

  const time = formatTime(timestamp);
  const hoursAgo = getHoursAgo(timestamp);

  return (
    <>
      <header
        style={{
          backgroundColor: 'var(--bg-base)',
          borderBottom: '1px solid var(--border)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
        }}
        className="sticky top-0 z-40 px-8 py-6"
      >
        <div className="flex items-center justify-between">
          {/* Left side - Logo and branding */}
          <div className="flex items-center gap-4">
            <div className="flex flex-col gap-1">
              <h1
                style={{ color: 'var(--accent)' }}
                className="text-3xl font-bold tracking-tight"
              >
                Sentics
              </h1>
              <p style={{ color: 'var(--text-secondary)' }} className="text-xs font-semibold uppercase tracking-widest">
                AI Trading Intelligence
              </p>
            </div>
            <div style={{ backgroundColor: 'var(--border)' }} className="w-px h-12" />
            <div className="flex flex-col gap-0.5">
              <p style={{ color: 'var(--text-muted)' }} className="text-xs uppercase tracking-wider">Live Analysis</p>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: 'var(--high)' }} />
                <span style={{ color: 'var(--text-secondary)' }} className="text-xs font-medium">
                  {time} UTC
                </span>
              </div>
            </div>
          </div>

          {/* Right side - Actions */}
          <button
            onClick={() => setShowDisclaimer(true)}
            style={{
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--accent)',
              border: '1px solid var(--border)'
            }}
            className="px-4 py-2 rounded-lg font-semibold text-sm uppercase tracking-wider hover:opacity-80 transition-all"
          >
            Disclaimer
          </button>
        </div>
      </header>

      {showDisclaimer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="max-w-2xl rounded-xl bg-[--bg-surface] border border-[--border] p-8 max-h-[80vh] overflow-y-auto shadow-lg">
            <h2 className="text-2xl font-bold mb-6 text-[--text-primary]">Trading Disclaimer</h2>
            <div className="space-y-5 text-sm text-[--text-secondary] leading-relaxed">
              <div>
                <p className="font-semibold text-[--text-primary] mb-2">Not Investment Advice</p>
                <p>
                  This platform provides analysis for educational purposes only. It should not be construed as investment advice, a recommendation to buy or sell any security, or an offer of services.
                </p>
              </div>
              <div>
                <p className="font-semibold text-[--text-primary] mb-2">Market Risk</p>
                <p>
                  Cryptocurrency markets are highly volatile and speculative. All investments carry risk, including loss of principal. Past performance does not guarantee future results.
                </p>
              </div>
              <div>
                <p className="font-semibold text-[--text-primary] mb-2">AI-Generated Content</p>
                <p>
                  Rationales are generated using AI and may contain inaccuracies. Always conduct independent research before making any investment decisions.
                </p>
              </div>
              <div>
                <p className="font-semibold text-[--text-primary] mb-2">Meme Coins</p>
                <p>
                  Analysis of meme coins includes elevated risk of manipulation and loss. These are speculative and not recommended for risk-averse investors.
                </p>
              </div>
              <div className="pt-2 border-t border-[--border]">
                <p className="text-xs text-[--text-muted]">
                  We make no warranties about the accuracy, timeliness, or completeness of any information provided.
                </p>
              </div>
            </div>
            <div className="mt-8 flex gap-3">
              <button
                onClick={() => setShowDisclaimer(false)}
                className="flex-1 rounded-lg bg-[--accent] px-4 py-3 font-semibold text-white hover:opacity-90 transition-smooth"
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
