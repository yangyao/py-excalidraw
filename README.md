# Excalidraw All‑in‑One

All‑in‑one Excalidraw deployment with a Python FastAPI backend. Ships a built frontend, a simple persistence API compatible with Excalidraw, and a lightweight admin UI.

## Table of Contents
- Overview
- Quick Start
- Configuration
- Admin UI
- APIs
- Build & Deploy (GitHub Actions)
- Reverse Proxy (Caddy)
- Maintenance (Makefile)
- Troubleshooting
- Notes

## Overview
- Serves the Excalidraw frontend (built inside the image).
- Save/load binary protocol compatible with Excalidraw.
- Simple web admin to list/open/delete documents and set names (stores share keys server‑side so items are directly openable).
- Minimal Firebase proxy endpoints used by Excalidraw.
- Storage backends: memory (default) or filesystem.

## Quick Start

```bash
# Build
make build

# Start (detached)
make up

# Specific upstream version
make build EXCALIDRAW_REF=v0.17.3

# Foreground
make up-fg

# Stop / cleanup
make down
make clean-image
make clean-data
```

Note: Without make, you can run the equivalent `docker buildx` and `docker run` commands directly.

## Configuration

Build‑time (frontend endpoints)
- `PUBLIC_ORIGIN` (required for production): e.g., `https://chart.example.com`
- `WS_ORIGIN` (optional): defaults to `PUBLIC_ORIGIN`
- `EXCALIDRAW_REPO` (optional): upstream repo URL (default official)
- `EXCALIDRAW_REF` (optional): branch/tag/commit (default `master`)

Runtime (container env)
- `STORAGE_TYPE`: `memory` | `filesystem`
- `LOCAL_STORAGE_PATH`: data path for filesystem storage (default `/app/data`)
- `PUBLIC_ORIGIN`: admin page uses this origin when opening documents in the main app

## Admin UI

Access
- `http://127.0.0.1:8888/admin`

Behavior
- Admin lists only canvases that have a stored share key (i.e., can be opened).
- Use "Add Canvas" to paste a share link and optional name; Admin stores the key server-side so Open/Copy Link work directly on `PUBLIC_ORIGIN`.

Security
- The admin page is unauthenticated by default. Protect it via reverse proxy auth, IP allowlist, VPN, etc., for production.
- Storing share keys on the server makes canvases openable from Admin and weakens pure end‑to‑end secrecy; restrict Admin access.

## APIs

Document management
- `POST /api/v2/post/` — body is raw bytes → `{ "id": "..." }`
- `GET /api/v2/{id}/` — returns raw bytes
- `DELETE /api/v2/{id}` — delete by id

Admin
- `GET /admin` — web interface
- `GET /api/v2/admin/documents` — list only openable items: id, size, createdAt, name, shareLink
- `POST /api/v2/admin/documents/{id}/name` — set name
- `POST /api/v2/admin/documents/{id}/meta` — set name and share key (parsed from share link)

Firebase compatibility
- `POST /v1/projects/{project}/databases/{db}/documents:commit`
- `POST /v1/projects/{project}/databases/{db}/documents:batchGet`

## Build & Deploy (GitHub Actions)

This repo includes `.github/workflows/deploy.yml` to build and deploy to a remote Linux server via SSH.

Server prerequisites
- Docker Engine installed; the SSH user can run `docker` (in `docker` group).
- Open necessary ports (e.g., 8888; or place Caddy/NGINX in front).

Repository secrets (required)
- `SERVER_HOST`: server IP/hostname
- `SERVER_USER`: SSH username
- `SERVER_SSH_KEY`: private key for SSH auth
- `PUBLIC_ORIGIN`: public origin (e.g., `https://chart.example.com`)
- Optional `WS_ORIGIN`: WebSocket origin (defaults to PUBLIC_ORIGIN)

What the workflow does
```
push to main
  → Buildx build (linux/amd64) with PUBLIC_ORIGIN/WS_ORIGIN baked into frontend
  → docker save image.tar.gz and upload to server via SCP
  → SSH: docker load → rm -f old container → docker run -d with env + volume
  → (Optional) Caddy proxies 80/443 to :8888
```

Usage
- Automatic: push to `main` triggers the workflow.
- Manual: “Run workflow” in Actions; you can override `excalidraw_repo` and `excalidraw_ref`.

Troubleshooting
- Platform mismatch: the workflow builds for `linux/amd64` to avoid arm64/amd64 conflicts.
- Permissions: add SSH user to `docker` group, or adapt the workflow to use `sudo docker`.

## Reverse Proxy (Caddy)

Goal
- Serve app at `chart.example.com`.
- Serve admin at `chart-admin.example.com`, rewriting `/` → `/admin`.

Host Caddyfile (bare metal)

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

Dockerized Caddy (example service)

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

Notes
- Caddy will manage TLS automatically; ensure ports 80/443 are open and DNS points to the server.
- Using a separate admin domain forces full‑page navigation (avoids SPA/Service Worker interception).

## Maintenance (Makefile)

Targets
- `make build` — build image (amd64) with frontend URLs baked in
- `make up` — start container detached (recreates if exists)
- `make up-fg` — start container in foreground
- `make down` — stop & remove container
- `make logs` — follow logs
- `make ps` — show container status
- `make clean-image` — remove built image
- `make clean-data` — remove local `./data`

Variables (override via CLI or env)
- `EXCALIDRAW_REPO`, `EXCALIDRAW_REF`
- `PUBLIC_ORIGIN`, `WS_ORIGIN`
- `IMAGE`, `CONTAINER`, `PORT`, `DATA_DIR`

## Troubleshooting
- App not reachable:
  - Check `docker ps` and `docker logs --tail 200 excalidraw`.
  - Ensure port mapping `-p 8888:8888` and firewall rules.
- Admin page opens on wrong origin:
  - Set runtime env `PUBLIC_ORIGIN` to your main app domain.
- Platform mismatch (arm64 host build → amd64 server):
  - Build with `--platform linux/amd64` (already in CI and scripts).
- Filesystem storage not persisted:
  - Ensure volume mount to `/app/data` and `STORAGE_TYPE=filesystem`.

## Notes
- Frontend is cloned and built during the image build.
- Static site is served with SPA fallback (`index.html`).
- Admin endpoints are unauthenticated; protect in production.
- Frontend URLs are set at build time via `PUBLIC_ORIGIN`/`WS_ORIGIN`.
- Admin page uses runtime `PUBLIC_ORIGIN` to open docs on the main app origin.
