import os

from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import bindparam

ENV_PATH = ".env"
load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")
access_blueprint = Blueprint("nhvr-access", __name__, url_prefix="/api/nhvr-access")
engine = create_engine(DATABASE_URL)


def format_response(rows):
    result = {    }
    for row in rows:
        result.setdefault(str(row.osm_way_id), []).append({
            "osm_way_id": row.osm_way_id,
            "networkName": row.network_name,
            "access": row.access_code,
            "description": row.access_desc,
            "manager": row.manager,
        })
    return result


@access_blueprint.route("/query", methods=["GET"])
def request_network_access():
    '''
    Networks should be a list of network names, as selectable.
    The database is then asked "Please get all of these networks"
    Returns a list in format of:
    <osm_id>: [
        {
          networkName: 'NHVR',
          access: 'restricted',
          description: 'Restricted network',
        },
        {
          networkName: <name>,
          access: 'conditional',
          description: 'Allowed only between 9 to 5',
        },
      ],
    '''
    networks = request.args.getlist("network")
    if not networks:
        return jsonify({"error": "at least one 'network' param required"}), 400

    with engine.connect() as conn:

        stmt = text("""
            SELECT osm_way_id, network_name, access_code, access_desc, manager
            FROM nhvr_access.nhvr_network_access
            WHERE network_name IN :networks
        """).bindparams(bindparam("networks", expanding=True))
        result = conn.execute(stmt, {"networks": networks})
        rows = result.fetchall()
    print(rows)

    return jsonify(format_response(rows))

if __name__ == "__main__":
    request_network_access(['CONTROLLED_ACCESS_BUS', 'VIC - HPLV 36.5m Tri-Dolly A-Double'])
