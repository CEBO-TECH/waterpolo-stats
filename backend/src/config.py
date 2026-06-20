from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://waterpolo:waterpolo_password_123@localhost:5432/waterpolo_stats"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    YOUTUBE_API_KEY: str = ""
    INITIAL_ADMIN_EMAIL: str = ""
    INITIAL_ADMIN_PASSWORD: str = ""

    # Run `alembic upgrade head` automatically on app startup (Postgres only).
    AUTO_MIGRATE: bool = True

    # Voice-note object storage. "local" (dev/test) or "s3" (MinIO / S3 in prod).
    STORAGE_BACKEND: str = "local"
    VOICE_STORAGE_DIR: str = "/tmp/wts_voice_notes"
    S3_ENDPOINT: str = ""  # e.g. http://minio:9000
    S3_BUCKET: str = "voice-notes"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = "us-east-1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
