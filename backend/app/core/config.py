from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bug Tracker API"

    database_url: str = "sqlite:///./bug_tracker.db"

    db_user: str | None = None
    db_password: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "bug_tracker"

    secret_key: str = "development-only-change-me"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    upload_dir: str = "uploads"
    max_upload_mb: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()