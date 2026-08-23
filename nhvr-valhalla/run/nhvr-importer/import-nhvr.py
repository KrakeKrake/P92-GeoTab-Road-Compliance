### USAGE
#
# python import-nhvr.py --nhvr-dir nhvr/ --input osm.pbf/victoria-260816.osm.pbf --output victoria.nhvr.osm.pbf
#
#
#




import argparse
import glob
import os
import sys
import osmium
from osgeo import ogr






# Enum for the access state.
ACCESS_STATUS = {
    "Approved": 0,
    "Approved with Conditions": 1,
    "Restricted": 2,
}


def read_gpkgs(nhvr_dir):
    """
    Read every *.gpkg in nhvr_dir and build way_id -> {network: status}.
    This is gonna be big bcs it represents the entire network.
    """
    networks = {}  # osm_way_id -> {network_name: status, network_name: status, ...}
    # For each geopackage...
    for gpkg in sorted(glob.glob(os.path.join(nhvr_dir, "*.gpkg"))):
        nhvr_data = ogr.Open(gpkg)
        if nhvr_data is None:
            print(f"WARNING: could not open {gpkg}")
            continue

        # This layer is all of the ways in the geopackage, most important one
        layer = nhvr_data.GetLayerByName("hvn_road_segments")
        if layer is None:
            print(f"WARNING: no hvn_road_segments layer in {gpkg}")
            nhvr_data = None
            continue

        #
        print(f"reading {gpkg} ({layer.GetFeatureCount()} segments)")
        layer.ResetReading()
        for feat in layer:
            way_id = feat.GetField("osm_way_id")

            # Not the name of the raod but the name of the network (I.E HPLT B-Double)
            name = feat.GetField("network_name")


            status = access_status(feat.GetField("access_code"))
            if not way_id or not name or status is None:
                continue

            # Way networks is a dict of {network_name: status} for this way.
            # Its a reference not forgotten
            way_networks = networks.setdefault(way_id, {})
            prev_status = way_networks.get(name)
            # If there *was* a previous status, and it's not the same as the current status,
            # then we should use the more restrictive status.
            if prev_status is not None and prev_status != status:
                print(f"Way {way_id} has different status for {name} ({prev_status} vs {status})")
                if prev_status < status: # So the more restrictive status is used
                    # I dont think nhvr has any duplicates, better safe than sorry.
                    way_networks[name] = status
            else:
                way_networks[name] = status
    nhvr_data = None
    print(f"{len(networks)} ways matched in NHVR data")
    return networks


def access_status(status_string):
    """
    A function that returns the access status of a network based on its status string
    Afaik there are only 3 used by the NHVR, but could of course be expanded.
    """
    if status_string == "Approved":
        return ACCESS_STATUS["Approved"]
    elif status_string == "Approved with Conditions":
        return ACCESS_STATUS["Approved with Conditions"]
    elif status_string == "Restricted":
        return ACCESS_STATUS["Restricted"]
    else:
        return None

def format_tag(networks):
    """
    Format the tag in the required pipe seperated format for Valhalla to parse correctly.
    Improbably that any networks will have the pipe in their name.
    """
    return "|".join(f"{name}:{status}" for name, status in sorted(networks.items()))



class nhvrWays(osmium.SimpleHandler):
    """
    A handler based on osmium.SimpleHandler that adds nhvr_networks tags to matched ways
    """

    def __init__(self, networks, writer):
        super().__init__()
        self.networks = networks
        self.writer = writer
        self.modified = 0

    def node(self, n):
        self.writer.add_node(n)

    def way(self, w):
        if w.id in self.networks:
            m = osmium.osm.mutable.Way(w)
            tags = [(t.k, t.v) for t in w.tags]
            tags.append(("nhvr_networks", format_tag(self.networks[w.id])))
            m.tags = tags
            self.writer.add_way(m)
            self.modified += 1
        else:
            self.writer.add_way(w)

    def relation(self, r):
        self.writer.add_relation(r)



def main():
    here = os.path.dirname(os.path.abspath(__file__))

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="NHVR data importer")
    _ = parser.add_argument("--nhvr-dir", default=os.path.join(here, "nhvr"),
                        help="directory containing NHVR *.gpkg files")
    _ = parser.add_argument("--input", required=True, help="input OSM.PBF file path")
    _ = parser.add_argument("--output", default="New PBF", help="output OSM.PBF file path")
    args = parser.parse_args()

    output = args.output or args.input + ".nhvr.osm.pbf"
    networks = read_gpkgs(args.nhvr_dir) # Read the NHVR data into memory
    print(networks) #Debug
    if not networks:
        sys.exit("no NHVR way matches found, aborting")

    # If the output exists, un-exist it.
    if os.path.exists(output):
        os.unlink(output)

    print(f"processing {args.input}")
    writer = osmium.SimpleWriter(output)
    handler = nhvrWays(networks, writer) # Write the NHVR memory out of memory.
    handler.apply_file(args.input)
    writer.close()

    print(f"added nhvr_networks to {handler.modified} ways")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
