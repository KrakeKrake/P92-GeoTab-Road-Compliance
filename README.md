# GeoTab Road Compliance

A self-contained web application for heavy-vehicle route compliance:

- a Valhalla-based web app for planning truck routes and isochrones
- a Valhalla routing server with NHVR network access built into the graph
- a PostgreSQL database and compliance API for vehicle profiles, mass/dimension
  checks, and NHVR network lookup

This README is for installing and running it. For development see [Development](#development) at the end.

## What you need

| Requirement | Notes |
|---|---|
| Docker with Compose v2, **or** Podman with `podman-compose` | `docker compose version` or `podman-compose version` must work |
| The NHVR GeoPackage files | A folder containing one or more `*.gpkg` files |
| One base OpenStreetMap extract | A single `*.osm.pbf` file (e.g. a Geofabrik state/region extract) |
| Access to the container images | The four images are tags in one repository (`IMAGE_REPO`), or already present on the host |
| Disk space | At least ~10 GB free for a state-sized extract; more for larger regions |
| A terminal | The installer prompts for the data paths and a database password |

The NHVR GeoPackages and the OSM extract are read from your machine and are
**never uploaded**. They do need to be present on the machine before setup.

## Install (one command)

The installer pulls the prebuilt images from the repository you choose. If you
are the developer and have not published the images yet, build and push them
first (see [Development](#development)), then run the installer.

```bash
mkdir -p ~/nhvr && cd ~/nhvr
curl -fsSL https://raw.githubusercontent.com/KrakeKrake/P92-GeoTab-Road-Compliance/main/install.sh | bash
```

The installer does not clone the source tree. It downloads the Compose file and
scripts (a few KB) and pulls the runtime images (several GB). Your GeoPackages
and OSM extract stay on your machine and are only read by the containers.

The installer:

1. installs the deployment bundle (Compose file, setup/update scripts, `.env`
   template) into the current directory by default — **not** the source tree;
2. asks for the NHVR GeoPackage folder, the base OSM `.pbf` file, a database
   password (press Enter to generate one), the image namespace, and the web
   port;
3. writes `.env`;
4. pulls the prebuilt images, imports the data, builds the Valhalla tiles and
   starts the stack.

> The command above uses the `main` branch. If you are testing a branch before
> it is merged, replace `main` in the URL with the branch name and pass
> `--branch <branch>` to the installer.

When it finishes, open:

- **Web app:** <http://localhost:8080>
- **Valhalla status:** <http://localhost:8080/valhalla/status>
- **API example:** <http://localhost:8080/api/compliance/profiles-by-licence/HC>

The install directory is self-contained. Manage the stack from there:

```bash
cd ~/nhvr
docker compose ps
```

Use `--dir DIR` to install somewhere else. Do not install into the source
checkout; the installer refuses that on purpose. If the target already contains
a deployment bundle, it refuses to overwrite it unless you pass `--force`.

What lives where:

| Item | Location |
|---|---|
| Compose file, scripts, `.env`, `custom_files/` | The install directory (for example `~/nhvr`) |
| Containers, network, Postgres volume | Managed by Docker/Podman under the Compose project name (`nhvr-compliance` by default) |
| Database data | The Compose volume (`nhvr-compliance-pgdata` by default) |
| Images | `${IMAGE_REPO}:<service>-${IMAGE_TAG}` in your registry |

Only the web app is published. Valhalla and the compliance API are reached
through the web app's nginx at `/valhalla/` and `/api/`, so the browser only
talks to one origin.

### Non-interactive install

```bash
curl -fsSL https://raw.githubusercontent.com/KrakeKrake/P92-GeoTab-Road-Compliance/main/install.sh | bash -s -- \
  --yes \
  --nhvr-gpkg-dir /data/nhvr \
  --osm-pbf /data/victoria.osm.pbf \
  --db-password 'a-url-safe-password' \
  --image-repo docker.io/krakekrake/eat40005
```

Useful installer options:

| Option | Purpose |
|---|---|
| `--dir DIR` | Install somewhere other than the current directory |
| `--force` | Replace an existing deployment bundle in the target directory |
| `--copy-data` | Copy the GeoPackages and selected OSM PBF into `<dir>/data` (can be many GB) |
| `--project-name NAME` | Compose project/volume/network name prefix |
| `--no-pull` | Use images already on this host (no registry pull) |
| `--prepare-only` | Download and write `.env`, but do not run setup |
| `--reconfigure` | Recreate `.env` (the old one is kept as `.env.bak`) |
| `--reset-db` | Delete the existing Postgres volume first (**destroys database data**) |
| `--branch NAME` | Download from a different git branch (default `main`) |

`--copy-data` is optional. By default the installer writes absolute paths to
your existing data, so the install directory can be moved without copying a
large PBF or GeoPackage set. Use `--copy-data` only when you want a fully
portable directory.

The images are pulled from `${IMAGE_REPO}:<service>-${IMAGE_TAG}`, for example
`docker.io/krakekrake/eat40005:valhalla-latest`. If they are not published yet,
install from a checkout instead (see [Development](#development)), or push them
first and set `--image-repo`.

### If you prefer to install manually

```bash
git clone https://github.com/KrakeKrake/P92-GeoTab-Road-Compliance.git
cd P92-GeoTab-Road-Compliance
cp .env.example .env
# edit .env: NHVR_GPKG_DIR, OSM_PBF_DIR, OSM_PBF_NAME, DB_PASSWORD,
#            IMAGE_REPO / IMAGE_TAG, WEB_PORT
./setup.sh
```

`setup.sh` is safe to re-run, but it always re-imports and rebuilds the data.
Use `update.sh` for routine refreshes; it fingerprints the inputs and skips the
work when nothing changed.

## First start: what happens

`setup.sh` runs the data pipeline in order:

1. starts PostGIS (unless `DB_HOST` points at an external database) and applies
   the compliance schema and first-run seed data;
2. merges the NHVR access tags from the GeoPackages into the OSM PBF;
3. loads the same NHVR data into PostGIS for the API;
4. builds the Valhalla routing tiles (skipped when `VALHALLA_UPSTREAM` is
   external);
5. starts the stack.

The seeded vehicle templates, goods rules and compliance defaults are **initial
values only**. They are applied once, on the first startup, and are meant to be
edited in the web app afterwards. Updates never overwrite them.

The first tile build can take a while depending on the size of the extract.
Watch it with:

```bash
cd ~/nhvr
docker compose logs -f valhalla
```

## Updating the data

Put the new GeoPackages in `NHVR_GPKG_DIR` and/or replace the base `.pbf`,
then:

```bash
cd ~/nhvr
./update.sh --dry-run   # show what changed
./update.sh             # import, reload PostGIS, rebuild tiles
```

What changes and what does not:

| Data | How it updates |
|---|---|
| Valhalla routing tiles | Full rebuild. NHVR access is baked into the graph; Valhalla has no incremental tile update. |
| `nhvr_access.nhvr_network_access` (PostGIS) | Reloaded into a staging table and swapped in one transaction. The API stays available during the load. |
| Compliance / account schema | SQL migrations only. `account.users` is never dropped. |
| Seeded templates and rules | First startup only; edit them in the web app. |

The default update is **blue/green**: tiles are built in
`custom_files/.build`, then Valhalla is stopped only for the directory swap. If
something goes wrong, the previous tiles are restored.

Useful update options:

```bash
./update.sh --db-only     # only reload the PostGIS NHVR table
./update.sh --tiles-only  # rebuild tiles from the current PBF
./update.sh --simple      # rebuild in place (downtime = build time)
./update.sh --rollback    # restore custom_files/.old and restart Valhalla
./update.sh --force       # redo even if the input fingerprints match
```

`--db-only` and `--tiles-only` deliberately do not advance the update state, so
the next normal `./update.sh` completes the remaining work.

## Day-to-day commands

Run these from the install directory (the directory you installed into, for
example `~/nhvr`).

```bash
docker compose ps                 # service health
docker compose logs -f valhalla   # tile build / routing logs
docker compose logs -f web-app    # nginx/proxy logs
docker compose stop               # stop everything
docker compose start              # start it again
docker compose down               # remove containers (data volumes stay)
```

When any service lives outside this host (see
[Split deployment](#split-deployment-external-database--valhalla--api)), use
`./compose.sh` instead of `docker compose`. It derives the Compose profiles from
`.env` so a bundled container does not shadow an external one:

```bash
./compose.sh up -d web-app
./compose.sh ps
```

### Ports

The web app is the only port published in the deployment file:

| URL | Service |
|---|---|
| `http://localhost:8080` | Web app |
| `http://localhost:8080/valhalla/status` | Valhalla through the web app |
| `http://localhost:8080/api/...` | Compliance API through the web app |

Change `WEB_PORT` in `.env` and run `docker compose up -d web-app` to move it.

### Split deployment (external database / Valhalla / API)

The stack does not have to run on one host. Three `.env` values select where
each dependency lives; the bundled containers are only started when the
corresponding value is the default:

| `.env` value | Default | Bundled service runs when |
|---|---|---|
| `DB_HOST` + `DB_PORT` + `DB_SSLMODE` | `postgis:5432` | `DB_HOST=postgis` (profile `local-db`) |
| `VALHALLA_UPSTREAM` | `http://valhalla:8002` | host is `valhalla` (profile `local-valhalla`) |
| `API_UPSTREAM` | `http://compliance-api:5000` | host is `compliance-api` (profile `local-api`) |

Both upstream values are full origins without a trailing slash. The web app
still proxies `/valhalla/` and `/api/`, so `VITE_VALHALLA_URL=/valhalla` and
`VITE_NHVR_API_URL=` do not change; the browser only ever talks to the web app.

Example: local Valhalla and API, database on RDS:

```dotenv
DB_HOST=mydb.abc123.ap-southeast-2.rds.amazonaws.com
DB_PORT=5432
DB_SSLMODE=require
VALHALLA_UPSTREAM=http://valhalla:8002
API_UPSTREAM=http://compliance-api:5000
```

Then run `./setup.sh` (or `./update.sh --db-only` for an existing install).
`setup.sh`, `update.sh` and `./compose.sh` derive `COMPOSE_PROFILES` from these
values, so the bundled PostGIS is not started. Plain `docker compose` reads the
literal `COMPOSE_PROFILES` line from `.env`; either keep it in sync when you
edit the values above, or use `./compose.sh`.

External database notes:

- The role needs permission to create the `compliance`, `account` and
  `nhvr_access` schemas and the `postgis`/`pgrouting` extensions (the NHVR
  loader creates them). On RDS, use the master user or a member of
  `rds_superuser`.
- `DB_PASSWORD` must be URL-safe, because it is embedded in `DATABASE_URL`.
- The local `nhvr-compliance-pgdata` volume is not used; back the database up
  with the provider's tooling.
- `docker-compose.override.yml`'s debug port binding for `postgis` is ignored
  when the bundled container is not running.

Example: database on RDS, Valhalla and the API on their own hosts, web app here:

```dotenv
DB_HOST=mydb.abc123.ap-southeast-2.rds.amazonaws.com
DB_SSLMODE=require
VALHALLA_UPSTREAM=https://routing.internal.example.com
API_UPSTREAM=https://api.internal.example.com
```

- A host that runs the API sets `COMPOSE_PROFILES=local-api` (plus its own
  database settings) and runs `./compose.sh up -d`. Migrations run there.
- A web-only host runs just `web-app` (`./compose.sh up -d web-app`). It does
  not need `custom_files/`, the GeoPackages or the OSM extract.
- A Valhalla host builds its own tiles. `setup.sh`/`update.sh` skip the tile
  build when `VALHALLA_UPSTREAM` is external, and `--tiles-only`/`--rollback`
  refuse to run there on purpose.

### Optional tools

```bash
docker compose --profile tools up -d adminer     # DB browser on 127.0.0.1:5433
docker compose --profile external up -d valhalla-cors   # direct CORS Valhalla on 8003
```

### Backups

Back up the Postgres volume (`nhvr-compliance-pgdata` by default) and the
`custom_files/` directory. Those contain all persistent state.

### Changing the database password

`DB_PASSWORD` is applied when the Postgres volume is first created. On an
existing volume, changing `.env` alone does not change the database role:

1. update the role inside PostGIS with `ALTER ROLE`;
2. update `DB_PASSWORD` in `.env`;
3. recreate the API containers (`docker compose up -d --force-recreate db-migrate compliance-api`).

Use a URL-safe password (letters, digits, `-`, `_`) because it is embedded in a
database URL.

## Troubleshooting

**`password authentication failed for user "nhvr"` during setup.**
Postgres only applies `DB_PASSWORD` when it initialises an empty volume. If a
volume from an earlier install is still present, the new `.env` password will
not match it. A failed first install leaves that volume behind, so the next run
generates a different password and hits this error. Either keep the original
password, change the role in the running container, or erase the volume if it
holds no data:

```bash
cd ~/nhvr
docker compose down
docker volume rm nhvr-compliance-pgdata
./setup.sh              # or re-run install.sh
```

`install.sh --reset-db` does the volume removal for you. On a fresh install the
installer now refuses to generate a new password when the volume already exists.

**A port is already in use.**
Change `WEB_PORT` in `.env` (and `DB_DEBUG_PORT`, `API_DEBUG_PORT`,
`VALHALLA_DEBUG_PORT` if you are using the development override), then
`docker compose up -d`.

**The images cannot be pulled.**
Set `IMAGE_REPO` and `IMAGE_TAG` to where the images were published, or use
`--no-pull` if they are already on the host. All four images are tags in that
one repository (for example `docker.io/krakekrake/eat40005:valhalla-latest`),
which is what Docker Hub supports. Keep the repository fully qualified
(`docker.io/...`) so podman does not resolve a local short name to `localhost`.

**`docker compose up` says no compose file was found.**
Run it from the install directory (`cd ~/nhvr`) or pass the file explicitly:

```bash
docker compose -f ~/nhvr/docker-compose.yml \
  --env-file ~/nhvr/.env up -d
```

**The first run looks stuck.**
It is importing the PBF and building tiles. Follow
`docker compose logs -f valhalla`. The importer and tile builder are the long
steps.

**Valhalla is unhealthy but the web app loads.**
Check `docker compose logs valhalla`. A missing `custom_files/nhvr.osm.pbf` or a
failed tile build will leave it unhealthy; rerun `./setup.sh`.

**`custom_files` is not writable` / `mv: cannot move ... Permission denied`.**
Rootful Docker writes bind-mounted files as root, so the host-side tile
promotion cannot move them. `setup.sh` and `update.sh` now stop before the long
build if `custom_files` or `.state` is not writable and print the exact `chown`
command:

```bash
sudo chown -R "$(id -u):$(id -g)" custom_files .state
```

Set the container user to your account once as well:

```bash
cd ~/nhvr
sed -i '/^PUID=/d;/^PGID=/d' .env
printf 'PUID=%s\nPGID=%s\n' "$(id -u)" "$(id -g)" >> .env
sudo chown -R "$(id -u):$(id -g)" custom_files
docker compose up -d --force-recreate valhalla valhalla-tiles nhvr-tools
./setup.sh
```

If the install predates the `user:` mappings, update the bundle first by
running the installer from outside the install directory:

```bash
cd /tmp
curl -fsSL https://raw.githubusercontent.com/KrakeKrake/P92-GeoTab-Road-Compliance/main/install.sh \
  | bash -s -- --dir ~/nhvr --force --no-pull
```

If the tiles were already built in `custom_files/.build` and only the promotion
failed, you can finish without rebuilding:

```bash
cp -a custom_files/.build/. custom_files/
docker compose up -d
```

New installs on rootful Docker set `PUID`/`PGID` automatically. Rootless
Podman uses `0`/`0` (container root maps to your user) and needs no change.
Re-running `install.sh` over an existing install adds missing `PUID`/`PGID` (and
the topology keys) to `.env`, replaces a `0:0` pair on rootful Docker, and warns
when the values do not match the user running the installer.

**I changed an image or `.env` and nothing happened.**
The web app's `VITE_*` values are injected at container start, so recreate the
container after changing them: `docker compose up -d web-app`. Changing
`IMAGE_REPO`, `IMAGE_TAG`, or the compose file requires
`docker compose up -d` (and `pull` first for a registry change).

**SELinux hosts.**
The data mounts use the `:z` relabel option. It is harmless on non-SELinux
systems.

## Development

Only needed if you want to change the code or build the images yourself.

```bash
git clone https://github.com/KrakeKrake/P92-GeoTab-Road-Compliance.git
cd P92-GeoTab-Road-Compliance
cp .env.example .env
# edit .env, then:
./setup.sh
```

`docker-compose.yml` is the deployment definition (images only).
`docker-compose.override.yml` adds the build contexts and localhost debug ports,
and is loaded automatically for `docker compose` commands in this directory.

Build and publish the images:

```bash
# set IMAGE_REPO and IMAGE_TAG in .env first
docker compose build
docker compose push
```

If your Compose version also tries to push the pulled images, add
`--ignore-push-failures`.

`setup.sh` reuses an existing `localhost/valhalla:nhvr` image (tagging it as
`${IMAGE_REPO}:valhalla-${IMAGE_TAG}`) instead of recompiling Valhalla.
The Valhalla build is the long part; the other images build in a few minutes.

For a server that only needs the deployment definition:

```bash
export COMPOSE_FILE=docker-compose.yml
docker compose -f docker-compose.yml pull
docker compose -f docker-compose.yml up -d
```

Tests for the web app:

```bash
cd web-app
npm ci
npm run typecheck
npm run lint
npx vitest run
```

Note: the repository has some pre-existing Vitest failures in map/directions
specs that are unrelated to the deployment changes.

# Uninstalling
Notably when uninstalling to reinstall, it is possible that three docker rementants remains, these can be removed by: 
```bash
docker stop nhvr-compliance-postgis-1
docker rm nhvr-compliance-postgis-1
docker volume rm nhvr-compliance-pgdata
```
