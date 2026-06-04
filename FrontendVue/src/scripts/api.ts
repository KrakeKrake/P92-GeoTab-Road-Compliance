// Gather from the API.
import type { wayPoint } from "./route";
export type { wayPoint } from "./route"; // re-export so Mapping.vue can import from here

async function getRoute(
  osm_id_1: number,
  osm_id_2: number,
): Promise<wayPoint[]> {
  const response = await fetch(
    `/api/route?osm_id_1=${osm_id_1}&osm_id_2=${osm_id_2}`,
  );
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.error ?? `Request failed: ${response.status}`);
  }
  const data = (await response.json()) as wayPoint[];
  console.log("Received response", data);
  return data;
}

function get_geo(route: wayPoint[]): [number, number][] {
  const geos: [number, number][] = [];
  for (const wp of route) {
    // geo_start and geo_end are [lng, lat] pairs — push both endpoints of each edge
    geos.push([wp.geo_start[0], wp.geo_start[1]]);
    geos.push([wp.geo_end[0], wp.geo_end[1]]);
  }
  return geos;
}

export { getRoute };
export { get_geo };
