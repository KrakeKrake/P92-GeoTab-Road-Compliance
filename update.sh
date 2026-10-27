#!/usr/bin/env bash
# Refreshes the NHVR data (PBF + PostGIS) and Valhalla tiles.
#
# Valhalla has no incremental tile update, so any data change means a full tile
# rebuild. The default path builds into custom_files/.build and swaps it in
# after a successful build (blue/green); --simple rebuilds in place instead.
#
#   ./update.sh [--dry-run] [--force] [--db-only] [--tiles-only]
#               [--no-migrations] [--simple] [--keep-old] [--rollback]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
# shellcheck source=scripts/lib.sh
. "$ROOT/scripts/lib.sh"

DRY_RUN=0
FORCE=0
DB_ONLY=0
TILES_ONLY=0
NO_MIGRATIONS=0
SIMPLE=0
KEEP_OLD=0
ROLLBACK=0

usage() {
  cat <<EOF
Usage: ./update.sh [options]

  --dry-run          show what would change, do nothing
  --force            treat inputs as changed even if their fingerprint matches
  --db-only          reload PostGIS only (does not advance update state)
  --tiles-only       rebuild tiles from the existing PBF (does not advance state)
  --no-migrations    skip SQL migrations
  --simple           stop Valhalla and rebuild in place (downtime = build time)
  --keep-old         keep custom_files/.old after a successful blue/green swap
  --rollback         restore custom_files/.old and restart Valhalla
  -h, --help         show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --force) FORCE=1 ;;
    --db-only) DB_ONLY=1 ;;
    --tiles-only) TILES_ONLY=1 ;;
    --no-migrations) NO_MIGRATIONS=1 ;;
    --simple) SIMPLE=1 ;;
    --keep-old) KEEP_OLD=1 ;;
    --rollback) ROLLBACK=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
  shift
done

[[ -f "$ENV_FILE" ]] || die ".env not found. Copy .env.example to .env and edit it."
if [[ $TILES_ONLY -eq 1 ]]; then
  validate_inputs tiles
elif [[ $DB_ONLY -eq 1 ]]; then
  validate_inputs db
else
  validate_inputs full
fi
read_state

if ! valhalla_is_local; then
  if [[ $TILES_ONLY -eq 1 || $ROLLBACK -eq 1 ]]; then
    die "VALHALLA_UPSTREAM is external (${VALHALLA_UPSTREAM}); this host does not manage the tile set. Run this on the Valhalla host, or build tiles there with the valhalla-tiles image."
  fi
  log "VALHALLA_UPSTREAM=${VALHALLA_UPSTREAM} is external; only the PostGIS data will be refreshed"
fi

if [[ $ROLLBACK -eq 1 ]]; then
  rollback_build
  exit 0
fi

CUR_PBF="$(fingerprint_pbf)"
CUR_GPKG="$(fingerprint_gpkg)"
PBF_CHANGED=1
GPKG_CHANGED=1
[[ "$CUR_PBF" == "$STATE_PBF" ]] && PBF_CHANGED=0
[[ "$CUR_GPKG" == "$STATE_GPKG" ]] && GPKG_CHANGED=0
if [[ $FORCE -eq 1 ]]; then
  PBF_CHANGED=1
  GPKG_CHANGED=1
fi

if [[ $DRY_RUN -eq 1 ]]; then
  changed=0
  [[ $PBF_CHANGED -eq 1 || $GPKG_CHANGED -eq 1 ]] && changed=1
  cat <<EOF
base PBF changed:   $( [[ $PBF_CHANGED -eq 1 ]] && echo yes || echo no )
NHVR GeoPackages:   $( [[ $GPKG_CHANGED -eq 1 ]] && echo changed || echo unchanged )
would migrate:      $( [[ $NO_MIGRATIONS -eq 1 || $TILES_ONLY -eq 1 ]] && echo no || echo yes )
would import PBF:   $( [[ $TILES_ONLY -eq 0 && $changed -eq 1 ]] && valhalla_is_local && echo yes || echo no )
would reload DB:    $( [[ $TILES_ONLY -eq 0 && ( $DB_ONLY -eq 1 || $changed -eq 1 ) ]] && echo yes || echo no )
would build tiles:  $( [[ $DB_ONLY -eq 0 && $changed -eq 1 ]] && valhalla_is_local && echo yes || echo no )
mode:               $( [[ $SIMPLE -eq 1 ]] && echo "in-place" || echo "blue/green" )
EOF
  [[ $changed -eq 0 && $DB_ONLY -eq 0 && $TILES_ONLY -eq 0 ]] && echo "nothing to do (use --force)"
  exit 0
fi

# ---- schema ------------------------------------------------------------------
run_migrations() {
  [[ $NO_MIGRATIONS -eq 1 || $TILES_ONLY -eq 1 ]] && return 0
  log "applying compliance migrations"
  compose run --rm --no-deps db-migrate
}

# ---- db-only -----------------------------------------------------------------
if [[ $DB_ONLY -eq 1 ]]; then
  if [[ $GPKG_CHANGED -eq 0 ]]; then
    log "NHVR GeoPackages unchanged (use --force to reload)"
  fi
  ensure_database
  run_migrations
  log "reloading NHVR networks into PostGIS"
  compose run --rm --no-deps nhvr-tools load-db
  warn "state not updated; run ./update.sh again before rebuilding tiles"
  exit 0
fi

# ---- tiles-only --------------------------------------------------------------
if [[ $TILES_ONLY -eq 1 ]]; then
  [[ -f "$CUSTOM_FILES/nhvr.osm.pbf" ]] \
    || die "--tiles-only needs custom_files/nhvr.osm.pbf"
  if [[ $PBF_CHANGED -eq 1 || $GPKG_CHANGED -eq 1 ]]; then
    warn "inputs changed; --tiles-only builds from the existing (possibly stale) PBF"
  fi
  rm -rf "$BUILD_DIR"
  mkdir -p "$BUILD_DIR"
  cp -f "$CUSTOM_FILES/nhvr.osm.pbf" "$BUILD_DIR/nhvr.osm.pbf"
  seed_build_from_live 1
  log "rebuilding Valhalla tiles"
  build_tiles "$BUILD_DIR" -e build_admins=False -e build_time_zones=False
  promote_build "$KEEP_OLD"
  reload_web_app
  warn "state not updated by --tiles-only"
  smoke_test
  exit 0
fi

# ---- nothing changed ---------------------------------------------------------
if [[ $PBF_CHANGED -eq 0 && $GPKG_CHANGED -eq 0 ]]; then
  ensure_database
  run_migrations
  log "NHVR data and tiles are up to date (use --force to rebuild)"
  exit 0
fi

# ---- import + load + build ---------------------------------------------------
ensure_database
run_migrations

if ! valhalla_is_local; then
  log "loading NHVR networks into PostGIS (Valhalla is external; no tile build)"
  compose run --rm --no-deps nhvr-tools load-db
  write_state "$CUR_PBF" "$CUR_GPKG"
  smoke_test
  log "update complete"
  exit 0
fi

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

log "importing NHVR networks into the OSM PBF"
compose run --rm --no-deps \
  -e OUTPUT_PBF=/custom_files/.build/nhvr.osm.pbf \
  nhvr-tools import

log "loading NHVR networks into PostGIS"
compose run --rm --no-deps nhvr-tools load-db

# The admin/timezone databases come from the base OSM extract, not the NHVR
# tags, so they can be reused when only the GeoPackages changed.
if [[ $PBF_CHANGED -eq 1 ]]; then
  COPY_ADMINS=0
  BUILD_ARGS=(-e build_admins=True -e build_time_zones=True)
else
  COPY_ADMINS=1
  BUILD_ARGS=(-e build_admins=False -e build_time_zones=False)
fi
seed_build_from_live "$COPY_ADMINS"

if [[ $SIMPLE -eq 1 ]]; then
  log "rebuilding tiles in place (Valhalla will be unavailable)"
  rm -rf "$OLD_DIR"
  mkdir -p "$OLD_DIR"
  compose stop valhalla >/dev/null 2>&1 || true
  for item in valhalla_tiles valhalla_tiles.tar file_hashes.txt nhvr.osm.pbf; do
    [[ -e "$CUSTOM_FILES/$item" ]] && mv -f "$CUSTOM_FILES/$item" "$OLD_DIR/$item"
  done
  if [[ "$COPY_ADMINS" -eq 0 ]]; then
    for item in admins.sqlite timezones.sqlite; do
      [[ -e "$CUSTOM_FILES/$item" ]] && mv -f "$CUSTOM_FILES/$item" "$OLD_DIR/$item"
    done
  fi
  cp -f "$BUILD_DIR/nhvr.osm.pbf" "$CUSTOM_FILES/nhvr.osm.pbf"
  if ! build_tiles "$CUSTOM_FILES" "${BUILD_ARGS[@]}"; then
    warn "tile build failed; restoring the previous tiles"
    rollback_build
    exit 1
  fi
  compose up -d --no-deps valhalla
  if ! wait_for_valhalla; then
    warn "new tiles are not healthy; restoring the previous tiles"
    rollback_build
    exit 1
  fi
  reload_web_app
  cleanup_stale_pbfs
  rm -rf "$OLD_DIR"
else
  log "building Valhalla tiles (this is the long step)"
  build_tiles "$BUILD_DIR" "${BUILD_ARGS[@]}"
  promote_build "$KEEP_OLD"
  reload_web_app
fi

write_state "$CUR_PBF" "$CUR_GPKG"
smoke_test
log "update complete"
