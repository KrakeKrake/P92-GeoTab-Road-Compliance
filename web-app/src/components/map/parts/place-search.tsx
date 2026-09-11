import { useState, useRef, useEffect } from 'react';
import { Search, X, MapPin, Loader2 } from 'lucide-react';
import { useCommonStore } from '@/stores/common-store';
import { useNavigationStore } from '@/stores/navigation-store';
import { NOMINATIM_URL } from '@/utils/nominatim';

interface NominatimResult {
  place_id: number;
  display_name: string;
  name: string;
  lat: string;
  lon: string;
}

const VIEWBOX_HALF = 0.5; // ~55 km radius

export const PlaceSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<NominatimResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const zoomTo = useCommonStore((s) => s.zoomTo);
  const setSearchResult = useCommonStore((s) => s.setSearchResult);
  const searchResult = useCommonStore((s) => s.searchResult);
  const isNavigating = useNavigationStore((s) => s.isNavigating);

  const userPosRef = useRef<{ lat: number; lng: number } | null>(null);
  const reqIdRef = useRef(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Grab user location once on mount to bias search results
  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        userPosRef.current = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      },
      () => { /* denied — no bias */ },
      { timeout: 5000, maximumAge: 60_000 }
    );
  }, []);

  // Fire search whenever query changes, debounced 150 ms
  useEffect(() => {
    if (query.trim().length === 0) {
      setResults([]);
      setIsOpen(false);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    const id = ++reqIdRef.current;

    const timer = setTimeout(async () => {
      try {
        const params = new URLSearchParams({
          q: query,
          format: 'json',
          limit: '6',
          countrycodes: 'au',
          addressdetails: '0',
        });

        if (userPosRef.current) {
          const { lat, lng } = userPosRef.current;
          params.set(
            'viewbox',
            `${lng - VIEWBOX_HALF},${lat + VIEWBOX_HALF},${lng + VIEWBOX_HALF},${lat - VIEWBOX_HALF}`
          );
          params.set('bounded', '0');
        }

        const res = await fetch(`${NOMINATIM_URL}?${params}`);
        if (id !== reqIdRef.current) return; // stale — a newer request is in flight
        if (!res.ok) { setIsLoading(false); return; }

        const data: NominatimResult[] = await res.json();
        if (id !== reqIdRef.current) return;

        setResults(data);
        setIsOpen(data.length > 0);
      } catch {
        if (id === reqIdRef.current) setResults([]);
      } finally {
        if (id === reqIdRef.current) setIsLoading(false);
      }
    }, 150);

    return () => clearTimeout(timer);
  }, [query]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelect = (result: NominatimResult) => {
    const lng = parseFloat(result.lon);
    const lat = parseFloat(result.lat);
    const shortName = result.name || result.display_name.split(',')[0] || result.display_name;
    setQuery(shortName);
    setIsOpen(false);
    setSearchResult({ lng, lat, name: result.display_name });
    const d = 0.002;
    zoomTo([[lat - d, lng - d], [lat + d, lng + d]]);
  };

  const handleClear = () => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
    setSearchResult(null);
    inputRef.current?.focus();
  };

  if (isNavigating) return null;

  return (
    <div ref={containerRef} className="absolute left-4 top-4 z-40 w-80 max-w-[calc(100vw-2rem)]">
      <div className="flex items-center gap-2 rounded-full bg-white px-4 py-2.5 shadow-lg">
        {isLoading ? (
          <Loader2 className="h-4 w-4 shrink-0 animate-spin text-gray-400" />
        ) : (
          <Search className="h-4 w-4 shrink-0 text-gray-400" />
        )}
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setIsOpen(true)}
          placeholder="Search places..."
          className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-gray-400"
        />
        {(query || searchResult) && (
          <button onClick={handleClear} className="shrink-0 text-gray-400 hover:text-gray-600" aria-label="Clear">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="mt-1.5 overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-xl">
          {results.map((r, i) => {
            const primary = r.name || r.display_name.split(',')[0] || r.display_name;
            return (
              <button
                key={r.place_id}
                onClick={() => handleSelect(r)}
                className={`flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-gray-50 ${
                  i < results.length - 1 ? 'border-b border-gray-50' : ''
                }`}
              >
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-gray-900">{primary}</p>
                  <p className="truncate text-xs text-gray-500">{r.display_name}</p>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
