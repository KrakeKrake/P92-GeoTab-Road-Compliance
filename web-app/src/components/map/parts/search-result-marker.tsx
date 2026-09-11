import { useState, useEffect } from 'react';
import { Marker, Popup } from 'react-map-gl/maplibre';
import { X } from 'lucide-react';
import { useCommonStore } from '@/stores/common-store';

export const SearchResultMarker = () => {
  const searchResult = useCommonStore((s) => s.searchResult);
  const setSearchResult = useCommonStore((s) => s.setSearchResult);
  const [popupOpen, setPopupOpen] = useState(true);

  // Re-open popup whenever a new result is selected
  useEffect(() => {
    if (searchResult) setPopupOpen(true);
  }, [searchResult]);

  if (!searchResult) return null;

  const { lng, lat, name } = searchResult;
  const lines = name.split(',').map((s) => s.trim()).filter(Boolean);
  const title = lines[0] ?? name;
  const subtitle = lines.slice(1, 3).join(', ');

  return (
    <>
      <Marker
        longitude={lng}
        latitude={lat}
        onClick={() => setPopupOpen(true)}
        style={{ cursor: 'pointer' }}
      >
        {/* Red teardrop pin */}
        <div className="flex flex-col items-center">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-red-500 shadow-lg ring-2 ring-white">
            <div className="h-2.5 w-2.5 rounded-full bg-white" />
          </div>
          <div className="h-3 w-0.5 bg-red-500" />
        </div>
      </Marker>

      {popupOpen && (
        <Popup
          longitude={lng}
          latitude={lat}
          closeButton={false}
          offset={48}
          maxWidth="260px"
          onClose={() => setPopupOpen(false)}
        >
          <div className="min-w-[180px] p-2">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold leading-snug text-gray-900">
                  {title}
                </p>
                {subtitle && (
                  <p className="mt-0.5 text-xs leading-snug text-gray-500">
                    {subtitle}
                  </p>
                )}
              </div>
              <button
                onClick={() => setSearchResult(null)}
                className="shrink-0 text-gray-400 hover:text-gray-600"
                aria-label="Dismiss"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </Popup>
      )}
    </>
  );
};
