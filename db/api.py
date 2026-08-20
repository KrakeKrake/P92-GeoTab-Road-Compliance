from flask import Flask, jsonify, request
from flask_cors import CORS

from compliance.routes import compliance_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(compliance_bp)


def nearest_node(lon, lat):
    """Returns the source node ID of the nearest road segment to the given coordinates."""
    from db_test import conn
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source FROM ways
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        LIMIT 1
        """,
        (lon, lat),
    )
    result = cur.fetchone()
    cur.close()
    return result[0] if result else None


@app.route("/api/route")
def route():
    try:
        from db_test import create_compliant_route, structure_route_as_dict
    except Exception as error:
        return jsonify({
            "error": "Routing database is not available.",
            "detail": str(error),
        }), 500

    lat1 = request.args.get("lat1", type=float)
    lon1 = request.args.get("lon1", type=float)
    lat2 = request.args.get("lat2", type=float)
    lon2 = request.args.get("lon2", type=float)

    if None in (lat1, lon1, lat2, lon2):
        return jsonify({"error": "lat1, lon1, lat2, lon2 query params are required"}), 400

    try:
        node1 = nearest_node(lon1, lat1)
        node2 = nearest_node(lon2, lat2)
    except Exception as e:
        return jsonify({"error": "Failed to find nearest road nodes.", "detail": str(e)}), 500

    if not node1 or not node2:
        return jsonify({"error": "Could not find a road near one or both locations."}), 400

    print(f"Routing: ({lat1},{lon1}) -> node {node1}  |  ({lat2},{lon2}) -> node {node2}")

    try:
        result = structure_route_as_dict(create_compliant_route(node1, node2))
    except Exception as e:
        return jsonify({"error": "Routing failed.", "detail": str(e)}), 500

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
