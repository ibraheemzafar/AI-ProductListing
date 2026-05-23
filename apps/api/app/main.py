from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.error_middleware import ErrorHandlingMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AI Product Listing API", version="0.1.0")
    app.add_middleware(ErrorHandlingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.api_cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)
    app.mount(
        "/uploads",
        StaticFiles(directory=settings.local_storage_path),
        name="uploads",
    )
    return app


app = create_app()
