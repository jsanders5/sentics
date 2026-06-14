export function formatPrice(price?: number | null): string {
  if (price === null || price === undefined || typeof price !== "number" || price <= 0) {
    return "N/A";
  }
  if (price >= 1) {
    return `$${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return `$${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`;
}

export function formatMarketCap(cap?: number | null): string {
  if (!cap || cap <= 0) return "N/A";
  if (cap >= 1e12) return `$${(cap / 1e12).toLocaleString("en-US", { maximumFractionDigits: 2 })}T`;
  if (cap >= 1e9) return `$${(cap / 1e9).toLocaleString("en-US", { maximumFractionDigits: 2 })}B`;
  if (cap >= 1e6) return `$${(cap / 1e6).toLocaleString("en-US", { maximumFractionDigits: 2 })}M`;
  return `$${cap.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}
