from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os


def mount_static(app: FastAPI, static_dir: str):
    static_dir = static_dir or "./frontend/build"
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

        # Fallback for client-side routing to index.html
        @app.middleware("http")
        async def spa_fallback(request: Request, call_next):
            # pass through API routes
            if request.url.path.startswith("/api/") or request.url.path.startswith("/v1/") or request.url.path.startswith("/ping") or request.url.path.startswith("/admin"):
                return await call_next(request)
            # try static first
            path = os.path.join(static_dir, request.url.path.lstrip("/"))
            if os.path.exists(path) and os.path.isfile(path):
                return await call_next(request)
            index_path = os.path.join(static_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return await call_next(request)
