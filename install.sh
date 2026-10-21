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

INSTALL_DIR="${INSTALL_DIR:-$PWD/nhvr-compliance}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-nhvr-compliance}"
NETWORK_NAME="${NETWORK_NAME:-${PROJECT_NAME//-/_}_default}"
DB_VOLUME_NAME="${DB_VOLUME_NAME:-${PROJECT_NAME}-pgdata}"

NHVR_GPKG_DIR="${NHVR_GPKG_DIR:-}"
OSM_PBF_FILE="${OSM_PBF_FILE:-}"
DB_PASSWORD="${DB_PASSWORD:-}"
IMAGE_REPO="${IMAGE_REPO:-docker.io/krakekrake/eat40005}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
WEB_PORT="${WEB_PORT:-8080}"

ASSUME_YES=0
NO_PULL=0
RECONFIGURE=0
PREPARE_ONLY=0

log()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWARN:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: install.sh [options]

  --dir DIR              install directory (default: \$PWD/nhvr-compliance;
                         use . for the current directory)
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

if [[ -f "$INSTALL_DIR/.env" && $RECONFIGURE -eq 0 ]]; then
  log "using existing $INSTALL_DIR/.env"
else
  if [[ $ASSUME_YES -eq 0 ]]; then
    [[ -n "$NHVR_GPKG_DIR" ]] || NHVR_GPKG_DIR="$(ask 'Directory containing the NHVR .gpkg files')"
    [[ -n "$OSM_PBF_FILE" ]] || OSM_PBF_FILE="$(ask 'Path to the base OSM .pbf file')"
    [[ -n "$DB_PASSWORD" ]] || DB_PASSWORD="$(ask 'Database password (press Enter to generate one)' "$(random_password)")"
    IMAGE_REPO="$(ask 'Docker Hub repository for the images (namespace/repo)' "$IMAGE_REPO")"
    WEB_PORT="$(ask 'Web port' "$WEB_PORT")"
  fi
fi

if [[ -f "$INSTALL_DIR/.env" && $RECONFIGURE -eq 0 ]]; then
  # setup.sh will validate the existing values.
  :
else
  [[ -n "$NHVR_GPKG_DIR" ]] || die "NHVR GeoPackage directory is required (--nhvr-gpkg-dir or interactive prompt)"
  [[ -d "$NHVR_GPKG_DIR" ]] || die "NHVR GeoPackage directory does not exist: $NHVR_GPKG_DIR"
  compgen -G "$NHVR_GPKG_DIR/*.gpkg" >/dev/null || die "no *.gpkg files in $NHVR_GPKG_DIR"
  [[ -n "$OSM_PBF_FILE" ]] || die "OSM PBF path is required (--osm-pbf or interactive prompt)"
  [[ -f "$OSM_PBF_FILE" ]] || die "OSM PBF not found: $OSM_PBF_FILE"
  [[ -n "$DB_PASSWORD" ]] || DB_PASSWORD="$(random_password)"
  # setup.sh runs from the install directory, so store absolute paths.
  NHVR_GPKG_DIR="$(cd "$NHVR_GPKG_DIR" && pwd)"
  OSM_PBF_FILE="$(cd "$(dirname "$OSM_PBF_FILE")" && pwd)/$(basename "$OSM_PBF_FILE")"
fi

# ---- download the deployment bundle -----------------------------------------
# Running from a checkout uses the local files; the curl path downloads them.
if [[ -f "$PWD/docker-compose.yml" && -f "$PWD/setup.sh" && -f "$PWD/scripts/lib.sh" ]]; then
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
