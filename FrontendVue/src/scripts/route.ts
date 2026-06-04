export interface wayPoint {
  seq: number;
  node_id: number;
  edge_id: number;
  osm_id: number;
  name: string;
  cost: number;
  tag_id: number;
  geo_start: [number, number];
  geo_end: [number, number];
  restrictions: Restriction;
}
// "restrictions":[107024,198994037,13,"Approved with Conditions","<p><p>Conditionally Approved - Williamstown Road&nbsp;no-truck zone&nbsp;applies from 8pm to 6am, weekdays, and from 8pm Friday until 6am Monday, for ALL TRUCKS. Enforcement begins only when WGT opens.&nbsp;</p></p>","Williamstown Road","Department of Transport and Planning   "]
export interface Restriction {
  id: number;
  route_id: number;
  randomNumber: number;
  type: string;
  description: string;
}
// {
//     # Below is what route gets
//     # (121, 166319, 776012, 485235230, 'Francis Street', 0.00011368289933051796, 108)
//     "seq": row[0],
//     "node_id": row[1],
//     "edge_id": row[2],
//     "osm_id": row[3],
//     "name": row[4],
//     "cost": row[5],
//     "tag_id": row[6],
//     "geo_start": geo[0][0],
//     "geo_end": geo[1][0],
// }