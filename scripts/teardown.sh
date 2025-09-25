#!/usr/bin/env bash

set -euo pipefail

REMOVE_IMAGE=0
REMOVE_DATA=0

usage() {
  cat <<EOF
Usage: $0 [--remove-image|-i] [--remove-data]

Stops the running container and optionally removes the built image and local data directory.

Options:
  -i, --remove-image   Remove the built image (excalidraw-fastapi:latest)
      --remove-data    Remove local ./data directory (filesystem storage data)
  -h, --help           Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--remove-image) REMOVE_IMAGE=1; shift;;
    --remove-data) REMOVE_DATA=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

echo "[i] Stopping container 'excalidraw' (if running)"
docker rm -f excalidraw >/dev/null 2>&1 || true

if [[ "$REMOVE_IMAGE" -eq 1 ]]; then
  echo "[i] Removing image excalidraw-fastapi:latest"
  docker rmi -f excalidraw-fastapi:latest || true
fi

if [[ "$REMOVE_DATA" -eq 1 ]]; then
  echo "[i] Removing ./data directory"
  rm -rf ./data
fi

echo "[i] Teardown complete."
