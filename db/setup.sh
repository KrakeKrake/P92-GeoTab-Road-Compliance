#!/usr/bin/env bash

COMPOSE_FILE="./docker-compose.yml"

import_osm() {
    echo "Importing OSM data..."
    docker run --rm \
        --network "nhvr_compliance_default" \
        -v "$(pwd)/source:/data" \
        pgrouting/pgrouting-extra \
        osm2pgrouting -f /data/$1 \
        --conf /usr/local/share/osm2pgrouting/mapconfig_for_cars.xml \
        --clean \
        --dbname "$DB_NAME" --username "$DB_USER" --password "$DB_PASSWORD" \
        --host "$DB_CONTAINER" \
        --port "$DB_PORT"
}

set -a
source .env
set +a

RUN_IMPORT=false

for arg in "$@"; do
    case $arg in
    --import) RUN_IMPORT=true ;;
    esac
done

echo "Setting up database and adminer..."

docker compose up -d

echo "Waiting for database to be ready..."
RETRIES=120
until docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME" -q 2>/dev/null; do
    sleep 1
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -eq 0 ]; then
        echo "Failed to connect to database in time (120s)."
        exit 1
    fi
done

# Create the extensions in the DB!
echo "Creating extensions in database..."

docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS pgrouting;"

echo "Checking versions..."
postgis_ver=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT PostGIS_full_version();")
pgrouting_ver=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT pgr_version();")
echo "PostGIS version: $postgis_ver"
echo "pgrouting version: $pgrouting_ver"

if [[ "$RUN_IMPORT" == "false" ]]; then
    exit 0
fi

# Check for OSM data
echo "Beginning OSM data import..."
echo "INFO: This may use ALOT of RAM, and may fail silently, be sure to allow docker to use as much ram as necessary"
if [ -d "./source/" ]; then
    echo "OSM data found. Proceeding with import..."
    for file in ./source/*; do
        if [[ $file == *.osm.pbf ]]; then
            echo "Found PBF file: $file"
            if [ -x "$(command -v osmium)" ]; then
                converted="${file%.osm.pbf}.osm"
                osmium cat "$file" -o "$converted"
                import_osm "$(basename "$converted")"
            else
                echo "Please install osmium to unpack PBF files! Skipping: $file"
                continue
            fi
        elif [[ "$file" == *.osm ]]; then
            echo "Found OSM file: $file"
            import_osm "$file"
        fi
    done
else
    echo "OSM data not found. Skipping import."
fi
