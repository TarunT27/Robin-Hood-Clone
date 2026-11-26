// Formats a dollar amount in short form, like 2.41T or 310.50M.
export const fixMarketCap = marketCap => {
  const units = [
    [1e12, 'T'],
    [1e9, 'B'],
    [1e6, 'M'],
    [1e3, 'K'],
  ];
  for (const [size, unit] of units) {
    if (marketCap >= size) return (marketCap / size).toFixed(2) + unit;
  }
  return marketCap.toFixed(2);
};

// Formats a percent change like +1.23% or -0.50%.
export const formatPercent = value => {
  if (typeof value !== 'number' || Number.isNaN(value)) return '';
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
};
