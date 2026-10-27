FROM node:24-alpine AS builder
WORKDIR /app
ENV PATH=/app/node_modules/.bin:$PATH

# package-lock.json is part of the build context now, so the build is
# reproducible instead of resolving dependencies afresh.
COPY package.json package-lock.json ./
RUN npm ci

COPY . /app
ENV NODE_ENV=production
RUN npm run build

# production environment
FROM nginx:1.29-alpine
# envsubst writes /usr/share/nginx/html/config.js at container start.
RUN apk add --no-cache gettext

# Upstreams are substituted into the nginx config at container start. The
# filter keeps nginx variables such as $host intact.
ENV VALHALLA_UPSTREAM=http://valhalla:8002 \
    API_UPSTREAM=http://compliance-api:5000 \
    NGINX_ENVSUBST_FILTER="^(VALHALLA_UPSTREAM|API_UPSTREAM)$"

# The stock server block is replaced by the template below.
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY docker/runtime-config.template.js /etc/nginx/runtime-config.template.js
COPY docker-entrypoint.d/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh
RUN chmod +x /docker-entrypoint.d/40-runtime-config.sh

COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
