import { MapProvider } from 'react-map-gl/maplibre';
import { MapComponent } from './components/map';
import { RoutePlanner } from './components/route-planner';
import { SettingsPanel } from './components/settings-panel/settings-panel';
import { CompliancePanel } from './components/compliance-panel';
import { Toaster } from '@/components/ui/sonner';

export const App = () => {
  return (
    <MapProvider>
      <div className="flex h-screen w-screen overflow-hidden">

        {/* Existing Valhalla area */}
        <div className="relative min-w-0 flex-1">
          <MapComponent />
          <RoutePlanner />
          <SettingsPanel />
        </div>

        {/* New HeavyRoute area */}
        <CompliancePanel />

      </div>

      <Toaster
        position="bottom-center"
        duration={5000}
        richColors
      />
    </MapProvider>
  );
};