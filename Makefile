SHELL := /bin/bash

# Image/container config
IMAGE ?= excalidraw-fastapi:latest
CONTAINER ?= excalidraw
PORT ?= 8888
DATA_DIR ?= $(PWD)/data

# Excalidraw upstream
EXCALIDRAW_REPO ?= https://github.com/excalidraw/excalidraw.git
EXCALIDRAW_REF ?= master

# Frontend/public endpoints (build-time + runtime)
PUBLIC_ORIGIN ?= http://127.0.0.1:8888
WS_ORIGIN ?=

.PHONY: help build up up-fg down logs ps rebuild clean-image clean-data

help:
	@echo "Targets:"
	@echo "  build       Build image (amd64) with PUBLIC_ORIGIN baked in"
	@echo "  up          Run container detached (recreate if exists)"
	@echo "  up-fg       Run container in foreground"
	@echo "  down        Stop and remove container"
	@echo "  logs        Follow container logs"
	@echo "  ps          Show container status"
	@echo "  rebuild     build + up"
	@echo "  clean-image Remove built image"
	@echo "  clean-data  Remove local ./data"
	@echo ""
	@echo "Variables (override via env or CLI):"
	@echo "  EXCALIDRAW_REPO, EXCALIDRAW_REF, PUBLIC_ORIGIN, WS_ORIGIN, IMAGE, CONTAINER, PORT, DATA_DIR"

build:
	@echo "[i] Building $(IMAGE) with EXCALIDRAW_REPO=$(EXCALIDRAW_REPO) EXCALIDRAW_REF=$(EXCALIDRAW_REF) PUBLIC_ORIGIN=$(PUBLIC_ORIGIN) WS_ORIGIN=$(WS_ORIGIN)"
	@if docker buildx version >/dev/null 2>&1; then \
		docker buildx build \
		  --platform linux/amd64 \
		  --build-arg EXCALIDRAW_REPO="$(EXCALIDRAW_REPO)" \
		  --build-arg EXCALIDRAW_REF="$(EXCALIDRAW_REF)" \
		  --build-arg PUBLIC_ORIGIN="$(PUBLIC_ORIGIN)" \
		  --build-arg WS_ORIGIN="$(WS_ORIGIN)" \
		  -t "$(IMAGE)" \
		  --load \
		  . ; \
	else \
		echo "[!] docker buildx not found; using docker build (no cross-platform)" >&2; \
		docker build \
		  --build-arg EXCALIDRAW_REPO="$(EXCALIDRAW_REPO)" \
		  --build-arg EXCALIDRAW_REF="$(EXCALIDRAW_REF)" \
		  --build-arg PUBLIC_ORIGIN="$(PUBLIC_ORIGIN)" \
		  --build-arg WS_ORIGIN="$(WS_ORIGIN)" \
		  -t "$(IMAGE)" \
		  . ; \
	fi

up: ## Run detached
	@mkdir -p "$(DATA_DIR)"
	@echo "[i] (Re)starting container $(CONTAINER) on :$(PORT)"
	-@docker rm -f "$(CONTAINER)" >/dev/null 2>&1 || true
	@docker run -d \
	  --name "$(CONTAINER)" \
	  --restart=always \
	  -p "$(PORT):8888" \
	  -e STORAGE_TYPE=filesystem \
	  -e LOCAL_STORAGE_PATH=/app/data \
	  -e PUBLIC_ORIGIN="$(PUBLIC_ORIGIN)" \
	  -v "$(DATA_DIR):/app/data" \
	  "$(IMAGE)"
	@echo "[i] Up: http://127.0.0.1:$(PORT)"

up-fg: ## Run foreground
	@mkdir -p "$(DATA_DIR)"
	-@docker rm -f "$(CONTAINER)" >/dev/null 2>&1 || true
	@docker run \
	  --name "$(CONTAINER)" \
	  -p "$(PORT):8888" \
	  -e STORAGE_TYPE=filesystem \
	  -e LOCAL_STORAGE_PATH=/app/data \
	  -e PUBLIC_ORIGIN="$(PUBLIC_ORIGIN)" \
	  -v "$(DATA_DIR):/app/data" \
	  "$(IMAGE)"

down:
	@echo "[i] Stopping $(CONTAINER)"
	-@docker rm -f "$(CONTAINER)" >/dev/null 2>&1 || true

logs:
	@docker logs -f "$(CONTAINER)"

ps:
	@docker ps -a --filter "name=$(CONTAINER)"

rebuild: build up

clean-image:
	-@docker rmi -f "$(IMAGE)" || true

clean-data:
	-@rm -rf "$(DATA_DIR)"

