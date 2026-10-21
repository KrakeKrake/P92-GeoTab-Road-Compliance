#!/usr/bin/env bash
# Shared helpers for setup.sh and update.sh. Sourced, not executed.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

log()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWARN:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

ENV_FILE="${ENV_FILE:-$ROOT/.env}"
if [[ -f "$ENV_FILE" ]]; then
  # Compose uses the same file; sourcing it here is only for path checks and
  # the few values the scripts print. Keep secrets URL-safe and shell-safe.
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

NHVR_GPKG_DIR="${NHVR_GPKG_DIR:-./db/nhvr_gpkg}"
OSM_PBF_DIR="${OSM_PBF_DIR:-./nhvr-valhalla/run/nhvr-importer/osm.pbf}"
OSM_PBF_NAME="${OSM_PBF_NAME:-}"
OSM_PBF_FILE="$OSM_PBF_DIR/$OSM_PBF_NAME"
CUSTOM_FILES="$ROOT/custom_files"
BUILD_DIR="$CUSTOM_FILES/.build"
OLD_DIR="$CUSTOM_FILES/.old"
FAILED_DIR="$CUSTOM_FILES/.failed"
STATE_DIR="$ROOT/.state"
STATE_FILE="$STATE_DIR/data"

# ---- compose -----------------------------------------------------------------
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v podman-compose >/dev/null 2>&1; then
  COMPOSE=(podman-compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  die "no working 'docker compose', 'podman-compose' or 'docker-compose' found"
fi

# Explicit COMPOSE_FILE wins (use it for the deploy-only file). Otherwise load
# the override when present, matching plain `docker compose` behaviour.
compose_files=()
if [[ -n "${COMPOSE_FILE:-}" ]]; then
  IFS=':' read -r -a _files <<< "$COMPOSE_FILE"
  for _f in "${_files[@]}"; do
    compose_files+=(-f "$_f")
    [[ "$_f" == *override* ]] && HAS_BUILD=1
  done
else
  compose_files=(-f docker-compose.yml)
  if [[ -f docker-compose.override.yml ]]; then
    compose_files+=(-f docker-compose.override.yml)
    HAS_BUILD=1
  fi
fi
HAS_BUILD="${HAS_BUILD:-0}"

compose() { "${COMPOSE[@]}" --env-file "$ENV_FILE" "${compose_files[@]}" "$@"; }

# Plain image CLI for the "is it already built?" check in setup.sh.
if command -v docker >/dev/null 2>&1; then
  DOCKER=(docker)
elif command -v podman >/dev/null 2>&1; then
  DOCKER=(podman)
else
  DOCKER=()
fi
image_present() {
  [[ ${#DOCKER[@]} -gt 0 ]] && "${DOCKER[@]}" image inspect "$1" >/dev/null 2>&1
}

# ---- validation --------------------------------------------------------------
# mode: full (base PBF + GeoPackages), db (GeoPackages), tiles (live PBF),
# none (only .env/directories). Deployment servers may only have custom_files.
validate_inputs() {
  local mode="${1:-full}"
  [[ -f "$ENV_FILE" ]] || die ".env not found. Copy .env.example to .env and edit it."
  mkdir -p "$CUSTOM_FILES" "$STATE_DIR"
  case "$mode" in
    full)
      [[ -n "$OSM_PBF_NAME" ]] || die "OSM_PBF_NAME is not set in .env"
      [[ -d "$OSM_PBF_DIR" ]] || die "OSM_PBF_DIR does not exist: $OSM_PBF_DIR"
      [[ -f "$OSM_PBF_FILE" ]] || die "OSM PBF not found: $OSM_PBF_FILE"
      validate_inputs db
      ;;
    db)
      [[ -d "$NHVR_GPKG_DIR" ]] || die "NHVR_GPKG_DIR does not exist: $NHVR_GPKG_DIR"
      compgen -G "$NHVR_GPKG_DIR/*.gpkg" >/dev/null || die "no *.gpkg files in $NHVR_GPKG_DIR"
      ;;
    tiles)
      [[ -f "$CUSTOM_FILES/nhvr.osm.pbf" ]] || die "custom_files/nhvr.osm.pbf does not exist"
      ;;
    none) ;;
  esac
}

# ---- fingerprints ------------------------------------------------------------
# Size + mtime keeps updates cheap; --force is the escape hatch if a file is
# replaced without changing either.
fingerprint_pbf() {
  { stat -c '%n %s %Y' "$OSM_PBF_FILE"; } | sha256sum | cut -d' ' -f1
}
fingerprint_gpkg() {
  find "$NHVR_GPKG_DIR" -maxdepth 1 -type f -name '*.gpkg' \
    -printf '%f %s %T@\n' | sort | sha256sum | cut -d' ' -f1
}

read_state() {
  STATE_PBF=""
  STATE_GPKG=""
  if [[ -f "$STATE_FILE" ]]; then
    # shellcheck disable=SC1090
    . "$STATE_FILE"
  fi
}
write_state() {
  mkdir -p "$STATE_DIR"
  {
    echo "STATE_PBF=$1"
    echo "STATE_GPKG=$2"
    echo "STATE_UPDATED_AT=$(date -Is)"
  } > "$STATE_FILE"
}

# ---- waits -------------------------------------------------------------------
wait_for_postgres() {
  log "waiting for postgis"
  local i
  for i in $(seq 1 60); do
    compose exec -T postgis pg_isready -U "${DB_USER:-nhvr}" -d "${DB_NAME:-nhvr_compliance}" -q >/dev/null 2>&1 && return 0
    sleep 2
  done
  die "postgis did not become ready (check: compose logs postgis)"
}

wait_for_valhalla() {
  log "waiting for valhalla"
  local i
  for i in $(seq 1 60); do
    compose exec -T valhalla curl -fsS http://127.0.0.1:8002/status >/dev/null 2>&1 && return 0
    sleep 2
  done
  return 1
}

smoke_test() {
  local port="${WEB_PORT:-8080}"
  if ! command -v curl >/dev/null 2>&1; then
    warn "curl not found; skipping host smoke tests"
    return 0
  fi
  curl -fsS --max-time 10 "http://127.0.0.1:${port}/valhalla/status" >/dev/null \
    || warn "web-app /valhalla/status did not answer yet"
  curl -fsS --max-time 10 "http://127.0.0.1:${port}/api/compliance/profiles-by-licence/HC" >/dev/null \
    || warn "web-app /api/compliance/... did not answer yet"
}

# ---- tiles -------------------------------------------------------------------
# Builds into a directory using the same /custom_files path the server sees, so
# the generated valhalla.json is valid after promotion.
build_tiles() {
  local dir="$1"
  shift
  VALHALLA_BUILD_DIR="$dir" compose --profile tools run --rm --no-deps "$@" valhalla-tiles
}

seed_build_from_live() {
  local copy_admins="$1" # 1 = base PBF unchanged, reuse admin/timezone DBs
  mkdir -p "$BUILD_DIR"
  [[ -f "$CUSTOM_FILES/valhalla.json" ]] && cp -f "$CUSTOM_FILES/valhalla.json" "$BUILD_DIR/"
  [[ -f "$CUSTOM_FILES/default_speeds.json" ]] && cp -f "$CUSTOM_FILES/default_speeds.json" "$BUILD_DIR/"
  if [[ "$copy_admins" -eq 1 ]]; then
    [[ -f "$CUSTOM_FILES/admins.sqlite" ]] && cp -f "$CUSTOM_FILES/admins.sqlite" "$BUILD_DIR/"
    [[ -f "$CUSTOM_FILES/timezones.sqlite" ]] && cp -f "$CUSTOM_FILES/timezones.sqlite" "$BUILD_DIR/"
  fi
}

# Files that make up a usable Valhalla data directory.
TILE_ITEMS=(
  valhalla_tiles
  valhalla_tiles.tar
  valhalla.json
  file_hashes.txt
  admins.sqlite
  timezones.sqlite
  default_speeds.json
  nhvr.osm.pbf
)

# The previous setup named the merged PBF <base>.nhvr.osm.pbf. Keep the live
# directory to one PBF so a manual rebuild cannot merge two extracts.
cleanup_stale_pbfs() {
  find "$CUSTOM_FILES" -maxdepth 1 -type f -name '*.nhvr.osm.pbf' \
    ! -name 'nhvr.osm.pbf' -print -delete
}

rollback_build() {
  [[ -d "$OLD_DIR" ]] || die "no .old directory to roll back to"
  log "rolling back tiles"
  compose stop valhalla >/dev/null 2>&1 || true
  rm -rf "$FAILED_DIR"
  mkdir -p "$FAILED_DIR"
  local item
  for item in "${TILE_ITEMS[@]}"; do
    # Only replace items that were actually backed up; anything else is new.
    if [[ -e "$OLD_DIR/$item" ]]; then
      [[ -e "$CUSTOM_FILES/$item" ]] && mv -f "$CUSTOM_FILES/$item" "$FAILED_DIR/$item"
      mv -f "$OLD_DIR/$item" "$CUSTOM_FILES/$item"
    fi
  done
  compose up -d --no-deps valhalla
  wait_for_valhalla || die "rollback started valhalla but it is not healthy"
  compose restart web-app >/dev/null 2>&1 || true
  log "rollback complete"
}

# Stops the server, swaps .build into place, starts it and rolls back if the
# new tiles do not answer. Downtime is the swap, not the build.
promote_build() {
  local keep_old="$1"
  log "promoting new tiles"
  rm -rf "$OLD_DIR"
  mkdir -p "$OLD_DIR"
  compose stop valhalla >/dev/null 2>&1 || true
  local item
  for item in "${TILE_ITEMS[@]}"; do
    # Move a live item aside only when the build produced a replacement.
    if [[ -e "$BUILD_DIR/$item" ]]; then
      [[ -e "$CUSTOM_FILES/$item" ]] && mv -f "$CUSTOM_FILES/$item" "$OLD_DIR/$item"
      mv -f "$BUILD_DIR/$item" "$CUSTOM_FILES/$item"
    fi
  done
  compose up -d --no-deps valhalla
  if ! wait_for_valhalla; then
    if [[ -z "$(ls -A "$OLD_DIR" 2>/dev/null)" ]]; then
      die "new tiles did not become healthy and there are no previous tiles to roll back to"
    fi
    warn "new tiles did not become healthy; rolling back"
    rollback_build
    return 1
  fi
  # Nginx resolves upstream addresses at startup; restart it so a recreated
  # valhalla container does not leave the proxy pointing at the old IP.
  compose restart web-app >/dev/null 2>&1 || true
  cleanup_stale_pbfs
  if [[ "$keep_old" -eq 1 ]]; then
    log "keeping previous tiles in custom_files/.old"
  else
    rm -rf "$OLD_DIR"
  fi
}
