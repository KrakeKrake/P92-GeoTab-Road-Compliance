#!/usr/bin/env bash
# One-shot installer for the GeoTab Road Compliance stack.
#
#   curl -fsSL https://raw.githubusercontent.com/KrakeKrake/P92-GeoTab-Road-Compliance/main/install.sh | bash
#
# It downloads only the small deployment bundle (compose file + scripts), pulls
# the prebuilt images, asks where your data lives, and runs setup.sh. The source
# tree and build contexts are not needed on the target machine.
#
# Non-interactive:
#   curl -fsSL .../install.sh | bash -s -- --yes \
#     --nhvr-gpkg-dir /data/nhvr --osm-pbf /data/victoria.osm.pbf \
#     --db-password 'url-safe-password' --image-repo krakekrake/eat40005
set -euo pipefail

REPO_OWNER="${REPO_OWNER:-KrakeKrake}"
REPO_NAME="${REPO_NAME:-P92-GeoTab-Road-Compliance}"
REPO_BRANCH="${REPO_BRANCH:-main}"
RAW_BASE="${RAW_BASE:-https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${REPO_BRANCH}}"

INSTALL_DIR="${INSTALL_DIR:-}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-nhvr-compliance}"
NETWORK_NAME="${NETWORK_NAME:-${PROJECT_NAME//-/_}_default}"
DB_VOLUME_NAME="${DB_VOLUME_NAME:-${PROJECT_NAME}-pgdata}"

NHVR_GPKG_DIR="${NHVR_GPKG_DIR:-}"
OSM_PBF_FILE="${OSM_PBF_FILE:-}"
DB_PASSWORD="${DB_PASSWORD:-}"
IMAGE_REPO="${IMAGE_REPO:-docker.io/krakekrake/eat40005}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
PUID="${PUID:-}"
PGID="${PGID:-}"
WEB_PORT="${WEB_PORT:-8080}"

ASSUME_YES=0
NO_PULL=0
RECONFIGURE=0
PREPARE_ONLY=0
RESET_DB=0
FORCE=0
COPY_DATA=0

log()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWARN:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: install.sh [options]

  --dir DIR              install directory (default: the current directory)
  --force                replace an existing deployment bundle in --dir
  --copy-data            copy the GeoPackages and OSM PBF into <dir>/data
  --project-name NAME    Compose project name (default: nhvr-compliance)
  --nhvr-gpkg-dir DIR    directory containing the NHVR *.gpkg files
  --osm-pbf FILE         base OSM .pbf file
  --db-password PASS     database password (URL-safe)
  --image-repo REPO      Docker Hub repository for the images, e.g. user/repo
  --image-tag TAG        image tag suffix (default: latest)
  --web-port PORT        published web port (default: 8080)
  --branch NAME          git branch to download from (default: main)
  --no-pull              do not pull images (use images already on this host)
  --reconfigure          recreate .env (a backup is kept)
  --reset-db             delete the existing Postgres volume first
                         (DESTROYS the database; use on a failed fresh install)
  --prepare-only         download/configure only; do not run setup.sh
  --yes                  non-interactive; fail if required values are missing
  -h, --help             show this help

The NHVR GeoPackages and the OSM PBF are read from your machine; they are never
uploaded. The images must be published at \$IMAGE_REPO:<service>-\$IMAGE_TAG,
or already present locally when using --no-pull.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) INSTALL_DIR="$2"; shift 2 ;;
    --project-name) PROJECT_NAME="$2"; NETWORK_NAME="${PROJECT_NAME//-/_}_default"; DB_VOLUME_NAME="${PROJECT_NAME}-pgdata"; shift 2 ;;
    --nhvr-gpkg-dir) NHVR_GPKG_DIR="$2"; shift 2 ;;
    --osm-pbf) OSM_PBF_FILE="$2"; shift 2 ;;
    --db-password) DB_PASSWORD="$2"; shift 2 ;;
    --image-repo|--image-namespace) IMAGE_REPO="$2"; shift 2 ;;
    --image-tag) IMAGE_TAG="$2"; shift 2 ;;
    --web-port) WEB_PORT="$2"; shift 2 ;;
    --branch) REPO_BRANCH="$2"; RAW_BASE="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${REPO_BRANCH}"; shift 2 ;;
    --no-pull) NO_PULL=1; shift ;;
    --reconfigure) RECONFIGURE=1; shift ;;
    --reset-db) RESET_DB=1; shift ;;
    --force) FORCE=1; shift ;;
    --copy-data) COPY_DATA=1; shift ;;
    --prepare-only) PREPARE_ONLY=1; shift ;;
    --yes|-y) ASSUME_YES=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1 (use --help)" ;;
  esac
done

# Make Docker Hub explicit unless the first component is a registry. Without
# this, podman can resolve a short name to a local localhost/... image.
_first="${IMAGE_REPO%%/*}"
if [[ "$_first" != *.* && "$_first" != *:* && "$_first" != localhost ]]; then
  IMAGE_REPO="docker.io/$IMAGE_REPO"
fi

# Rootful Docker writes bind-mounted files as root, which makes the host-side
# tile promotion fail. Match the invoking user there; rootless Podman needs 0:0.
if [[ -z "$PUID" || -z "$PGID" ]]; then
  PUID=0
  PGID=0
  if command -v docker >/dev/null 2>&1; then
    _compose_out="$(docker compose version 2>&1 || true)"
    if [[ "$_compose_out" == *"Docker Compose version"* ]]; then
      _rootless="$(docker info --format '{{.Rootless}}' 2>/dev/null || true)"
      if [[ "$_rootless" == "false" ]]; then
        PUID="$(id -u)"
        PGID="$(id -g)"
      fi
    fi
  fi
fi

# ---- gather values -----------------------------------------------------------
ask() {
  local prompt="$1" default="${2:-}" answer=""
  if [[ -r /dev/tty ]]; then
    read -r -p "${prompt}${default:+ [${default}]}: " answer < /dev/tty || true
  fi
  printf '%s' "${answer:-$default}"
}

random_password() {
  # URL-safe, also safe to source from .env.
  local value
  value="$(head -c 32 /dev/urandom 2>/dev/null | base64 | tr -dc 'A-Za-z0-9' | head -c 24 || true)"
  printf '%s' "${value:-nhvr$(date +%s)}"
}

docker_cli() {
  if command -v docker >/dev/null 2>&1; then
    printf '%s' docker
  elif command -v podman >/dev/null 2>&1; then
    printf '%s' podman
  fi
}

volume_exists() {
  local cli
  cli="$(docker_cli)"
  [[ -n "$cli" ]] || return 1
  "$cli" volume inspect "$DB_VOLUME_NAME" >/dev/null 2>&1
}

remove_db_volume() {
  local cli
  cli="$(docker_cli)"
  [[ -n "$cli" ]] || die "cannot reset $DB_VOLUME_NAME: docker/podman not found"
  volume_exists || return 0
  log "removing database volume $DB_VOLUME_NAME"
  "$cli" volume rm "$DB_VOLUME_NAME" >/dev/null 2>&1 \
    || die "could not remove volume $DB_VOLUME_NAME; stop the stack first (docker compose down) and re-run with --reset-db"
}

# ---- install directory -------------------------------------------------------
if [[ -z "$INSTALL_DIR" ]]; then
  if [[ $ASSUME_YES -eq 1 ]]; then
    INSTALL_DIR="."
  else
    INSTALL_DIR="$(ask 'Install directory' '.')"
  fi
fi
[[ -n "$INSTALL_DIR" ]] || INSTALL_DIR="."
[[ -e "$INSTALL_DIR" && ! -d "$INSTALL_DIR" ]] \
  && die "install path exists and is not a directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
INSTALL_DIR="$(cd "$INSTALL_DIR" && pwd -P)"

# Do not replace the checkout's own compose/setup files by accident.
if [[ "$INSTALL_DIR" == "$(pwd -P)" && -d "$PWD/nhvr-valhalla" && -d "$PWD/web-app" ]]; then
  die "refusing to install into the source checkout; run from a deployment directory or pass --dir <dir>"
fi

# Do not silently overwrite an existing deployment bundle. A lone .env is
# allowed (e.g. retrying a failed install); --force replaces the bundle.
existing_bundle=0
for f in docker-compose.yml setup.sh update.sh scripts/lib.sh; do
  [[ -e "$INSTALL_DIR/$f" ]] && existing_bundle=1
done
if [[ $existing_bundle -eq 1 && $FORCE -eq 0 ]]; then
  die "$INSTALL_DIR already contains a deployment bundle; use --force to replace it or --dir <other-dir>"
fi

HAVE_ENV=0
[[ -f "$INSTALL_DIR/.env" && $RECONFIGURE -eq 0 ]] && HAVE_ENV=1
if [[ $HAVE_ENV -eq 1 ]]; then
  # Avoid silently reusing an unrelated .env from whatever directory we ran in.
  if ! grep -q '^NHVR_GPKG_DIR=' "$INSTALL_DIR/.env" \
     || ! grep -q '^IMAGE_REPO=' "$INSTALL_DIR/.env"; then
    die "$INSTALL_DIR/.env does not look like a GeoTab Road Compliance config; use --reconfigure or another --dir"
  fi
fi

if [[ $HAVE_ENV -eq 1 ]]; then
  log "using existing $INSTALL_DIR/.env"
else
  if [[ $ASSUME_YES -eq 0 ]]; then
    [[ -n "$NHVR_GPKG_DIR" ]] || NHVR_GPKG_DIR="$(ask 'Directory containing the NHVR .gpkg files')"
    [[ -n "$OSM_PBF_FILE" ]] || OSM_PBF_FILE="$(ask 'Path to the base OSM .pbf file')"
    if [[ -z "$DB_PASSWORD" ]]; then
      if [[ $RESET_DB -eq 0 ]] && volume_exists; then
        warn "Postgres volume '$DB_VOLUME_NAME' already exists, so a new password will not be applied to it."
        DB_PASSWORD="$(ask "Existing database password for $DB_VOLUME_NAME (leave blank to abort)" '')"
        [[ -n "$DB_PASSWORD" ]] || die "refusing to reuse volume '$DB_VOLUME_NAME' without its password; pass --db-password or use --reset-db to delete it"
      else
        DB_PASSWORD="$(ask 'Database password (press Enter to generate one)' "$(random_password)")"
      fi
    fi
    IMAGE_REPO="$(ask 'Docker Hub repository for the images (namespace/repo)' "$IMAGE_REPO")"
    WEB_PORT="$(ask 'Web port' "$WEB_PORT")"
  fi
fi

if [[ $HAVE_ENV -eq 1 ]]; then
  # setup.sh will validate the existing values.
  :
else
  [[ -n "$NHVR_GPKG_DIR" ]] || die "NHVR GeoPackage directory is required (--nhvr-gpkg-dir or interactive prompt)"
  [[ -d "$NHVR_GPKG_DIR" ]] || die "NHVR GeoPackage directory does not exist: $NHVR_GPKG_DIR"
  compgen -G "$NHVR_GPKG_DIR/*.gpkg" >/dev/null || die "no *.gpkg files in $NHVR_GPKG_DIR"
  [[ -n "$OSM_PBF_FILE" ]] || die "OSM PBF path is required (--osm-pbf or interactive prompt)"
  [[ -f "$OSM_PBF_FILE" ]] || die "OSM PBF not found: $OSM_PBF_FILE"
  if [[ -z "$DB_PASSWORD" ]]; then
    if [[ $RESET_DB -eq 0 ]] && volume_exists; then
      die "Postgres volume '$DB_VOLUME_NAME' already exists; pass --db-password with its password, or --reset-db to delete it"
    fi
    DB_PASSWORD="$(random_password)"
  fi
  # setup.sh runs from the install directory, so store absolute paths.
  NHVR_GPKG_DIR="$(cd "$NHVR_GPKG_DIR" && pwd)"
  OSM_PBF_FILE="$(cd "$(dirname "$OSM_PBF_FILE")" && pwd)/$(basename "$OSM_PBF_FILE")"
fi

# ---- optional data copy ------------------------------------------------------
if [[ $COPY_DATA -eq 1 ]]; then
  if [[ $HAVE_ENV -eq 1 ]]; then
    warn "--copy-data ignored when reusing an existing .env (use --reconfigure)"
  else
    DATA_GPKG="$INSTALL_DIR/data/nhvr_gpkg"
    DATA_OSM="$INSTALL_DIR/data/osm"
    if [[ "$DATA_GPKG" == "$NHVR_GPKG_DIR" ]]; then
      log "GeoPackages are already in $DATA_GPKG"
    elif [[ "$DATA_GPKG" == "$NHVR_GPKG_DIR"/* ]]; then
      die "install data directory is inside NHVR_GPKG_DIR; choose another --dir"
    else
      log "copying GeoPackages into $DATA_GPKG (this can take a while)"
      rm -rf "$DATA_GPKG"
      mkdir -p "$DATA_GPKG"
      cp -a "$NHVR_GPKG_DIR/." "$DATA_GPKG/"
      NHVR_GPKG_DIR="$DATA_GPKG"
    fi
    OSM_DEST="$DATA_OSM/$(basename "$OSM_PBF_FILE")"
    if [[ "$OSM_PBF_FILE" -ef "$OSM_DEST" ]]; then
      log "OSM PBF is already in $DATA_OSM"
    else
      log "copying OSM PBF into $DATA_OSM"
      mkdir -p "$DATA_OSM"
      cp -a "$OSM_PBF_FILE" "$OSM_DEST"
    fi
    OSM_PBF_FILE="$OSM_DEST"
  fi
fi

# ---- download the deployment bundle -----------------------------------------
# Only a source checkout supplies the bundle locally. An existing deployment
# directory must download it (with --force) so it can be upgraded.
if [[ -d "$PWD/nhvr-valhalla" && -d "$PWD/web-app" ]]; then
  SRC_DIR="$PWD"
else
  SRC_DIR=""
fi

mkdir -p "$INSTALL_DIR/scripts"
bundle=(
  docker-compose.yml
  .env.example
  setup.sh
  update.sh
  nginx.conf
  README.md
  scripts/lib.sh
)

for rel in "${bundle[@]}"; do
  dst="$INSTALL_DIR/$rel"
  [[ "$INSTALL_DIR" -ef "$SRC_DIR" ]] && continue
  if [[ -n "$SRC_DIR" ]]; then
    cp -f "$SRC_DIR/$rel" "$dst"
  else
    mkdir -p "$(dirname "$dst")"
    if ! curl -fsSL "$RAW_BASE/$rel" -o "$dst"; then
      die "could not download $rel from $RAW_BASE (is the branch pushed?)"
    fi
  fi
done

chmod +x "$INSTALL_DIR/setup.sh" "$INSTALL_DIR/update.sh" "$INSTALL_DIR/scripts/lib.sh"

# ---- write .env --------------------------------------------------------------
set_env() {
  local file="$1" key="$2" value="$3"
  KEY="$key" VALUE="$value" awk '
    BEGIN { k = ENVIRON["KEY"]; v = ENVIRON["VALUE"] }
    index($0, k "=") == 1 { print k "=" v; found = 1; next }
    { print }
    END { if (!found) print k "=" v }
  ' "$file" > "$file.tmp"
  mv "$file.tmp" "$file"
}

if [[ ! -f "$INSTALL_DIR/.env" || $RECONFIGURE -eq 1 ]]; then
  [[ -f "$INSTALL_DIR/.env" ]] && cp -f "$INSTALL_DIR/.env" "$INSTALL_DIR/.env.bak"
  cp -f "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
  set_env "$INSTALL_DIR/.env" COMPOSE_PROJECT_NAME "$PROJECT_NAME"
  set_env "$INSTALL_DIR/.env" NETWORK_NAME "$NETWORK_NAME"
  set_env "$INSTALL_DIR/.env" DB_VOLUME_NAME "$DB_VOLUME_NAME"
  set_env "$INSTALL_DIR/.env" NHVR_GPKG_DIR "$NHVR_GPKG_DIR"
  set_env "$INSTALL_DIR/.env" OSM_PBF_DIR "$(dirname "$OSM_PBF_FILE")"
  set_env "$INSTALL_DIR/.env" OSM_PBF_NAME "$(basename "$OSM_PBF_FILE")"
  set_env "$INSTALL_DIR/.env" DB_PASSWORD "$DB_PASSWORD"
  set_env "$INSTALL_DIR/.env" IMAGE_REPO "$IMAGE_REPO"
  set_env "$INSTALL_DIR/.env" IMAGE_TAG "$IMAGE_TAG"
  set_env "$INSTALL_DIR/.env" PUID "$PUID"
  set_env "$INSTALL_DIR/.env" PGID "$PGID"
  set_env "$INSTALL_DIR/.env" WEB_PORT "$WEB_PORT"
  chmod 600 "$INSTALL_DIR/.env"
  log "wrote $INSTALL_DIR/.env"
fi

DISPLAY_PORT="$(grep -E '^WEB_PORT=' "$INSTALL_DIR/.env" 2>/dev/null | cut -d= -f2 || true)"
DISPLAY_PORT="${DISPLAY_PORT:-8080}"

cat <<EOF

Installed into: $INSTALL_DIR
Manage from:    cd $INSTALL_DIR

Web app:        http://localhost:${DISPLAY_PORT}

Valhalla:       http://localhost:${DISPLAY_PORT}/valhalla/status
Compliance API: http://localhost:${DISPLAY_PORT}/api/compliance/profiles-by-licence/HC

EOF

if [[ $RESET_DB -eq 1 ]]; then
  remove_db_volume
fi

if [[ $PREPARE_ONLY -eq 1 ]]; then
  log "prepared only; run: cd $INSTALL_DIR && ./setup.sh"
  exit 0
fi

cd "$INSTALL_DIR"
if [[ $NO_PULL -eq 1 ]]; then
  log "running setup (using local images)"
  ./setup.sh --no-build
else
  log "running setup (pulling images)"
  ./setup.sh
fi
