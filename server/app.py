from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes.documents import router as documents_router
from .routes.firebase import router as firebase_router
from .routes.ui import mount_static
from .routes.admin import router as admin_router


def create_app() -> FastAPI:
    app = FastAPI(title="Excalidraw All-in-one (FastAPI)")

    # CORS: allow all by default; tighten in settings if needed
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=300,
    )

    # API routes
    app.include_router(documents_router)
    app.include_router(firebase_router)
    app.include_router(admin_router)

    # Static frontend
    mount_static(app, settings.FRONTEND_DIR)

    @app.get("/ping")
    def ping():
        return {"msg": "pong"}

    return app


app = create_app()
