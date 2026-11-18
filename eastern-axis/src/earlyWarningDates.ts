/**
 * Monthly commodity vintages (YYYY-MM) and daily funding/OSS observations
 * (YYYY-MM-DD) must both pass. A missing/invalid date never becomes zero.
 */
export function isValidObservedPeriod(value: string): boolean {
  if (typeof value !== 'string') return false;
  const short = /^(\d{4})-(\d{2})$/.exec(value);
  if (short) {
    const year = Number(short[1]), month = Number(short[2]);
    return year >= 1950 && year <= 2200 && month >= 1 && month <= 12;
  }
  const full = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!full) return false;
  const year = Number(full[1]), month = Number(full[2]), day = Number(full[3]);
  if (year < 1950 || year > 2200 || month < 1 || month > 12 || day < 1 || day > 31) return false;
  const parsed = new Date(Date.UTC(year, month - 1, day));
  return parsed.getUTCFullYear() === year &&
    parsed.getUTCMonth() + 1 === month && parsed.getUTCDate() === day;
}
