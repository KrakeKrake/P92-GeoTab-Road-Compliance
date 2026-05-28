import psycopg as postgres

DB_URL = "eat40005.krakekrake.me"
DB_NAME = "o2p"
DB_USER = "o2p"
DB_PASSWORD = "lU0pgj9up@vty1B#plVA"

conn = postgres.connect(host=DB_URL, user=DB_USER, password=DB_PASSWORD)
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

    # cost * CASE tag_id
    #             WHEN 101 THEN 0.5   -- motorway, make very attractive
    #             WHEN 102 THEN 0.7   -- trunk
    #             WHEN 103 THEN 0.8   -- primary
    #             WHEN 106 THEN 2.0   -- residential, penalise
    #             WHEN 107 THEN 5.0   -- living street, heavily penalise
    #             WHEN 110 THEN 10.0  -- service road
    #             ELSE 1.0
    #         END AS cost,
    #         reverse_cost * CASE tag_id
    #             WHEN 101 THEN 0.5   -- motorway, make very attractive
    #             WHEN 102 THEN 0.7   -- trunk
    #             WHEN 103 THEN 0.8   -- primary
    #             WHEN 106 THEN 2.0   -- residential, penalise
    #             WHEN 107 THEN 5.0   -- living street, heavily penalise
    #             WHEN 110 THEN 10.0  -- service road
    #             ELSE 1.0
    #         END AS reverse_cost


def create_route(id_1, id_2):

    cur = conn.cursor()
    cur.execute(
        """
        SELECT seq, route.node, route.edge, ways.osm_id, ways.name, route.cost FROM pgr_astar(
        'SELECT id, source, target, x1, y1, x2, y2, cost * CASE tag_id
                    WHEN 101 THEN 0.5   -- motorway, make very attractive
                    WHEN 102 THEN 0.7   -- trunk
                    WHEN 103 THEN 0.8   -- primary
                    WHEN 106 THEN 2.0   -- residential
                    WHEN 107 THEN 5.0   -- living street
                    WHEN 110 THEN 10.0  -- service road
                    ELSE 1.0
                END AS cost,
                reverse_cost * CASE tag_id
                    WHEN 101 THEN 0.5   -- motorway, make very attractive
                    WHEN 102 THEN 0.7   -- trunk
                    WHEN 103 THEN 0.8   -- primary
                    WHEN 106 THEN 2.0   -- residential
                    WHEN 107 THEN 5.0   -- living street
                    WHEN 110 THEN 10.0  -- service road
                    ELSE 1.0
                END AS reverse_cost
        FROM ways ',
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
        """
        SELECT seq, route.node, route.edge, ways.osm_id, ways.name, route.cost FROM pgr_astar(
        'SELECT id, source, target, x1, y1, x2, y2, cost, reverse_cost
        FROM ways
        LEFT JOIN victoria_s_volvo_semi_trailer_lzehv_pre_approved_network ON ways.osm_id = osm_way_id WHERE access_code != ''restricted'' OR access_code IS NULL',
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


def structure_route_as_dict(route):
    result = []
    for index, row in enumerate(route):
        result.append(
            {
                "seq": row[0],
                "osm_id": row[3],
                "name": row[4],
                "cost": row[5],
            }
        )
    return result


def route_info(route):
    for row in route:
        print(
            f"{row['seq']}. Name: {row['name']}, OSM ID: {row['osm_id']}, Cost: {row['cost']}"
        )


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
start_source = lookup_id_from_osm_id(199910372)
end_source = lookup_id_from_osm_id(13303784)
print(get_road_info(start_source))
print(get_road_info(end_source))
print(start_source, end_source)
route_info(structure_route_as_dict(create_route(start_source, end_source)))

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
