"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
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
    voice_notes,
    youtube,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="WaterPolo Stats API",
        version="1.0.0",
        description="Professional water polo statistics platform",
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

    return app


app = create_app()
