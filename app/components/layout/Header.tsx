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
      <header className="sticky top-0 z-40 border-b border-[--border] bg-[--bg-base]/95 backdrop-blur-sm px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-baseline gap-1.5">
              <h1 className="font-sans text-2xl font-bold bg-gradient-to-r from-[--accent] to-[--medium-h] bg-clip-text text-transparent">
                Sentics
              </h1>
              <span className="text-xs font-semibold uppercase tracking-widest text-[--text-secondary]">
                STI
              </span>
            </div>
            <div className="w-px h-6 bg-[--border]" />
            <span className="text-sm font-medium text-[--text-secondary]">
              Trading Intelligence
            </span>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-xs text-[--text-muted]">
              <div className="w-2 h-2 rounded-full bg-[--high] animate-pulse" />
              <span>Last update: {time} UTC</span>
              {hoursAgo > 0 && <span className="text-[--text-secondary]">• {hoursAgo}h ago</span>}
            </div>
            <button
              onClick={() => setShowDisclaimer(true)}
              className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary] hover:text-[--accent] transition-smooth px-3 py-1.5 rounded-md hover:bg-[--bg-surface]"
            >
              Disclaimer
            </button>
          </div>
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
