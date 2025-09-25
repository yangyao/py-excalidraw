#!/usr/bin/env bash

set -euo pipefail

# Defaults (can be overridden via env or flags)
EXCALIDRAW_REPO_DEFAULT="https://github.com/excalidraw/excalidraw.git"
EXCALIDRAW_REF_DEFAULT="master"

EXCALIDRAW_REPO="${EXCALIDRAW_REPO:-$EXCALIDRAW_REPO_DEFAULT}"
EXCALIDRAW_REF="${EXCALIDRAW_REF:-$EXCALIDRAW_REF_DEFAULT}"

usage() {
  cat <<EOF
Usage: $0 [-r REPO] [-t REF] [--no-detach]

Builds the Docker image (with frontend cloned & built inside) and starts the service via docker-compose.

Options:
  -r, --repo REPO   Excalidraw repo URL (default: ${EXCALIDRAW_REPO_DEFAULT})
  -t, --ref REF     Excalidraw git ref (branch/tag/commit) (default: ${EXCALIDRAW_REF_DEFAULT})
  --no-detach       Run docker-compose up in foreground (default: detached)
  -h, --help        Show this help

Environment variables also supported:
  EXCALIDRAW_REPO, EXCALIDRAW_REF

Examples:
  EXCALIDRAW_REF=v0.17.3 $0
  $0 -r https://github.com/excalidraw/excalidraw.git -t master
EOF
}

DETACH=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--repo)
      EXCALIDRAW_REPO="$2"; shift 2;;
    -t|--ref)
      EXCALIDRAW_REF="$2"; shift 2;;
    --no-detach)
      DETACH=0; shift;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown argument: $1" >&2; usage; exit 1;;
  esac
done

# Choose docker compose command
if command -v docker-compose >/dev/null 2>&1; then
  DCMD=(docker-compose)
elif docker compose version >/dev/null 2>&1; then
  DCMD=(docker compose)
else
  echo "docker-compose or docker compose is required" >&2
  exit 1
fi

# Ensure data dir exists (used when STORAGE_TYPE=filesystem)
mkdir -p data

export EXCALIDRAW_REPO
export EXCALIDRAW_REF

echo "[i] Building image with EXCALIDRAW_REPO=${EXCALIDRAW_REPO} EXCALIDRAW_REF=${EXCALIDRAW_REF}"
"${DCMD[@]}" build

echo "[i] Starting service (detached=${DETACH})"
if [[ "$DETACH" -eq 1 ]]; then
  "${DCMD[@]}" up -d
  echo "[i] Service is up: http://localhost:8888"
else
  "${DCMD[@]}" up
fi

