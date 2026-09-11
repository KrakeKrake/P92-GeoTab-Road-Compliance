# The goal here:
# Scan the nhvr_gpkg directory
# For each one extract it and send it to the postgress with a table under that same network name
# Which lists out the OSM_IDs of that network with their:
# Access codes, street names, access descriptions, etc.
import os
import sqlite3 as sqlite
import dotenv
import argparse
import glob
import os
import sys

from dotenv import load_dotenv
from osgeo import ogr
import sqlalchemy as sql
from sqlalchemy import create_engine, text
import dotenv
from dataclasses import dataclass

ENV_PATH = "compliance/.env"
load_dotenv(dotenv_path=ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)

def main():
    for gpkg in get_nhvr_gpkgs():
        print(inspect_gpkg(gpkg))


def get_nhvr_gpkgs():
    '''
    Get all of the files in the nhvr_gpkgs folder and filter to only .gpkg
    '''
    return sorted(
        "nhvr_gpkg/" + x
        for x in os.listdir("nhvr_gpkg")
        if x.endswith(".gpkg")
    )

class gpkgEntry:
    def __init__(self, osm_id, access_code, access_desc, street_name):
        self.osm_id = osm_id
        self.access_code = access_code
        self.access_desc = access_desc
        self.street_name = street_name


def extract_nhvr_data(path):

    with sqlite.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT osm_id, access_code, access_desc, street_name""")
        rows = cursor.fetchall()
        print(rows)

def inspect_gpkg(path):
    with sqlite.connect(path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """)

        for row in cursor.fetchall():
            print(row[0])

# Enum for the access state.
ACCESS_STATUS = {
    "Approved": 0,
    "Approved with Conditions": 1,
    "Restricted": 2,
}
def access_status(access_string):
    if access_string is None:
        return None
    return ACCESS_STATUS.get(access_string.strip())


@dataclass
class NetworkAccess:
    status: int
    desc: str
    manager: str

def read_gpkgs(nhvr_dir):
    """
    Read every *.gpkg in nhvr_dir and build way_id -> {network: NetworkAccess}.
    This is gonna be big bcs it represents the entire network.
    """
    networks = {}  # osm_way_id -> {network_name: NetworkAccess, ...}
    for gpkg in sorted(glob.glob(os.path.join(nhvr_dir, "*.gpkg"))):
        nhvr_data = ogr.Open(gpkg)
        if nhvr_data is None:
            print(f"WARNING: could not open {gpkg}")
            continue
        layer = nhvr_data.GetLayerByName("hvn_road_segments")
        if layer is None:
            print(f"WARNING: no hvn_road_segments layer in {gpkg}")
            nhvr_data = None
            continue

        print(f"reading {gpkg} ({layer.GetFeatureCount()} segments)")
        layer.ResetReading()
        for feat in layer:
            way_id = feat.GetField("osm_way_id")
            name = feat.GetField("network_name")
            desc = feat.GetField("access_description")
            manager = feat.GetField("road_manager_names")
            status = access_status(feat.GetField("access_code"))

            if way_id is None or not name or status is None:
                continue

            way_networks = networks.setdefault(way_id, {})
            existing = way_networks.get(name)

            if existing is not None and existing.status != status:
                #print(f"Way {way_id} has different status for {name} ({existing.status} vs {status})")
                if existing.status < status:  # keep the more restrictive one
                    way_networks[name] = NetworkAccess(status, desc, manager)
            else:
                way_networks[name] = NetworkAccess(status, desc, manager)

    nhvr_data = None
    #print(f"{len(networks)} ways matched in NHVR data")
    return networks



def import_networks(networks: dict):
    engine = create_engine(DATABASE_URL)
    rows = []
    for way_id, net_map in networks.items():
        for network_name, entry in net_map.items():
            rows.append({
                "osm_way_id": way_id,
                "network_name": network_name,
                "access_code": entry.status,
                "access_desc": entry.desc,
                "manager": entry.manager,
            })
    upsert = text("""
        INSERT INTO nhvr_access.nhvr_network_access
            (osm_way_id, network_name, access_code, access_desc, manager)
        VALUES
            (:osm_way_id, :network_name, :access_code, :access_desc, :manager)
        ON CONFLICT (osm_way_id, network_name)
        DO UPDATE SET
            access_code = EXCLUDED.access_code,
            access_desc = EXCLUDED.access_desc,
            manager = EXCLUDED.manager,
            updated_at = now()
    """)

    with engine.begin() as conn:
        conn.execute(upsert, rows)

    print(f"Upserted {len(rows)} rows")


if __name__ == "__main__":
    networks = read_gpkgs("nhvr_gpkg")
    import_networks(networks)
