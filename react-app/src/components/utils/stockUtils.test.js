import { fixMarketCap, formatPercent } from './stockUtils';

test('fixMarketCap picks the right unit', () => {
  expect(fixMarketCap(2.41e12)).toBe('2.41T');
  expect(fixMarketCap(1e12)).toBe('1.00T');
  expect(fixMarketCap(310.5e6)).toBe('310.50M');
  expect(fixMarketCap(999)).toBe('999.00');
});

test('formatPercent signs and rounds', () => {
  expect(formatPercent(1.234)).toBe('+1.23%');
  expect(formatPercent(-0.5)).toBe('-0.50%');
  expect(formatPercent(0)).toBe('0.00%');
  expect(formatPercent(undefined)).toBe('');
});
