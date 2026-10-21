#!/usr/bin/env bash
# Loads every NHVR GeoPackage into nhvr_access.nhvr_network_access.
# The live table is never dropped in place: rows go into a staging table and
# are swapped in one transaction, so the compliance API keeps answering
# during an update.
set -euo pipefail

: "${NHVR_GPKG_DIR:?NHVR_GPKG_DIR is not set}"
: "${PGHOST:?PGHOST is not set}"
: "${PGPORT:?PGPORT is not set}"
: "${PGDATABASE:?PGDATABASE is not set}"
: "${PGUSER:?PGUSER is not set}"

shopt -s nullglob
gpkgs=("${NHVR_GPKG_DIR}"/*.gpkg)
if (( ${#gpkgs[@]} == 0 )); then
  echo "ERROR: no *.gpkg files in ${NHVR_GPKG_DIR}" >&2
  exit 1
fi

psql -v ON_ERROR_STOP=1 -q <<'SQL'
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;
CREATE SCHEMA IF NOT EXISTS nhvr_access;
DROP TABLE IF EXISTS nhvr_access.nhvr_network_access_staging CASCADE;
SQL

first=1
for gpkg in "${gpkgs[@]}"; do
  echo "loading $(basename "$gpkg")"
  args=(
    -f PostgreSQL
    "PG:host=${PGHOST} port=${PGPORT} dbname=${PGDATABASE} user=${PGUSER}"
    "$gpkg"
    -sql "SELECT osm_way_id, network_name, access_code,
                 access_description AS access_desc,
                 road_manager_names AS manager, geom
          FROM hvn_road_segments"
    -nln nhvr_access.nhvr_network_access_staging
    -nlt LINESTRING
    --config PG_USE_COPY YES
  )
  if [[ $first -eq 1 ]]; then
    args+=(-lco GEOMETRY_NAME=geom)
    first=0
  else
    args+=(-append)
  fi
  ogr2ogr "${args[@]}"
done

psql -v ON_ERROR_STOP=1 -q <<'SQL'
-- Same conflict rule as import-nhvr.py: keep the most restrictive code per
-- (osm_way_id, network_name).
DROP TABLE IF EXISTS nhvr_access.nhvr_network_access_dedup;
CREATE TABLE nhvr_access.nhvr_network_access_dedup AS
SELECT DISTINCT ON (osm_way_id, network_name)
       osm_way_id, network_name, access_code, access_desc, manager, geom
FROM nhvr_access.nhvr_network_access_staging
ORDER BY osm_way_id, network_name,
         CASE access_code
           WHEN 'Restricted' THEN 2
           WHEN 'Approved with Conditions' THEN 1
           WHEN 'Approved' THEN 0
           ELSE -1
         END DESC;

BEGIN;
DROP TABLE IF EXISTS nhvr_access.nhvr_network_access_old;
ALTER TABLE IF EXISTS nhvr_access.nhvr_network_access
  RENAME TO nhvr_network_access_old;
ALTER TABLE nhvr_access.nhvr_network_access_dedup
  RENAME TO nhvr_network_access;
COMMIT;

DROP TABLE IF EXISTS nhvr_access.nhvr_network_access_old;
DROP TABLE IF EXISTS nhvr_access.nhvr_network_access_staging;

CREATE INDEX IF NOT EXISTS nhvr_network_access_way_id_idx
  ON nhvr_access.nhvr_network_access (osm_way_id);
CREATE INDEX IF NOT EXISTS nhvr_network_access_network_idx
  ON nhvr_access.nhvr_network_access (network_name);
ANALYZE nhvr_access.nhvr_network_access;
SQL

rows="$(psql -tAc 'SELECT count(*) FROM nhvr_access.nhvr_network_access;')"
echo "nhvr_access.nhvr_network_access: ${rows} rows"
