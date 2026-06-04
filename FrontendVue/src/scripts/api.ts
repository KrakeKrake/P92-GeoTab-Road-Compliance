// Gather from the API.
import type { wayPoint } from "./route";
export type { wayPoint } from "./route"; // re-export so Mapping.vue can import from here

async function getRoute(osm_id_1: number, osm_id_2: number): Promise<wayPoint[]> {
  const response = await fetch(
    `/api/route?osm_id_1=${osm_id_1}&osm_id_2=${osm_id_2}`,
  );
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.error ?? `Request failed: ${response.status}`);
  }
  const data = await response.json() as wayPoint[];
  console.log("Received response", data);
  return data;
}

async function get_geo(route: wayPoint[]): Promise<[number, number][]> {
  const geos: [number, number][] = [];
  for (const wayPoint of route) {
    geos.push([wayPoint.geo_start, wayPoint.geo_end]);
  }
  return geos;
}

export { getRoute };
export { get_geo };