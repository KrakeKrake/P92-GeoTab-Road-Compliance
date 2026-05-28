def parse_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert GeoPackage to PGRouting format"
    )
    parser.add_argument("gpkg", help="Path to GeoPackage file")
    return parser.parse_args()


def main():
    args = parse_cli()
    sqlite_path = args.gpkg
    import sqlite3

    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    # For now just print all the possible cols in the "hvn_road_segments"
    print(cursor.execute("PRAGMA table_info(hvn_road_segments)").fetchall())
    # Now get all of those and uhh, do something with them?
    data = cursor.execute(
        "SELECT osm_way_id, osm_way_version, access_code, access_description, road_name, road_manager_names \
        FROM hvn_road_segments"
    ).fetchall()

    print(data)
    print(
        cursor.execute(
            "SELECT * FROM hvn_road_segments WHERE access_code != 'Approved'"
        ).fetchone()
    )


if __name__ == "__main__":
    main()
