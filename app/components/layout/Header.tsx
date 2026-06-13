"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface HeaderProps {
  timestamp?: string | null;
}

function formatTime(isoString?: string | null): string {
  if (!isoString) return "—";
  const date = new Date(isoString);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

const navLinks = [
  { href: "/", label: "Dashboard" },
];

export function Header({ timestamp }: HeaderProps) {
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const pathname = usePathname();
  const time = formatTime(timestamp);

  return (
    <>
      <header
        className="sticky top-0 z-40"
        style={{ backgroundColor: 'var(--bg-base)', borderBottom: '1px solid var(--border)', boxShadow: '0 4px 20px rgba(0,0,0,0.3)' }}
      >
        {/* Top bar: branding + actions */}
        <div className="flex items-center justify-between px-4 md:px-8 py-3 md:py-4">
          <div className="flex items-center gap-3 md:gap-4">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight" style={{ color: 'var(--accent)' }}>
              Sentics
            </h1>
            <div className="hidden md:block w-px h-8" style={{ backgroundColor: 'var(--border)' }} />
            <p className="hidden md:block text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-secondary)' }}>
              AI Trading Intelligence
            </p>
          </div>

          <div className="flex items-center gap-3 md:gap-4">
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: 'var(--high)' }} />
              <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                {time} UTC
              </span>
            </div>
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
                <p>This platform provides analysis for educational purposes only. It should not be construed as investment advice, a recommendation to buy or sell any security, or an offer of services.</p>
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
