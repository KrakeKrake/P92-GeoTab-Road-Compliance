import { describe, expect, it } from 'vitest';
import { normalizeAccess } from './use-network-access-query';

describe('normalizeAccess', () => {
  it('maps the API access_code strings', () => {
    expect(normalizeAccess('Approved')).toBe('allowed');
    expect(normalizeAccess('Approved with Conditions')).toBe('conditional');
    expect(normalizeAccess('Restricted')).toBe('restricted');
  });

  it('accepts the numeric form', () => {
    expect(normalizeAccess(0)).toBe('allowed');
    expect(normalizeAccess(1)).toBe('conditional');
    expect(normalizeAccess(2)).toBe('restricted');
  });
});
