import test from 'node:test';
import assert from 'node:assert/strict';
import { isValidObservedPeriod } from '../src/earlyWarningDates.ts';

test('accepts real monthly commodity source periods', () => {
  assert.equal(isValidObservedPeriod('2026-10'), true);
  assert.equal(isValidObservedPeriod('2026-09'), true);
});

test('accepts daily NY Fed and OpenSSF source dates', () => {
  assert.equal(isValidObservedPeriod('2026-11-17'), true);
  assert.equal(isValidObservedPeriod('2026-11-18'), true);
  assert.equal(isValidObservedPeriod('2024-02-29'), true);
});

test('rejects malformed periods rather than hiding source readings', () => {
  for (const value of ['2026-13', '2026-00', '2026-11-32', '2026-02-29', '2026-11-17T00:00', '', 'not-known']) {
    assert.equal(isValidObservedPeriod(value), false, value);
  }
});
