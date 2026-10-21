#!/usr/bin/env bash
# First-run setup for the GeoTab Road Compliance stack.
#
# Assumes `docker compose up` may already have been run; this script brings the
# data layer up in the right order and (re)builds Valhalla tiles.
#
#   ./setup.sh [--skip-pbf] [--skip-db] [--skip-tiles] [--skip-compliance]
#              [--reset-compliance] [--no-build]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
# shellcheck source=scripts/lib.sh
. "$ROOT/scripts/lib.sh"

SKIP_PBF=0
SKIP_DB=0
SKIP_TILES=0
SKIP_COMPLIANCE=0
RESET_COMPLIANCE=0
NO_BUILD=0

usage() {
  cat <<EOF
Usage: ./setup.sh [options]

  --skip-pbf            reuse custom_files/nhvr.osm.pbf instead of importing
  --skip-db             do not load the NHVR GeoPackages into PostGIS
  --skip-tiles          do not (re)build Valhalla tiles
  --skip-compliance     do not run SQL migrations/seeds
  --reset-compliance    DESTROYS compliance + account schemas, then reseeds
  --no-build            do not build/pull images first
  -h, --help            show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-pbf) SKIP_PBF=1 ;;
    --skip-db) SKIP_DB=1 ;;
    --skip-tiles) SKIP_TILES=1 ;;
    --skip-compliance) SKIP_COMPLIANCE=1 ;;
    --reset-compliance) RESET_COMPLIANCE=1 ;;
    --no-build) NO_BUILD=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
  shift
done

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$ROOT/.env.example" "$ENV_FILE"
  die "created .env from .env.example; edit it (paths, DB_PASSWORD), then re-run"
fi

if [[ $SKIP_PBF -eq 1 && $SKIP_DB -eq 1 ]]; then
  validate_inputs none
elif [[ $SKIP_PBF -eq 1 ]]; then
  validate_inputs db
else
  validate_inputs full
fi

# ---- images ------------------------------------------------------------------
if [[ $NO_BUILD -eq 0 ]]; then
  if [[ $HAS_BUILD -eq 1 ]]; then
    # Valhalla is a long C++ build. Keep an existing image (including the old
    # localhost/valhalla:nhvr tag) instead of recompiling it every setup run.
    VALHALLA_IMAGE="${IMAGE_REPO:?set IMAGE_REPO in .env}:valhalla-${IMAGE_TAG:-latest}"
    log "building the fast images"
    compose build compliance-api web-app nhvr-tools
    if image_present "$VALHALLA_IMAGE"; then
      log "using existing Valhalla image: $VALHALLA_IMAGE"
    elif image_present "localhost/valhalla:nhvr"; then
      log "tagging localhost/valhalla:nhvr as $VALHALLA_IMAGE"
      "${DOCKER[@]}" tag localhost/valhalla:nhvr "$VALHALLA_IMAGE"
    elif image_present "valhalla:nhvr"; then
      log "tagging valhalla:nhvr as $VALHALLA_IMAGE"
      "${DOCKER[@]}" tag valhalla:nhvr "$VALHALLA_IMAGE"
    else
      log "building Valhalla (long: full C++ compile)"
      compose build valhalla
    fi
  else
    log "pulling images"
    compose pull
  fi
fi

# ---- database schema ---------------------------------------------------------
log "starting postgis"
compose up -d postgis
wait_for_postgres

if [[ $SKIP_COMPLIANCE -eq 0 ]]; then
  if [[ $RESET_COMPLIANCE -eq 1 ]]; then
    warn "--reset-compliance: dropping compliance and account schemas"
    compose run --rm --no-deps db-migrate \
      python -m compliance.migrate --reset
  else
    log "applying compliance migrations/seeds"
    compose run --rm --no-deps db-migrate
  fi
fi

# ---- data --------------------------------------------------------------------
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

if [[ $SKIP_PBF -eq 0 ]]; then
  log "importing NHVR networks into the OSM PBF"
  compose run --rm --no-deps \
    -e OUTPUT_PBF=/custom_files/.build/nhvr.osm.pbf \
    nhvr-tools import
else
  if [[ $SKIP_TILES -eq 0 ]]; then
    log "reusing custom_files/nhvr.osm.pbf (--skip-pbf)"
    [[ -f "$CUSTOM_FILES/nhvr.osm.pbf" ]] \
      || die "--skip-pbf requested but custom_files/nhvr.osm.pbf does not exist"
    cp -f "$CUSTOM_FILES/nhvr.osm.pbf" "$BUILD_DIR/nhvr.osm.pbf"
  else
    log "skipping PBF import (--skip-pbf and --skip-tiles)"
  fi
fi

if [[ $SKIP_DB -eq 0 ]]; then
  log "loading NHVR networks into PostGIS"
  compose run --rm --no-deps nhvr-tools load-db
fi

if [[ $SKIP_TILES -eq 0 ]]; then
  log "building Valhalla tiles (this is the long step)"
  # Reuse admin/timezone DBs if this is a re-run over an existing directory.
  seed_build_from_live 1
  build_tiles "$BUILD_DIR"
  promote_build 0
else
  log "skipping tile build (--skip-tiles)"
  [[ -d "$CUSTOM_FILES/valhalla_tiles" || -f "$CUSTOM_FILES/valhalla_tiles.tar" ]] \
    || warn "no tiles present; Valhalla will not serve routes until update.sh runs"
fi

log "starting the stack"
compose up -d
# Recreate the proxy now that every upstream exists, so nginx resolves the
# current Valhalla/API container addresses.
reload_web_app

# ---- state -------------------------------------------------------------------
# Preserve the previous fingerprints for steps that were skipped, so a
# `setup.sh --skip-*` run does not make the next update redo everything.
read_state
PBF_STATE="$STATE_PBF"
GPKG_STATE="$STATE_GPKG"
[[ $SKIP_PBF -eq 0 && $SKIP_TILES -eq 0 ]] && PBF_STATE="$(fingerprint_pbf)"
[[ $SKIP_DB -eq 0 ]] && GPKG_STATE="$(fingerprint_gpkg)"
write_state "$PBF_STATE" "$GPKG_STATE"

smoke_test

cat <<EOF

Setup complete.

  Web app       http://localhost:${WEB_PORT:-8080}
  Valhalla      http://localhost:${WEB_PORT:-8080}/valhalla/status
  Compliance    http://localhost:${WEB_PORT:-8080}/api/compliance/profiles-by-licence/HC

If the tile build was long, follow it with:
  docker compose logs -f valhalla
EOF
