import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchNhvrNetworks } from './use-nhvr-networks-query';

function mockFetch(body: unknown, ok = true) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok,
    json: async () => body,
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

describe('fetchNhvrNetworks', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns the network names reported by the API', async () => {
    const fetchMock = mockFetch({
      networks: ['B_DOUBLE', '28361546'],
    });

    await expect(fetchNhvrNetworks()).resolves.toEqual([
      'B_DOUBLE',
      '28361546',
    ]);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/nhvr-access\/networks$/)
    );
  });

  it('ignores malformed entries', async () => {
    mockFetch({ networks: ['B_DOUBLE', 42, '', null] });

    await expect(fetchNhvrNetworks()).resolves.toEqual(['B_DOUBLE']);
  });

  it('returns an empty list when the response has no networks field', async () => {
    mockFetch({});

    await expect(fetchNhvrNetworks()).resolves.toEqual([]);
  });

  it('throws when the API request fails', async () => {
    mockFetch({}, false);

    await expect(fetchNhvrNetworks()).rejects.toThrow(
      'Could not fetch NHVR networks'
    );
  });
});
