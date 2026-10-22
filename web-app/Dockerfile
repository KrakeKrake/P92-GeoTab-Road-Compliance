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

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/runtime-config.template.js /etc/nginx/runtime-config.template.js
COPY docker-entrypoint.d/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh
RUN chmod +x /docker-entrypoint.d/40-runtime-config.sh

COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
