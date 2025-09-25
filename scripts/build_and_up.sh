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

Builds the Docker image (with frontend cloned & built inside) and starts the service via plain Docker.

Options:
  -r, --repo REPO   Excalidraw repo URL (default: ${EXCALIDRAW_REPO_DEFAULT})
  -t, --ref REF     Excalidraw git ref (branch/tag/commit) (default: ${EXCALIDRAW_REF_DEFAULT})
  --no-detach       Run container in foreground (default: detached)
  -h, --help        Show this help

Environment variables also supported:
  EXCALIDRAW_REPO, EXCALIDRAW_REF
  PUBLIC_ORIGIN (frontend + admin links, default http://127.0.0.1:8888)
  WS_ORIGIN      (WebSocket origin, defaults to PUBLIC_ORIGIN)

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

# Ensure data dir exists (used when STORAGE_TYPE=filesystem)
mkdir -p data

export EXCALIDRAW_REPO
export EXCALIDRAW_REF

IMAGE_NAME="excalidraw-fastapi:latest"

echo "[i] Building image with EXCALIDRAW_REPO=${EXCALIDRAW_REPO} EXCALIDRAW_REF=${EXCALIDRAW_REF} PUBLIC_ORIGIN=${PUBLIC_ORIGIN:-http://127.0.0.1:8888} WS_ORIGIN=${WS_ORIGIN:-(default)}"
if docker buildx version >/dev/null 2>&1; then
  docker buildx build \
    --platform linux/amd64 \
    --build-arg EXCALIDRAW_REPO="$EXCALIDRAW_REPO" \
    --build-arg EXCALIDRAW_REF="$EXCALIDRAW_REF" \
    --build-arg PUBLIC_ORIGIN="${PUBLIC_ORIGIN:-http://127.0.0.1:8888}" \
    --build-arg WS_ORIGIN="${WS_ORIGIN:-}" \
    -t "$IMAGE_NAME" \
    --load \
    .
else
  echo "[!] docker buildx not found; using docker build (no cross-platform)" >&2
  docker build \
    --build-arg EXCALIDRAW_REPO="$EXCALIDRAW_REPO" \
    --build-arg EXCALIDRAW_REF="$EXCALIDRAW_REF" \
    --build-arg PUBLIC_ORIGIN="${PUBLIC_ORIGIN:-http://127.0.0.1:8888}" \
    --build-arg WS_ORIGIN="${WS_ORIGIN:-}" \
    -t "$IMAGE_NAME" \
    .
fi

echo "[i] (Re)starting container"
docker rm -f excalidraw >/dev/null 2>&1 || true

RUN_FLAGS=(
  --name excalidraw
  --restart=always
  -p 8888:8888
  -e STORAGE_TYPE=filesystem
  -e LOCAL_STORAGE_PATH=/app/data
  -e PUBLIC_ORIGIN="${PUBLIC_ORIGIN:-http://127.0.0.1:8888}"
  -v "$PWD/data:/app/data"
)

if [[ "$DETACH" -eq 1 ]]; then
  docker run -d "${RUN_FLAGS[@]}" "$IMAGE_NAME"
  echo "[i] Service is up: http://localhost:8888"
else
  docker run "${RUN_FLAGS[@]}" "$IMAGE_NAME"
fi
