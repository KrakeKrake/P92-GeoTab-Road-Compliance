#!/usr/bin/env bash
# Dispatches the two data jobs. `docker compose run --rm nhvr-tools import`
# etc. Only the selected job runs; the default `help` exits 0.
set -euo pipefail
cd "$(dirname "$0")"

cmd="${1:-help}"
case "$cmd" in
  import)
    : "${NHVR_GPKG_DIR:?NHVR_GPKG_DIR is not set}"
    : "${OSM_PBF_DIR:?OSM_PBF_DIR is not set}"
    : "${OSM_PBF_NAME:?OSM_PBF_NAME is not set}"
    : "${OUTPUT_PBF:?OUTPUT_PBF is not set}"

    input="${OSM_PBF_DIR}/${OSM_PBF_NAME}"
    [[ -f "$input" ]] || { echo "ERROR: base OSM PBF not found: $input" >&2; exit 1; }

    mkdir -p "$(dirname "$OUTPUT_PBF")"
    # Write beside the output, then rename, so an interrupted import never
    # leaves a half-written PBF for the tile builder to pick up.
    tmp="$(dirname "$OUTPUT_PBF")/.nhvr-import.$(basename "$OUTPUT_PBF")"
    rm -f "$tmp"
    python3 import-nhvr.py \
      --nhvr-dir "$NHVR_GPKG_DIR" \
      --input "$input" \
      --output "$tmp"
    mv -f "$tmp" "$OUTPUT_PBF"
    ;;

  load-db)
    exec ./load-nhvr.sh
    ;;

  help|--help|-h)
    cat <<'EOF'
Usage: docker compose run --rm nhvr-tools <command>

  import    merge NHVR *.gpkg access tags into the base OSM PBF
  load-db   load NHVR networks into PostGIS (staging + atomic swap)
  help      show this message
EOF
    ;;

  *)
    echo "ERROR: unknown command: $cmd" >&2
    exit 1
    ;;
esac
