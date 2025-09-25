############ Frontend build ############
FROM node:18 AS frontend-build

ARG EXCALIDRAW_REPO=https://github.com/excalidraw/excalidraw.git
ARG EXCALIDRAW_REF=master
ARG ENV_FILE=.env.excalidraw.local

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /src

COPY ${ENV_FILE} /src/.env.excalidraw

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
    STORAGE_TYPE=memory \
    LOCAL_STORAGE_PATH=/app/data \
    FRONTEND_DIR=/app/frontend/build

EXPOSE 8888

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8888"]
