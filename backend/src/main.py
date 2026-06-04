"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.api.routes import (
    auth,
    bootstrap,
    clubs,
    config,
    events,
    matches,
    players,
    seasons,
    settings as settings_routes,
    stats,
    youtube,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="WaterPolo Stats API",
        version="1.0.0",
        description="Professional water polo statistics platform",
    )

    # CORS — uses regex for dev (any localhost port), explicit list for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"https?://localhost(:\d+)?",
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
    app.include_router(bootstrap.router)
    app.include_router(settings_routes.router)
    app.include_router(players.router)
    app.include_router(matches.router)
    app.include_router(events.router)
    app.include_router(stats.router)
    app.include_router(seasons.router)
    app.include_router(youtube.router)
    app.include_router(config.router)

    return app


app = create_app()
