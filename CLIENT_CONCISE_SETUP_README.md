# GeoTab Road Compliance — Client Installation Guide

Install the heavy-vehicle compliance web application, PostgreSQL database, Compliance API, and Valhalla routing service using Docker.

## 1. Prerequisites

Before installing, you need:

- **Docker Desktop** (Windows or macOS), or Docker Engine with **Docker Compose v2** (Linux). Docker must be running.
- **Windows users:** WSL 2 with Ubuntu, with Ubuntu enabled in Docker Desktop's **Settings → Resources → WSL Integration**. Run the installation commands below in the **Ubuntu / WSL terminal**, not PowerShell.
- **One or more NHVR network GeoPackage files** (`*.gpkg`), stored together in a folder.
- **One OpenStreetMap extract** (`*.osm.pbf`) for the region you will route through.
- **Access to the project's published Docker images.** The default image repository used by the installer is `docker.io/krakekrake/eat40005`
- At least **10 GB of free disk space** for a state-sized extract; allow more for larger datasets.

### Where to obtain the map data

- NHVR network data: [NHVR download instructions](https://support.nhvr.gov.au/en/articles/12687520-how-to-download-nhvr-network-data). Download the required networks as `.gpkg` files.
- OpenStreetMap: [Geofabrik Australia extracts](https://download.geofabrik.de/australia-oceania/australia.html). For Victoria, download `victoria-latest.osm.pbf` from the [Victoria extract page](https://download.geofabrik.de/australia-oceania/australia/victoria.html).

These are **two separate datasets**. An OpenStreetMap GeoPackage is not a substitute for an NHVR network GeoPackage. The installer reads these files locally; it does not upload them.

## 2. Check that Docker is available

Open a Linux / Ubuntu terminal and run:

```bash
docker compose version
docker info
```

Both commands must complete successfully. If `docker` is unavailable in Ubuntu, start Docker Desktop and enable integration for that Ubuntu distribution.

## 3. Install the complete system

**Copy and paste these commands into the Linux / Ubuntu terminal:**

```bash
mkdir -p ~/nhvr && cd ~/nhvr
curl -fsSL https://raw.githubusercontent.com/KrakeKrake/P92-GeoTab-Road-Compliance/main/install.sh | bash
```

The installer will prompt you for:

1. **Installation directory:** accept the default unless you need a different location.
2. **NHVR GeoPackage directory:** the folder containing your downloaded `.gpkg` files.
3. **OSM PBF file:** the full path to the downloaded `.osm.pbf` file.
4. **Database password:** enter a private, URL-safe password (letters, digits, `_`, `-`), or press Enter to generate one when offered.  (Default password: change-me-to-a-url-safe-password)
5. **Docker image repository:** use the repository supplied by the project owner (the installer defaults to `docker.io/krakekrake/eat40005`).
6. **Web port:** press Enter to use `8080`, or choose another available port.

The installer downloads the deployment configuration, pulls the prebuilt images, starts PostgreSQL, applies the initial database migrations and seeds, imports the NHVR map data, creates Valhalla tiles, and starts the application. The initial import and tile build can take some time.

**Important:** Run this installer from a **separate deployment directory**, such as `~/nhvr`. Do **not** run it inside a cloned source-code repository.

## 4. Open the application

Once setup completes, open the following URLs in a browser **on the computer running Docker**:

| Service | Address |
| --- | --- |
| Web application | http://localhost:8080 |
| Compliance API test | http://localhost:8080/api/compliance/profiles-by-licence/HC |
| Valhalla status | http://localhost:8080/valhalla/status |

If you selected a different web port, replace `8080` in the links.

## 5. Start, stop, and check the system

In your Linux / Ubuntu terminal:

```bash
cd ~/nhvr
```

Check running services:

```bash
docker compose ps
```

Stop services without deleting the database:

```bash
docker compose stop
```

Start existing services again:

```bash
docker compose start
```

View application logs:

```bash
docker compose logs --tail=100 web-app
docker compose logs --tail=100 compliance-api
docker compose logs --tail=100 valhalla
```

The normal startup commands **do not require rerunning the installer**.

## 6. Optional — View the database in a web browser

From the installation directory, run:

```bash
docker compose --profile tools up -d adminer
```

Open **http://localhost:5433** and enter:

| Adminer field | Value |
| --- | --- |
| System | PostgreSQL |
| Server | `postgis` |
| Username | `nhvr` (or the configured `DB_USER`) |
| Password | The database password configured during installation |
| Database | `nhvr_compliance` (or the configured `DB_NAME`) |

Adminer is for database inspection/administration; clients who only use the web application do not need it.

## 7. Updating the datasets

If the NHVR GeoPackages or OSM extract has changed, use the project's update script instead of installing again:

```bash
cd ~/nhvr
./update.sh --dry-run
./update.sh
```

The update process can rebuild Valhalla routing tiles. Consult the project owner before replacing production datasets.

## Troubleshooting

| Issue | What to check |
| --- | --- |
| `docker: command not found` in WSL | Docker Desktop is running and WSL Integration is enabled for Ubuntu. |
| `pull access denied` | The project owner must publish the correct images or grant you access to the registry. The installer cannot download unpublished or inaccessible images. |
| Missing `.gpkg` or `.osm.pbf` | Confirm the paths entered in the installer exist **inside the Linux / WSL environment**. |
| `pipefail` / `$'\r'` errors | A downloaded shell script may have Windows CRLF line endings. Contact the project owner for a release with Unix LF line endings; do not manually change application files. |
| Web app does not load | Run `docker compose ps` and `docker compose logs --tail=100 web-app` from `~/nhvr`. |
| Port `8080` already in use | Choose another web port during installation or contact the project owner to update the configuration. |
| Database password fails after reinstall | An existing PostgreSQL volume may retain its original password. Contact the project owner; **do not delete volumes unless the data can be discarded**. |

## Important data-safety notes

- **Do not run** `docker compose down -v`, `--reset-db`, or `--reset-compliance` unless you intentionally want to remove data.
- Keep the database password private. Do not include it in screenshots, support messages, or Git commits.
- The URLs above use `localhost`, so they are intended for use on the installation machine. Remote access requires additional deployment and security configuration.
- This guide installs the published version from **`main`**, not an unmerged development branch.

For advanced configuration and development, consult the project's main `README.md`.
