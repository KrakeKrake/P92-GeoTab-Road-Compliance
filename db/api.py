from flask import Flask, jsonify, request
from flask_cors import CORS

from compliance.routes import compliance_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(compliance_bp)


@app.route("/api/route")
def route():
    try:
        from db_test import (
            create_compliant_route,
            lookup_id_from_osm_id,
            lookup_end_id_from_osm_id,
            structure_route_as_dict,
        )
    except Exception as error:
        return jsonify({
            "error": "Routing database is not available.",
            "detail": str(error),
        }), 500

    osm_id_1 = request.args.get("osm_id_1")
    osm_id_2 = request.args.get("osm_id_2")

    if not osm_id_1 or not osm_id_2:
        return jsonify({"error": "from and to query params required"}), 400

    id_1 = lookup_id_from_osm_id(osm_id_1)
    id_2 = lookup_end_id_from_osm_id(osm_id_2)

    print(f"Routing: OSM {osm_id_1} -> node {id_1}  |  OSM {osm_id_2} -> node {id_2}")

    route = structure_route_as_dict(create_compliant_route(id_1, id_2))
    return jsonify(route)


if __name__ == "__main__":
    app.run(debug=True, port=5000)