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

### Option 2: Direct Docker Compose

```bash
docker-compose up --build
```

Visit http://127.0.0.1:8888

## Admin Interface

The service includes a web-based admin interface for managing saved canvases:

**Access:** http://127.0.0.1:8888/admin

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

Configure the following environment variables in `docker-compose.yml`:

- `STORAGE_TYPE`: `memory` or `filesystem`
- `LOCAL_STORAGE_PATH`: data path for filesystem storage (default `/app/data`)
- `FRONTEND_DIR`: static assets path (default `/app/frontend/build`)

## Scripts

The `scripts/` directory contains helper scripts for easier service management:

### `build_and_up.sh`

Builds the Docker image and starts the service with docker-compose.

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

## Notes

- Frontend is automatically cloned and built inside the container
- Static site is served from `FRONTEND_DIR` with SPA fallback to `index.html`
- Admin endpoints are unauthenticated by default; protect them behind a reverse proxy or network ACL in production
- Frontend environment variables can be adjusted by editing the `.env.excalidraw` file
