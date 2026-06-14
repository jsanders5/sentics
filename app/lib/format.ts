export function formatPrice(price?: number | null): string {
  if (price === null || price === undefined || typeof price !== "number" || price <= 0) {
    return "N/A";
  }
  // Decimal precision scales with magnitude so trade-plan levels remain
  // distinguishable for low-priced assets (e.g. a ~$1 coin needs >2 decimals
  // or entry/stop collapse to the same displayed value).
  let decimals: number;
  if (price >= 1000) decimals = 2;
  else if (price >= 1) decimals = 4;
  else if (price >= 0.01) decimals = 6;
  else decimals = 8;
  return `$${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: decimals })}`;
}

export function formatMarketCap(cap?: number | null): string {
  if (!cap || cap <= 0) return "N/A";
  if (cap >= 1e12) return `$${(cap / 1e12).toLocaleString("en-US", { maximumFractionDigits: 2 })}T`;
  if (cap >= 1e9) return `$${(cap / 1e9).toLocaleString("en-US", { maximumFractionDigits: 2 })}B`;
  if (cap >= 1e6) return `$${(cap / 1e6).toLocaleString("en-US", { maximumFractionDigits: 2 })}M`;
  return `$${cap.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}
