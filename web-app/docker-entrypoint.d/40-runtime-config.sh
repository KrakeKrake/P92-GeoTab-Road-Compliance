#!/bin/sh
# Runs from the stock nginx entrypoint before nginx starts. The variable list
# is explicit so envsubst does not touch anything else in the template.
set -eu

envsubst '${VITE_VALHALLA_URL} ${VITE_NHVR_API_URL} ${VITE_NOMINATIM_URL} ${VITE_CENTER_COORDS} ${VITE_DEFAULT_COSTING_MODEL} ${VITE_CLIENT_ID}' \
  < /etc/nginx/runtime-config.template.js \
  > /usr/share/nginx/html/config.js
