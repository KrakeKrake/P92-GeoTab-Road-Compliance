import psycopg as postgres

DB_URL = "eat40005.krakekrake.me"
DB_NAME = "o2p"
DB_USER = "o2p"
DB_PASSWORD = "lU0pgj9up@vty1B#plVA"

conn = postgres.connect(
    host=DB_URL, user=DB_USER, password=DB_PASSWORD, autocommit=True
)

print(conn)
print("Connected!")


def lookup_id_from_osm_id(id):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source, target FROM ways WHERE osm_id = %s
    """,
        (id,),
    )
    result = cur.fetchone()
    cur.close()
    return result[0] if result else None


def closest_point(long, lat) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM ways
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        LIMIT 1;""",
        (long, lat),
    )
    result = cur.fetchone()
    cur.close()
    if result is None:
        return -1
    return result[0]

    # Direct from adminer.


# tag_id	tag_key	tag_value	way_count
# 101	highway	motorway	3965
# 102	highway	motorway_link	4319
# 104	highway	trunk	27138
# 105	highway	trunk_link	2057
# 106	highway	primary	47148
# 107	highway	primary_link	3164
# 108	highway	secondary	60216
# 109	highway	secondary_link	2127
# 110	highway	tertiary	123219
# 111	highway	tertiary_link	2644
# 112	highway	residential	475413
# 113	highway	living_street	1442
# 114	highway	service	267085
# 117	highway	unclassified	128840


def lookup_end_id_from_osm_id(osm_id):
    # Returns the TARGET of the LAST segment for an OSM way.
    cur = conn.cursor()
    cur.execute(
        "SELECT target FROM ways WHERE osm_id = %s ORDER BY id DESC LIMIT 1",
        (osm_id,),
    )
    result = cur.fetchone()
    cur.close()
    return result[0] if result else None


_SPEED_SQL = """
    CASE tag_id
        WHEN 101 THEN 110.0  -- motorway
        WHEN 102 THEN 80.0   -- motorway_link
        WHEN 104 THEN 100.0  -- trunk
        WHEN 105 THEN 80.0   -- trunk_link
        WHEN 106 THEN 80.0   -- primary
        WHEN 107 THEN 60.0   -- primary_link
        WHEN 108 THEN 60.0   -- secondary
        WHEN 109 THEN 50.0   -- secondary_link
        WHEN 110 THEN 50.0   -- tertiary
        WHEN 111 THEN 40.0   -- tertiary_link
        WHEN 112 THEN 50.0   -- residential (AU default)
        WHEN 113 THEN 10.0   -- living_street
        WHEN 114 THEN 20.0   -- service
        WHEN 117 THEN 50.0   -- unclassified
        ELSE 50.0
    END
"""

# Preference multiplier applied on top of real travel time.
# < 1.0 = preferred (motorways/trunks are easier and safer to drive).
# > 1.0 = penalised (avoid residential/service unless significantly faster).
# Deliberately modest so a genuinely faster residential path still wins.
_PREF_SQL = """
    CASE tag_id
        WHEN 101 THEN 0.4  -- motorway
        WHEN 102 THEN 0.4   -- motorway_link
        WHEN 104 THEN 0.88   -- trunk
        WHEN 105 THEN 0.92   -- trunk_link
        WHEN 106 THEN 0.95   -- primary
        WHEN 107 THEN 0.95   -- primary_link
        WHEN 108 THEN 1.00   -- secondary (neutral baseline)
        WHEN 109 THEN 1.00   -- secondary_link
        WHEN 110 THEN 1.10   -- tertiary
        WHEN 111 THEN 1.10   -- tertiary_link
        WHEN 112 THEN 1.40   -- residential
        WHEN 113 THEN 2.50   -- living_street
        WHEN 114 THEN 2.00   -- service
        WHEN 117 THEN 1.50   -- unclassified
        ELSE 1.0
    END
"""

# cost_s from osm2pgrouting = length_m / (maxspeed_kmh / 3.6), in seconds.
# Fall back to length_m + AU default speeds when cost_s = 0 (missing maxspeed tag).
# Then multiply by _PREF_SQL to bias toward higher-order roads.
_COST_EXPR = f"""
    (CASE WHEN cost_s > 0 THEN cost_s
          ELSE length_m / ({_SPEED_SQL} / 3.6)
     END) * ({_PREF_SQL})
"""

# IMPORTANT: negative reverse_cost_s means one-way street (osm2pgrouting uses -1 to signal
# "not traversable in this direction"). Never replace a negative with the fallback formula —
# doing so makes the road bidirectional and lets the router go the wrong way down a one-way.
_RCOST_EXPR = f"""
    CASE WHEN reverse_cost_s < 0 THEN reverse_cost_s
         ELSE (CASE WHEN reverse_cost_s > 0 THEN reverse_cost_s
                    ELSE length_m / ({_SPEED_SQL} / 3.6)
               END) * ({_PREF_SQL})
    END
"""


def create_route(id_1, id_2):
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT seq, route.node, route.edge, ways.osm_id, ways.name, route.cost, tag_id
        FROM pgr_dijkstra(
            'SELECT id, source, target,
                {_COST_EXPR} AS cost,
                {_RCOST_EXPR} AS reverse_cost
             FROM ways',
            %s, %s,
            directed => true
        ) AS route JOIN ways ON route.edge = ways.id ORDER BY seq
        """,
        (id_1, id_2),
    )
    result = cur.fetchall()
    cur.close()
    return result


def create_compliant_route(id_1, id_2):
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT seq, route.node, route.edge, ways.osm_id, ways.name, route.cost, tag_id
        FROM pgr_dijkstra(
            'SELECT id, source, target,
                {_COST_EXPR} AS cost,
                {_RCOST_EXPR} AS reverse_cost
             FROM ways
             WHERE NOT EXISTS (
                 SELECT 1 FROM victoria_s_volvo_semi_trailer_lzehv_pre_approved_network
                 WHERE ways.osm_id = osm_way_id
                 AND LOWER(access_code) = ''restricted''
             )',
            %s, %s,
            directed => true
        ) AS route JOIN ways ON route.edge = ways.id ORDER BY seq
        """,
        (id_1, id_2),
    )
    result = cur.fetchall()
    cur.close()
    return result


def get_road_info(id):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM ways WHERE id = %s
    """,
        (id,),
    )
    result = cur.fetchone()
    cur.close()
    return result


def get_restriction_for_osm_id(osm_id):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM victoria_s_volvo_semi_trailer_lzehv_pre_approved_network WHERE osm_way_id = %s
    """,
        (osm_id,),
    )
    result = cur.fetchone()
    cur.close()
    return result


def structure_route_as_dict(route):
    result = []
    for index, row in enumerate(route):
        geo = id_to_geo(row[2])
        restrictions = get_restriction_for_osm_id(row[3])
        result.append(
            {
                # Below is what route gets
                # (121, 166319, 776012, 485235230, 'Francis Street', 0.00011368289933051796, 108)
                "seq": row[0],
                "node_id": row[1],
                "edge_id": row[2],
                "osm_id": row[3],
                "name": row[4],
                "cost": row[5],
                "tag_id": row[6],
                "geo_start": geo[0][0],
                "geo_end": geo[1][0],
                "restrictions": restrictions,
            }
        )
    return result


def route_info(route):
    for row in route:
        # This is everything but often dont need everything
        # print(
        #     f"{row['seq']}. Name: {row['name']}, Internal ID: {row['edge_id']}, OSM ID: {row['osm_id']}, Cost: {row['cost']}, Tag ID: {row['tag_id']}, Geo Start: {row['geo_start']}, Geo End: {row['geo_end']}"
        # )
        print(
            f"{row['seq']}. Name: {row['name']}, Internal ID: {row['edge_id']}, OSM ID: {row['osm_id']}, Cost: {row['cost']}, Tag ID: {row['tag_id']}, Geo Start: {row['geo_start']}, Geo End: {row['geo_end']}, Restrictions: {row['restrictions']}"
        )
        # print(get_restriction_for_osm_id(row['osm_id']))


def id_to_geo(id):
    cur = conn.cursor()
    cur.execute("SELECT x1, y1 FROM ways WHERE id = %s;", (id,))
    start = cur.fetchall()
    cur.execute("SELECT x2, y2 FROM ways WHERE id = %s;", (id,))
    end = cur.fetchall()
    return start, end


def test():
    # point_1 = closest_point(145.041465, -37.823449)
    # print(point_1)
    # point_2 = closest_point(145.048146, -37.824105)
    # print(point_2)
    route = structure_route_as_dict(create_route(82662, 61407))
    route_info(route)


def get_id_from_osm_id(osm_id):
    cur = conn.cursor()
    cur.execute("SELECT id FROM ways WHERE osm_id = ?", (osm_id,))
    result = cur.fetchone()
    return result[0] if result else None


# Testing using various OSM IDs revelead that... well idk
# Occasionally routing sometimes failed, but testing with a random point on the calder freeway worked across the ENTIRETY of Victoria?
# But two places in the CBD two blocks away fail to route sometimes?
# start_source = lookup_id_from_osm_id(199910372)
# end_source = lookup_id_from_osm_id(13303784)
# print(get_road_info(start_source))
# print(get_road_info(end_source))
# print(start_source, end_source)
# # route_info(structure_route_as_dict(create_route(start_source, end_source)))
# route_info(structure_route_as_dict(create_compliant_route(start_source, end_source)))

# print(f"Burwood Road: {lookup_id_from_osm_id(1126612997)}")

# print(f"William Street: {lookup_id_from_osm_id(4080213)}")

# test()


def import_gpkg_to_pgr(gpkg_path):
    import sqlite3

    gpkg_conn = sqlite3.connect(gpkg_path)
    gpkg_cursor = gpkg_conn.cursor()

    cur = conn.cursor()
    # NAMING CONVENTION FOR THE TABLES: Replace all spaces with underscores, any other
    # characters that SQL does not allow should also be underscores
    cur.execute(
        """
            CREATE TABLE IF NOT EXISTS Victoria_s_Volvo_Semi_Trailer_LZEHV_Pre_Approved_Network (
                fid INTEGER PRIMARY KEY,
                osm_way_id INTEGER,
                osm_way_version INTEGER,
                access_code TEXT,
                access_description TEXT,
                road_name TEXT,
                road_manager_names TEXT
            );
        """,
        (),
    )
    for data in gpkg_cursor.execute(
        "SELECT fid, osm_way_id, osm_way_version, access_code, access_description, road_name, road_manager_names \
        FROM hvn_road_segments"
    ):
        cur.execute(
            """
                INSERT INTO Victoria_s_Volvo_Semi_Trailer_LZEHV_Pre_Approved_Network (
                    fid,
                    osm_way_id,
                    osm_way_version,
                    access_code,
                    access_description,
                    road_name,
                    road_manager_names
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            data,
        )
    conn.commit()
    cur.close()

    print("Import complete")


# import_gpkg_to_pgr("nhvr_hvn_12230801.gpkg")
