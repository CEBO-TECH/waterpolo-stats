"""FastAPI application factory."""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings


def _run_alembic_upgrade() -> None:
    """Run `alembic upgrade head` (blocking — called in a worker thread)."""
    from alembic import command
    from alembic.config import Config

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-apply migrations on startup so deploys/dev never need a manual step.
    # Postgres-only (tests use SQLite + create_all). env.py uses asyncio.run,
    # so we run it in a thread to avoid nesting event loops.
    if settings.AUTO_MIGRATE and settings.DATABASE_URL.startswith("postgresql"):
        try:
            await asyncio.to_thread(_run_alembic_upgrade)
            print("[startup] alembic upgrade head — OK")
        except Exception as e:  # don't block startup if migrations fail
            print(f"[startup] auto-migration skipped/failed: {e}")
    yield
from src.api.routes import (
    age_categories,
    auth,
    bootstrap,
    clubs,
    config,
    dashboard,
    events,
    matches,
    me as me_routes,
    players,
    seasons,
    settings as settings_routes,
    stats,
    substitutions,
    voice,
    voice_notes,
    youtube,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cap Track API",
        version="1.0.0",
        description="Cap Track — water polo statistics platform",
        lifespan=lifespan,
    )

    # CORS — explicit list for production web + regex covering dev (any localhost
    # port) and Capacitor/Ionic native WebView origins (iOS uses capacitor://localhost,
    # Android uses http(s)://localhost).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"(https?|capacitor|ionic)://localhost(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/v1/health")
    async def health():
        return {"status": "ok"}

    # Register routes
    app.include_router(auth.router)
    app.include_router(clubs.router)
    app.include_router(clubs.invitations_router)
    app.include_router(bootstrap.router)
    app.include_router(settings_routes.router)
    app.include_router(players.router)
    app.include_router(matches.router)
    app.include_router(events.router)
    app.include_router(stats.router)
    app.include_router(seasons.router)
    app.include_router(youtube.router)
    app.include_router(config.router)
    app.include_router(age_categories.router)
    app.include_router(dashboard.router)
    app.include_router(substitutions.router)
    app.include_router(me_routes.router)
    app.include_router(voice_notes.router)
    app.include_router(voice.router)

    return app


app = create_app()
