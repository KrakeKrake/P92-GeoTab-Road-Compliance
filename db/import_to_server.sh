#!/usr/bin/env bash

set -a
source .env
set +a

DATA_DIR=$(realpath "$1")

if [ -z "$DATA_DIR" ]; then
    echo "Usage: $0 <data_dir>"
    exit 1
fi


import_osm() {
    echo "Importing OSM data..."
    docker run --rm \
        -v "$DATA_DIR:/data" \
        pgrouting/pgrouting-extra \
        osm2pgrouting -f "/data/$1" \
        --conf /usr/local/share/osm2pgrouting/mapconfig_for_cars.xml \
        --clean \
        --dbname "$DB_NAME" --username "$DB_USER" --password "$DB_PASSWORD" \
        --host "$REMOTE_HOST" \
        --port "$DB_PORT"
}

echo "Beginning OSM data import..."
echo "INFO: This may use ALOT of RAM, and may fail silently, be sure to allow docker to use as much ram as necessary"
if [ -d "$DATA_DIR" ]; then
    echo "OSM data found. Proceeding with import..."
    for file in "$DATA_DIR"/*; do
        if [[ $file == *.osm.pbf ]]; then
            echo "Found PBF file: $file"
            if [ -x "$(command -v osmium)" ]; then
                converted="${file%.osm.pbf}.osm"
                osmium cat "$file" -o "$converted"
                import_osm "$(basename "$converted")"
            else
                echo "Please install osmium (possibly called 'osmium-tools') to unpack PBF files! Skipping: $file"
                continue
            fi
        elif [[ "$file" == *.osm ]]; then
            echo "Found OSM file: $file"
            import_osm "$(basename "$file")"
        fi
    done
else
    echo "OSM data not found. Skipping import."
fi
