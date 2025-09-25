############ Frontend build ############
FROM node:18 AS frontend-build

ARG EXCALIDRAW_REPO=https://github.com/excalidraw/excalidraw.git
ARG EXCALIDRAW_REF=master
ARG PUBLIC_ORIGIN
ARG WS_ORIGIN

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /src

# Always generate frontend env from build args to avoid hardcoding in repo
RUN set -eux; \
    PO="${PUBLIC_ORIGIN:-http://localhost:8888}"; PO="${PO%/}"; \
    WO="${WS_ORIGIN:-$PO}"; WO="${WO%/}"; \
    echo 'MODE="production"' > /src/.env.excalidraw; \
    echo "VITE_APP_BACKEND_V2_GET_URL=${PO}/api/v2/" >> /src/.env.excalidraw; \
    echo "VITE_APP_BACKEND_V2_POST_URL=${PO}/api/v2/post/" >> /src/.env.excalidraw; \
    echo "VITE_APP_LIBRARY_URL=https://libraries.excalidraw.com" >> /src/.env.excalidraw; \
    echo "VITE_APP_LIBRARY_BACKEND=https://us-central1-excalidraw-room-persistence.cloudfunctions.net/libraries" >> /src/.env.excalidraw; \
    echo "VITE_APP_PLUS_LP=${PO}" >> /src/.env.excalidraw; \
    echo "VITE_APP_PLUS_APP=${PO}" >> /src/.env.excalidraw; \
    echo "VITE_APP_AI_BACKEND=${PO}/ai/" >> /src/.env.excalidraw; \
    echo "VITE_APP_WS_SERVER_URL=${WO}" >> /src/.env.excalidraw; \
    echo "VITE_APP_ENABLE_TRACKING=false" >> /src/.env.excalidraw; \
    echo "VITE_APP_PLUS_EXPORT_PUBLIC_KEY='MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApQ0jM9Qz8TdFLzcuAZZX" >> /src/.env.excalidraw; \
    echo "/WvuKSOJxiw6AR/ZcE3eFQWM/mbFdhQgyK8eHGkKQifKzH1xUZjCxyXcxW6ZO02t" >> /src/.env.excalidraw; \
    echo "kPOPxhz+nxUrIoWCD/V4NGmUA1lxwHuO21HN1gzKrN3xHg5EGjyouR9vibT9VDGF" >> /src/.env.excalidraw; \
    echo "gq6+4Ic/kJX+AD2MM7Yre2+FsOdysrmuW2Fu3ahuC1uQE7pOe1j0k7auNP0y1q53" >> /src/.env.excalidraw; \
    echo "PrB8Ts2LUpepWC1l7zIXFm4ViDULuyWXTEpUcHSsEH8vpd1tckjypxCwkipfZsXx" >> /src/.env.excalidraw; \
    echo "iPszy0o0Dx2iArPfWMXlFAI9mvyFCyFC3+nSvfyAUb2C4uZgCwAuyFh/ydPF4DEE" >> /src/.env.excalidraw; \
    echo "PQIDAQAB'" >> /src/.env.excalidraw; \
    echo "VITE_APP_DEBUG_ENABLE_TEXT_CONTAINER_BOUNDING_BOX=false" >> /src/.env.excalidraw; \
    echo "VITE_APP_COLLAPSE_OVERLAY=false" >> /src/.env.excalidraw; \
    echo "VITE_APP_ENABLE_ESLINT=false" >> /src/.env.excalidraw;

RUN git clone --depth 1 ${EXCALIDRAW_REPO} excalidraw \
 && cd excalidraw \
 && if [ "${EXCALIDRAW_REF}" != "master" ]; then git fetch --depth 1 origin ${EXCALIDRAW_REF} && git checkout ${EXCALIDRAW_REF}; fi

# Ensure root-level env overrides as upstream reads .env.production at repo root
RUN cp /src/.env.excalidraw /src/excalidraw/.env.production || true \
 && cp /src/.env.excalidraw /src/excalidraw/.env.production.local || true

# Use project-provided overrides to avoid hardcoding in Dockerfile
RUN mkdir -p /src/excalidraw/packages/excalidraw-app/ && \
    cp /src/.env.excalidraw /src/excalidraw/packages/excalidraw-app/.env.production.local

WORKDIR /src/excalidraw
# Use yarn per packageManager in upstream repo, fallback to non-immutable
RUN corepack enable || true
# Set domestic registries to speed up installs (can be overridden via build args)
RUN npm config set registry https://registry.npmmirror.com
RUN yarn config set npmRegistryServer https://registry.npmmirror.com
RUN yarn --version || true
RUN yarn install --immutable || yarn install
# Determine app directory and apply env overrides
RUN set -eux; \
    APP_DIR=""; \
    if [ -d packages/excalidraw-app ]; then APP_DIR=packages/excalidraw-app; \
    elif [ -d excalidraw-app ]; then APP_DIR=excalidraw-app; \
    elif [ -d apps/excalidraw ]; then APP_DIR=apps/excalidraw; \
    else echo "Cannot find Excalidraw app directory" && ls -la && exit 1; fi; \
    # Overwrite env with our configuration to ensure it takes effect in all build scripts
    cp /src/.env.excalidraw "/src/excalidraw/${APP_DIR}/.env.production" || true; \
    cp /src/.env.excalidraw "/src/excalidraw/${APP_DIR}/.env.production.local" || true; \
    cd "$APP_DIR"; \
    yarn run build:app:docker || yarn run build
# Consolidate build artifacts into a canonical path
RUN set -eux; \
    mkdir -p /src/frontend-build; \
    if [ -d packages/excalidraw-app/build ]; then \
      cp -r packages/excalidraw-app/build/* /src/frontend-build/; \
    elif [ -d apps/excalidraw/build ]; then \
      cp -r apps/excalidraw/build/* /src/frontend-build/; \
    elif [ -d excalidraw-app/build ]; then \
      cp -r excalidraw-app/build/* /src/frontend-build/; \
    else \
      echo "Frontend build not found" && exit 1; \
    fi


############ Backend runtime ############
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies (use default PyPI)
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# Copy backend
COPY server /app/server

# Copy built frontend from previous stage (canonical path)
COPY --from=frontend-build /src/frontend-build /app/frontend/build

ENV HOST=0.0.0.0 \
    PORT=8888 \
    STORAGE_TYPE=filesystem \
    LOCAL_STORAGE_PATH=/app/data \
    FRONTEND_DIR=/app/frontend/build \
    PUBLIC_ORIGIN=http://127.0.0.1:8888

EXPOSE 8888

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8888"]
