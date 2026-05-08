import psycopg as postgres


DB_URL = "eat40005.krakekrake.me"
DB_NAME = "o2p"
DB_USER = "o2p"
DB_PASSWORD = "o2p"

conn = postgres.connect(
    host=DB_URL,
    user=DB_USER,
    password=DB_PASSWORD
)
print(conn)
print("Connected!")

def lookup_id_from_osm_id(id):
    cur = conn.cursor()
    cur.execute("""
        SELECT source, target FROM ways WHERE osm_id = %s
    """, (id,))
    result = cur.fetchone()
    cur.close()
    return result[0] if result else None

def closest_point(long, lat) -> int:
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM ways
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        LIMIT 1;""", (long, lat))
    result = cur.fetchone()
    cur.close()
    if result is None:
        return -1
    return result[0]

def create_route(id_1, id_2):
    cur = conn.cursor()
    cur.execute("""
        SELECT seq, route.node, route.edge, ways.osm_id, ways.name, route.cost FROM pgr_astar(
        'SELECT id, source, target, cost, reverse_cost, x1, y1, x2, y2 FROM ways', 
        %s, %s, 
        directed => false
        ) AS route JOIN ways ON route.edge = ways.id ORDER BY seq
    """, (id_1, id_2))
    result = cur.fetchall()
    cur.close()
    return result

def get_road_info(id):
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM ways WHERE id = %s
    """, (id,))
    result = cur.fetchone()
    cur.close()
    return result

def structure_route_as_dict(route):
    result = []
    for index, row in enumerate(route):
        result.append({
            "seq": row[0],
            "osm_id": row[3],
            "name": row[4],
            "cost": row[5],
        })
    return result

def route_info(route):
    for row in route:
        print(f"{row['seq']}. Name: {row['name']}, OSM ID: {row['osm_id']}, Cost: {row['cost']}")

def test():
    # point_1 = closest_point(145.041465, -37.823449)
    # print(point_1)
    # point_2 = closest_point(145.048146, -37.824105)
    # print(point_2)
    route = structure_route_as_dict(create_route(82662, 61407))
    route_info(route)

print(lookup_id_from_osm_id(4080213))

test()

