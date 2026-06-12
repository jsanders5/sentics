"use client";

import { useState } from "react";

interface HeaderProps {
  timestamp?: string;
}

function formatTime(isoString?: string): string {
  if (!isoString) return "Unknown";
  const date = new Date(isoString);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function getHoursAgo(isoString?: string): number {
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
      <header className="border-b border-[--border] bg-[--bg-base] px-6 py-3">
        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline gap-2">
            <h1 className="font-sans text-xl font-semibold text-[--text-primary]">Sentics</h1>
            <span className="text-sm text-[--text-secondary]">Trading Intelligence</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-[--text-muted]">
              Data as of {time} UTC · {hoursAgo}h ago
            </span>
            <button
              onClick={() => setShowDisclaimer(true)}
              className="text-sm font-medium text-[--accent] hover:opacity-80 transition-opacity"
            >
              Disclaimer
            </button>
          </div>
        </div>
      </header>

      {showDisclaimer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <div className="max-w-2xl rounded-lg bg-[--bg-surface] border border-[--border] p-6 max-h-[80vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4 text-[--text-primary]">Disclaimer</h2>
            <div className="space-y-4 text-sm text-[--text-secondary]">
              <p>
                <strong>Not Investment Advice:</strong> This platform provides analysis for educational
                purposes only. It should not be construed as investment advice, a recommendation to buy or
                sell any security, or an offer of services.
              </p>
              <p>
                <strong>Market Risk:</strong> Cryptocurrency markets are highly volatile and speculative.
                All investments carry risk, including loss of principal. Past performance does not guarantee
                future results.
              </p>
              <p>
                <strong>AI-Generated Content:</strong> Rationales are generated using AI and may contain
                inaccuracies. Always conduct independent research before making any investment decisions.
              </p>
              <p>
                <strong>Meme Coins:</strong> Analysis of meme coins includes elevated risk of manipulation and
                loss. These are speculative and not recommended for risk-averse investors.
              </p>
              <p>
                <strong>No Warranty:</strong> We make no warranties about the accuracy, timeliness, or
                completeness of any information provided.
              </p>
            </div>
            <div className="mt-6 flex gap-2">
              <button
                onClick={() => setShowDisclaimer(false)}
                className="flex-1 rounded-lg bg-[--accent] px-4 py-2 font-semibold text-white hover:opacity-90 transition-opacity"
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
