#!/usr/bin/env bash
# First-run setup (and deliberate full rebuild) for the GeoTab Road Compliance
# stack.
#
# What it does, in order:
#   1. validates .env and the input paths (unless a --skip-* flag avoids them);
#   2. builds or pulls the images (skip with --no-build);
#   3. starts the bundled PostgreSQL, or uses DB_HOST, then applies the
#      compliance schema and first-run seeds (idempotent);
#   4. imports the NHVR access tags into a merged OSM PBF (nhvr-tools import);
#   5. loads the same NHVR networks into PostGIS for the API (nhvr-tools load-db);
#   6. builds Valhalla tiles into custom_files/.build and promotes them
#      (blue/green), unless VALHALLA_UPSTREAM points at an external server;
#   7. starts the stack and runs HTTP smoke tests.
#
# When to run it:
#   - after installing, or when you want a full rebuild.
#   - routine data refreshes should use ./update.sh, which fingerprints the
#     inputs and skips work that is not needed.
#
# It is safe to re-run, but unlike update.sh it re-imports and rebuilds every
# time unless you use the --skip-* flags. Persistent state (the Postgres volume,
# custom_files/, .state/) is never deleted by a normal run; only
# --reset-compliance drops the compliance/account schemas.
#
# External services: if DB_HOST is not "postgis" the bundled database is not
# started, and if VALHALLA_UPSTREAM is not the bundled valhalla the PBF import
# and tile build are skipped. See README "Split deployment".
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

# A missing .env is a configuration error: create the template so the user has
# something to edit, then stop before anything starts.
if [[ ! -f "$ENV_FILE" ]]; then
  cp "$ROOT/.env.example" "$ENV_FILE"
  die "created .env from .env.example; edit it (paths, DB_PASSWORD), then re-run"
fi

# Validate only the inputs this run will actually use:
#   full -> base PBF + GeoPackages, db -> GeoPackages, none -> neither.
if [[ $SKIP_PBF -eq 1 && $SKIP_DB -eq 1 ]]; then
  validate_inputs none
elif [[ $SKIP_PBF -eq 1 ]]; then
  validate_inputs db
else
  validate_inputs full
fi

# ---- images ------------------------------------------------------------------
# A source checkout (docker-compose.override.yml present) builds locally; a
# deployment pulls the published tags.
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
# ensure_database starts the bundled PostGIS and waits for it, or just checks
# the external DB_HOST settings. The migrations are idempotent.
ensure_database

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
# Two independent data products:
#   - the merged PBF feeds the Valhalla routing graph (only when Valhalla is local);
#   - PostGIS nhvr_access.nhvr_network_access feeds the compliance API.
# --skip-pbf/--skip-tiles and --skip-db turn each half off separately.
if valhalla_is_local; then
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
else
  log "VALHALLA_UPSTREAM=${VALHALLA_UPSTREAM} is external; skipping the PBF import and tile build"
fi

if [[ $SKIP_DB -eq 0 ]]; then
  log "loading NHVR networks into PostGIS"
  compose run --rm --no-deps nhvr-tools load-db
fi

if [[ $SKIP_TILES -eq 0 ]]; then
  if valhalla_is_local; then
    log "building Valhalla tiles (this is the long step)"
    # Reuse the existing admin/timezone DBs on a rerun. Build into .build and
    # swap into place only if the new server answers, so a failed build leaves
    # the previous tiles untouched.
    seed_build_from_live 1
    build_tiles "$BUILD_DIR"
    promote_build 0
  fi
else
  log "skipping tile build (--skip-tiles)"
  if valhalla_is_local; then
    [[ -d "$CUSTOM_FILES/valhalla_tiles" || -f "$CUSTOM_FILES/valhalla_tiles.tar" ]] \
      || warn "no tiles present; Valhalla will not serve routes until update.sh runs"
  fi
fi

log "starting the stack"
if ! compose up -d; then
  # podman-compose can race while recreating a container; a retry is enough.
  warn "compose up reported an error; retrying once"
  sleep 2
  compose up -d
fi
# Recreate the proxy now that every upstream exists, so nginx resolves the
# current Valhalla/API container addresses.
reload_web_app

# ---- state -------------------------------------------------------------------
# Record input fingerprints so update.sh can tell whether a later run has
# anything to do. Steps that were skipped keep their previous fingerprint, so
# `setup.sh --skip-*` does not make the next update redo them.
read_state
PBF_STATE="$STATE_PBF"
GPKG_STATE="$STATE_GPKG"
[[ $SKIP_PBF -eq 0 && $SKIP_TILES -eq 0 ]] && valhalla_is_local \
  && PBF_STATE="$(fingerprint_pbf)"
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
