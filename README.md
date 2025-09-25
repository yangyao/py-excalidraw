# Excalidraw All-in-One

All-in-one Excalidraw service using a Python FastAPI backend — simple and compatible with Excalidraw's raw-bytes protocol and Firebase-like routes.

## Features

- Serves the built Excalidraw frontend from `./frontend/build`.
- Document persistence API compatible with Excalidraw's save/load:
  - `POST /api/v2/post/` → `{ "id": "..." }`
  - `GET /api/v2/{id}/` → returns saved binary payload
- **Web-based admin interface** for managing saved canvases:
  - View all saved documents with metadata (size, creation time, custom names)
  - Set custom names for better organization
  - Open documents directly in new tabs
  - Delete documents with confirmation
- Minimal Firebase proxy emulation used by Excalidraw:
  - `POST /v1/projects/{project}/databases/{db}/documents:commit`
  - `POST /v1/projects/{project}/databases/{db}/documents:batchGet`
- Pluggable storage backends: memory (default) and filesystem.

## Quick Start

### Option 1: Using Scripts (Recommended)

Use the provided scripts for easier management:

```bash
# Build and start the service (detached by default)
./scripts/build_and_up.sh

# Or with specific Excalidraw version
EXCALIDRAW_REF=v0.17.3 ./scripts/build_and_up.sh

# Or run in foreground
./scripts/build_and_up.sh --no-detach
```

Stop the service:

```bash
# Basic teardown
./scripts/teardown.sh

# Remove image and data
./scripts/teardown.sh --remove-image --remove-data
```

### Option 2: Plain Docker

Build the image with your public origin baked into the frontend, then run the container:

```bash
# Build (amd64), set your public origin for the frontend
docker buildx build \
  --platform linux/amd64 \
  --build-arg PUBLIC_ORIGIN="http://127.0.0.1:8888" \
  -t excalidraw-fastapi:latest \
  --load .

# Run (filesystem storage persisted to ./data)
mkdir -p ./data
docker run -d \
  --name excalidraw \
  --restart=always \
  -p 8888:8888 \
  -e STORAGE_TYPE=filesystem \
  -e LOCAL_STORAGE_PATH=/app/data \
  -e PUBLIC_ORIGIN="http://127.0.0.1:8888" \
  -v $(pwd)/data:/app/data \
  excalidraw-fastapi:latest

echo "Open http://127.0.0.1:8888"
```

## Admin Interface

The service includes a web-based admin interface for managing saved canvases:

**Access:** http://127.0.0.1:8888/admin

Admin links origin
- The admin page's “Open” buttons point to the main app origin.
- Configure this via runtime env `PUBLIC_ORIGIN` (e.g., `https://chart.example.com`).
- In Docker: set `PUBLIC_ORIGIN` via `-e PUBLIC_ORIGIN=...` when running the container.

### Features

- **View all saved canvases** with creation time, file size, and custom names
- **Set custom names** for canvases (useful for organization)
- **Open canvases** directly in new tabs
- **Delete canvases** with confirmation
- **Refresh** the list to see latest changes

### Admin API Endpoints

- `GET /admin` — Web interface for canvas management
- `GET /api/v2/admin/documents` — JSON list of all documents with metadata
- `POST /api/v2/admin/documents/{id}/name` — Set custom name for a document

The admin interface is unauthenticated by default. For production use, consider protecting it behind authentication or network restrictions.

## APIs

### Document Management
- POST `/api/v2/post/` — body is raw bytes, returns `{ "id": "..." }`
- GET `/api/v2/{id}/` — returns raw bytes
- DELETE `/api/v2/{id}` — delete a document by id

### Admin Interface
- GET `/admin` — web interface for managing saved canvases
- GET `/api/v2/admin/documents` — list saved documents (id, size, createdAt, name)
- POST `/api/v2/admin/documents/{id}/name` — set document name

### Firebase Compatibility
- POST `/v1/projects/{project}/databases/{db}/documents:commit`
- POST `/v1/projects/{project}/databases/{db}/documents:batchGet`

## Storage Backends

- memory: in-process, non-persistent (default)
- filesystem: set `STORAGE_TYPE=filesystem` and `LOCAL_STORAGE_PATH=./data` (or any directory)

## Environment Variables

At runtime (container env):
- `STORAGE_TYPE`: `memory` or `filesystem`
- `LOCAL_STORAGE_PATH`: data path for filesystem storage (default `/app/data`)
- `PUBLIC_ORIGIN`: public origin used by the admin page to open documents on the main site

## Scripts

The `scripts/` directory contains helper scripts for easier service management:

### `build_and_up.sh`

Builds the Docker image and starts the service with plain Docker.

**Usage:**
```bash
./scripts/build_and_up.sh [options]
```

**Options:**
- `-r, --repo REPO`: Excalidraw repository URL (default: https://github.com/excalidraw/excalidraw.git)
- `-t, --ref REF`: Git reference (branch/tag/commit) (default: master)
- `--no-detach`: Run in foreground instead of detached mode
- `-h, --help`: Show help

**Examples:**
```bash
# Default build and start
./scripts/build_and_up.sh

# Use specific Excalidraw version
./scripts/build_and_up.sh -t v0.17.3

# Run in foreground
./scripts/build_and_up.sh --no-detach
```

### `teardown.sh`

Stops the service and optionally removes images and data.

**Usage:**
```bash
./scripts/teardown.sh [options]
```

**Options:**
- `-i, --remove-image`: Remove the built Docker image
- `--remove-data`: Remove local data directory
- `-h, --help`: Show help

**Examples:**
```bash
# Basic teardown
./scripts/teardown.sh

# Complete cleanup
./scripts/teardown.sh --remove-image --remove-data
```

## Build Arguments

- `EXCALIDRAW_REPO`: upstream repository URL
- `EXCALIDRAW_REF`: branch/tag/commit hash
- `PUBLIC_ORIGIN` (build arg): used to generate frontend endpoints baked into static assets
- `WS_ORIGIN` (build arg): websocket origin; defaults to `PUBLIC_ORIGIN` if omitted

### Frontend endpoints without editing source

To avoid hardcoding your domain in the repo, the image build can generate the Excalidraw `.env` automatically when you pass `PUBLIC_ORIGIN` (and optionally `WS_ORIGIN`). This removes the need to edit `.env.excalidraw.production`.

- `PUBLIC_ORIGIN` (optional): scheme and host where users access the app, e.g. `https://your-domain.example`.
- `WS_ORIGIN` (optional): WebSocket origin; defaults to `PUBLIC_ORIGIN` if omitted.

Example (docker buildx):

```
docker buildx build \
  --platform linux/amd64 \
  --build-arg PUBLIC_ORIGIN="https://chart.example.com" \
  -t excalidraw-fastapi:latest \
  --load .
```

Example (plain Docker run shown above; no compose required)

What gets configured at build time:

- `VITE_APP_BACKEND_V2_GET_URL` → `${PUBLIC_ORIGIN}/api/v2/`
- `VITE_APP_BACKEND_V2_POST_URL` → `${PUBLIC_ORIGIN}/api/v2/post/`
- `VITE_APP_PLUS_LP` and `VITE_APP_PLUS_APP` → `${PUBLIC_ORIGIN}`
- `VITE_APP_AI_BACKEND` → `${PUBLIC_ORIGIN}/ai/`
- `VITE_APP_WS_SERVER_URL` → `${WS_ORIGIN:-PUBLIC_ORIGIN}`

## Notes

- Frontend is automatically cloned and built inside the container
- Static site is served from `FRONTEND_DIR` with SPA fallback to `index.html`
- Admin endpoints are unauthenticated by default; protect them behind a reverse proxy or network ACL in production
- Frontend endpoints are configured at build time via `PUBLIC_ORIGIN`/`WS_ORIGIN` build args (no local source edits needed)
- Admin page uses runtime env `PUBLIC_ORIGIN` for cross-domain “Open” links (e.g., admin subdomain → app domain)

## Deploy via GitHub Actions

This repo includes a workflow `.github/workflows/deploy.yml` that builds an image and deploys it to a remote Linux server via SSH.

Prerequisites on the server
- Docker Engine installed, with the target user able to run `docker` (in the `docker` group).
- Open TCP ports as needed (e.g., 8888 for direct access; or run Caddy in front).

Repository secrets (required)
- `SERVER_HOST`: server IP or hostname
- `SERVER_USER`: SSH username
- `SERVER_SSH_KEY`: private key content for the SSH user
- `PUBLIC_ORIGIN`: the public origin for the app, e.g. `https://chart.example.com`
- Optional `WS_ORIGIN`: WebSocket origin; defaults to `PUBLIC_ORIGIN` if not set

How it works
- Builds an amd64 image with build args `PUBLIC_ORIGIN` and `WS_ORIGIN` baked into the frontend.
- Saves the image to a tarball, uploads `image.tar.gz` to the server.
- On the server:
  - Stages files into `${REMOTE_DIR}` (default `/opt/py-excalidraw`).
  - Loads the image via `docker load`.
  - Restarts a single container `excalidraw` with `docker run -d` (port 8888, persistent volume `${REMOTE_DIR}/data:/app/data`, env `PUBLIC_ORIGIN`).

Usage
- Automatic: push to `main` triggers the workflow.
- Manual: use “Run workflow” in Actions; you may optionally override `excalidraw_repo` and `excalidraw_ref`.

Troubleshooting
- Platform mismatch: the workflow builds `linux/amd64` and loads locally to avoid arm64/amd64 issues.
- Permissions: if Docker requires sudo on your server, add the SSH user to the `docker` group or adapt the workflow to prefix `sudo` where needed.

## Caddy Reverse Proxy (Dual Domains)

Goal
- Serve the app at `chart.example.com`.
- Serve the admin at `chart-admin.example.com`, with `/` rewritten to `/admin`.

Host (bare‑metal) Caddy
- Caddyfile:

```
chart.example.com {
  encode zstd gzip
  reverse_proxy 127.0.0.1:8888 {
    header_up Host {host}
    header_up X-Forwarded-Proto {scheme}
  }
}

chart-admin.example.com {
  encode zstd gzip
  @root path /
  rewrite @root /admin
  reverse_proxy 127.0.0.1:8888 {
    header_up Host {host}
    header_up X-Forwarded-Proto {scheme}
  }
}
```

- DNS: point both domains to the server IP (A/AAAA records).
- Reload: `caddy reload --config /etc/caddy/Caddyfile`.

Dockerized Caddy
- Example compose service:

```
services:
  caddy:
    image: caddy:2
    container_name: caddy
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on: [excalidraw]

volumes:
  caddy_data:
  caddy_config:
```

- In the Caddyfile, change upstream to `excalidraw:8888` when proxying within the compose network.

Notes
- Caddy will manage TLS automatically via Let's Encrypt; ensure ports 80/443 are open and DNS is correct.
- Using a separate admin domain forces full-page navigation to `/admin`, avoiding SPA/Service Worker interception on the main app origin.
