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

# ---- deployment topology -----------------------------------------------------
# Local services are the defaults. Point these at external hosts to split the
# stack; compose profiles are derived from them so both `docker compose` (via
# ./compose.sh) and the setup/update scripts agree on what to start.
DB_HOST="${DB_HOST:-postgis}"
DB_PORT="${DB_PORT:-5432}"
DB_SSLMODE="${DB_SSLMODE:-prefer}"
VALHALLA_UPSTREAM="${VALHALLA_UPSTREAM:-http://valhalla:8002}"
API_UPSTREAM="${API_UPSTREAM:-http://compliance-api:5000}"

upstream_host() {
  local value="$1"
  value="${value#*://}"
  value="${value%%/*}"
  value="${value%%:*}"
  printf '%s' "$value"
}

db_is_local() { [[ "$DB_HOST" == "postgis" ]]; }
valhalla_is_local() { [[ "$(upstream_host "$VALHALLA_UPSTREAM")" == "valhalla" ]]; }
api_is_local() { [[ "$(upstream_host "$API_UPSTREAM")" == "compliance-api" ]]; }

compose_profiles() {
  local profiles=()
  db_is_local && profiles+=(local-db)
  valhalla_is_local && profiles+=(local-valhalla)
  api_is_local && profiles+=(local-api)
  local IFS=,
  printf '%s' "${profiles[*]}"
}
COMPOSE_PROFILES="$(compose_profiles)"
export COMPOSE_PROFILES

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

# ---- filesystem --------------------------------------------------------------
# True when the active engine is a rootful Docker (or rootful Podman socket),
# where container root writes host files as uid 0. `docker info` is the
# canonical answer; the socket owner is the fallback for runtimes that do not
# expose .Rootless.
docker_rootful() {
  command -v docker >/dev/null 2>&1 || return 1
  local rootless endpoint socket
  rootless="$(docker info --format '{{.Rootless}}' 2>/dev/null || true)"
  case "$rootless" in
    true) return 1 ;;
    false) return 0 ;;
  esac
  endpoint="$(docker context inspect --format '{{.Endpoints.docker.Host}}' 2>/dev/null || true)"
  [[ "$endpoint" == *"/run/user/"* ]] && return 1
  socket="${endpoint#unix://}"
  [[ -z "$socket" || "$socket" == "$endpoint" ]] && socket="/var/run/docker.sock"
  [[ -S "$socket" ]] || return 1
  [[ "$(stat -c %u "$socket" 2>/dev/null || echo 0)" == "$(id -u)" ]] && return 1
  return 0
}

# Containers can leave root-owned files behind in custom_files (a previous
# rootful run, or docker creating the bind-mount target). Fail early with the
# chown command instead of a bare "Permission denied" halfway through setup.
require_writable_dir() {
  local dir="$1" label="${2:-$1}"
  mkdir -p "$dir" 2>/dev/null || true
  [[ -d "$dir" && -w "$dir" ]] && return 0
  die "$label is not writable by $(id -un) (uid $(id -u)): $dir
Fix the ownership once with:
  sudo chown -R $(id -u):$(id -g) \"$dir\"
or install the stack into a directory your user owns."
}

# ---- validation --------------------------------------------------------------
# mode: full (base PBF + GeoPackages), db (GeoPackages), tiles (live PBF),
# none (only .env/directories). Deployment servers may only have custom_files.
validate_inputs() {
  local mode="${1:-full}"
  local _compose_out _rootless
  [[ -f "$ENV_FILE" ]] || die ".env not found. Copy .env.example to .env and edit it."
  require_writable_dir "$CUSTOM_FILES" "custom_files (Valhalla tiles and PBF)"
  require_writable_dir "$STATE_DIR" "the update-state directory"
  # Rootful Docker writes bind-mounted files as root; the host-side promotion
  # then fails with permission denied. Warn before the long tile build.
  if command -v docker >/dev/null 2>&1 \
     && [[ "$(docker info --format '{{.Rootless}}' 2>/dev/null || true)" == "false" ]]; then
    if [[ "${PUID:-0}" == "0" || "${PGID:-0}" == "0" ]]; then
      warn "rootful Docker detected but PUID/PGID are 0; containers will write into custom_files as root, and the tile promotion will fail. Set PUID=$(id -u) and PGID=$(id -g) in .env, then run: sudo chown -R $(id -u):$(id -g) custom_files"
    elif [[ "${PUID:-0}" != "$(id -u)" || "${PGID:-0}" != "$(id -g)" ]]; then
      warn "rootful Docker: containers run as ${PUID:-0}:${PGID:-0}, but this shell is uid $(id -u), gid $(id -g). The host-side tile promotion will fail unless they match; update PUID/PGID in .env."
    fi
  fi
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
ensure_database() {
  if db_is_local; then
    log "starting postgis"
    compose up -d postgis
    wait_for_postgres
  else
    log "using external database ${DB_HOST}:${DB_PORT}"
  fi
}

wait_for_postgres() {
  log "waiting for postgis"
  local i
  for i in $(seq 1 60); do
    compose exec -T postgis pg_isready -U "${DB_USER:-nhvr}" -d "${DB_NAME:-nhvr_compliance}" -q >/dev/null 2>&1 && break
    [[ "$i" -eq 60 ]] && die "postgis did not become ready (check: compose logs postgis)"
    sleep 2
  done
  # pg_isready does not authenticate. Check the .env credentials over TCP so a
  # reused volume with an older password fails here with a clear message.
  if ! compose exec -T -e PGPASSWORD="${DB_PASSWORD:-}" postgis \
      psql -h 127.0.0.1 -U "${DB_USER:-nhvr}" -d "${DB_NAME:-nhvr_compliance}" \
      -tAc 'SELECT 1' >/dev/null 2>&1; then
    die "PostGIS rejected DB_USER/DB_PASSWORD from $ENV_FILE.
The volume '${DB_VOLUME_NAME:-${COMPOSE_PROJECT_NAME:-nhvr-compliance}-pgdata}' was probably created with a different password.
Keep the original password, or change the role inside the running container, or erase the volume if it has no data:
  docker compose down
  docker volume rm ${DB_VOLUME_NAME:-${COMPOSE_PROJECT_NAME:-nhvr-compliance}-pgdata}
  ./setup.sh"
  fi
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
  local port="${WEB_PORT:-8080}" i ok
  if ! command -v curl >/dev/null 2>&1; then
    warn "curl not found; skipping host smoke tests"
    return 0
  fi
  # Containers can take a few seconds to become reachable after a recreate.
  ok=0
  for i in $(seq 1 15); do
    if curl -fsS --max-time 10 "http://127.0.0.1:${port}/valhalla/status" >/dev/null; then
      ok=1
      break
    fi
    sleep 2
  done
  [[ "$ok" -eq 1 ]] || warn "web-app /valhalla/status did not answer yet"

  ok=0
  for i in $(seq 1 15); do
    if curl -fsS --max-time 10 "http://127.0.0.1:${port}/api/compliance/profiles-by-licence/HC" >/dev/null; then
      ok=1
      break
    fi
    sleep 2
  done
  [[ "$ok" -eq 1 ]] || warn "web-app /api/compliance/... did not answer yet"
}

# ---- tiles -------------------------------------------------------------------
# Builds into a directory using the same /custom_files path the server sees, so
# the generated valhalla.json is valid after promotion.
build_tiles() {
  local dir="$1"
  shift
  valhalla_is_local \
    || die "VALHALLA_UPSTREAM is external (${VALHALLA_UPSTREAM}); build tiles on the Valhalla host instead"
  VALHALLA_BUILD_DIR="$dir" compose --profile tools run --rm --no-deps "$@" valhalla-tiles
}

seed_build_from_live() {
  local copy_admins="$1" # 1 = base PBF unchanged, reuse admin/timezone DBs
  mkdir -p "$BUILD_DIR"
  if [[ -f "$CUSTOM_FILES/valhalla.json" ]]; then
    cp -f "$CUSTOM_FILES/valhalla.json" "$BUILD_DIR/"
  fi
  if [[ -f "$CUSTOM_FILES/default_speeds.json" ]]; then
    cp -f "$CUSTOM_FILES/default_speeds.json" "$BUILD_DIR/"
  fi
  if [[ "$copy_admins" -eq 1 ]]; then
    if [[ -f "$CUSTOM_FILES/admins.sqlite" ]]; then
      cp -f "$CUSTOM_FILES/admins.sqlite" "$BUILD_DIR/"
    fi
    if [[ -f "$CUSTOM_FILES/timezones.sqlite" ]]; then
      cp -f "$CUSTOM_FILES/timezones.sqlite" "$BUILD_DIR/"
    fi
  fi
  # Missing optional files are fine; the tile builder creates them.
  return 0
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

# Nginx resolves upstream hostnames at startup. Recreate the proxy after
# Valhalla or the API has been replaced so it picks up the new container IP.
reload_web_app() {
  compose up -d --no-deps --force-recreate web-app >/dev/null 2>&1 || true
}

# The build/promotion swap is host-side. If either directory is not owned by
# the invoking user (rootful container output, a previous sudo run, or a
# userns-remapped daemon) `mv` fails with a bare "Permission denied".
require_host_control() {
  local dir="$1" uid owner mode
  uid="$(id -u)"
  owner="$(stat -c %u "$dir" 2>/dev/null || echo unknown)"
  mode="$(stat -c %a "$dir" 2>/dev/null || echo unknown)"
  if [[ ! -w "$dir" || ! -x "$dir" ]]; then
    die "$dir is not writable by $(id -un) (uid $uid): owner uid=$owner mode=$mode
Fix it with:
  sudo chown -R $uid:$(id -g) \"$CUSTOM_FILES\""
  fi
}

move_tiles() {
  local src="$1" dst="$2" uid owner
  uid="$(id -u)"
  if [[ -d "$src" && ! -w "$src" ]]; then
    owner="$(stat -c %u "$src" 2>/dev/null || echo unknown)"
    die "cannot move directory $src: it was created by uid $owner and is not writable by uid $uid.
Renaming a directory updates its '..' entry, so the directory itself must be writable.
Run: sudo chown -R $uid:$(id -g) \"$CUSTOM_FILES\"
then re-run ./update.sh --tiles-only (or use the manual copy shown in the README)."
  fi
  if ! mv -f "$src" "$dst"; then
    owner="$(stat -c %u "$src" 2>/dev/null || echo unknown)"
    die "could not move $src to $dst (uid $uid, source owner uid=$owner)
The host-side tile swap needs write permission on $CUSTOM_FILES and $BUILD_DIR.
Run: sudo chown -R $uid:$(id -g) \"$CUSTOM_FILES\"
then re-run ./update.sh --tiles-only (or use the manual copy shown in the README)."
  fi
}

rollback_build() {
  valhalla_is_local \
    || die "VALHALLA_UPSTREAM is external (${VALHALLA_UPSTREAM}); there are no local tiles to roll back"
  [[ -d "$OLD_DIR" ]] || die "no .old directory to roll back to"
  require_host_control "$CUSTOM_FILES"
  require_host_control "$OLD_DIR"
  log "rolling back tiles"
  compose stop valhalla >/dev/null 2>&1 || true
  rm -rf "$FAILED_DIR"
  mkdir -p "$FAILED_DIR"
  local item
  for item in "${TILE_ITEMS[@]}"; do
    # Only replace items that were actually backed up; anything else is new.
    if [[ -e "$OLD_DIR/$item" ]]; then
      [[ -e "$CUSTOM_FILES/$item" ]] \
        && move_tiles "$CUSTOM_FILES/$item" "$FAILED_DIR/$item"
      move_tiles "$OLD_DIR/$item" "$CUSTOM_FILES/$item"
    fi
  done
  compose up -d --no-deps valhalla
  wait_for_valhalla || die "rollback started valhalla but it is not healthy"
  reload_web_app
  log "rollback complete"
}

# Stops the server, swaps .build into place, starts it and rolls back if the
# new tiles do not answer. Downtime is the swap, not the build.
promote_build() {
  local keep_old="$1"
  log "promoting new tiles"
  require_host_control "$CUSTOM_FILES"
  require_host_control "$BUILD_DIR"
  if [[ -e "$BUILD_DIR/valhalla_tiles" ]]; then
    local built_owner
    built_owner="$(stat -c %u "$BUILD_DIR/valhalla_tiles" 2>/dev/null || echo unknown)"
    if [[ "$built_owner" != "$(id -u)" ]]; then
      warn "tiles were built as uid $built_owner, not $(id -u); run sudo chown -R $(id -u):$(id -g) \"$CUSTOM_FILES\" after promotion"
      if [[ ! -w "$BUILD_DIR/valhalla_tiles" ]]; then
        die "the built tile directory is not writable by $(id -un) (uid $(id -u)), so it cannot be renamed into place. This usually means the containers ran as root (PUID=0 in .env). Run: sudo chown -R $(id -u):$(id -g) \"$CUSTOM_FILES\" and set PUID=$(id -u) / PGID=$(id -g) in .env."
      fi
    fi
  fi
  rm -rf "$OLD_DIR"
  mkdir -p "$OLD_DIR"
  compose stop valhalla >/dev/null 2>&1 || true
  local item
  for item in "${TILE_ITEMS[@]}"; do
    # Move a live item aside only when the build produced a replacement.
    if [[ -e "$BUILD_DIR/$item" ]]; then
      [[ -e "$CUSTOM_FILES/$item" ]] \
        && move_tiles "$CUSTOM_FILES/$item" "$OLD_DIR/$item"
      move_tiles "$BUILD_DIR/$item" "$CUSTOM_FILES/$item"
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
  # Nginx resolves upstream addresses at startup; the caller refreshes the
  # proxy after the whole stack is up (see reload_web_app).
  cleanup_stale_pbfs
  if [[ "$keep_old" -eq 1 ]]; then
    log "keeping previous tiles in custom_files/.old"
  else
    rm -rf "$OLD_DIR"
  fi
}
