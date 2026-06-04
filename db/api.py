from db_test import (
    create_compliant_route,
    create_route,
    lookup_id_from_osm_id,
    structure_route_as_dict,
)
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/api/route")
def route():
    osm_id_1 = request.args.get("osm_id_1")
    osm_id_2 = request.args.get("osm_id_2")
    print(osm_id_1, osm_id_2)
    id_1 = lookup_id_from_osm_id(osm_id_1)
    id_2 = lookup_id_from_osm_id(osm_id_2)

    if not osm_id_1 or not osm_id_2:
        return jsonify({"error": "from and to query params required"}), 400

    route = structure_route_as_dict(create_compliant_route(id_1, id_2))
    return jsonify(route)
