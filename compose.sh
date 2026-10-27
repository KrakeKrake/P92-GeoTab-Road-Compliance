#!/usr/bin/env bash
# docker compose wrapper that derives COMPOSE_PROFILES from the .env topology
# (DB_HOST, VALHALLA_UPSTREAM, API_UPSTREAM).
#
# Use this for commands you run by hand so an external database or external
# Valhalla/API does not get shadowed by a bundled container:
#
#   ./compose.sh ps
#   ./compose.sh logs -f valhalla
#   ./compose.sh up -d web-app
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
. "$ROOT/scripts/lib.sh"

compose "$@"
