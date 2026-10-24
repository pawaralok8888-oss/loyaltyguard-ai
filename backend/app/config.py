import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Deployment note: requires Python 3.11 (pin in render.yaml / railway.toml)


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./loyaltyguard.db"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    N8N_SHARED_SECRET: str = ""
    LLM_PROVIDER: str = "fallback"
    LLM_API_KEY: str = ""
    FROZEN_DATETIME: str = ""

    # Portal base URL — override in production to point to real (or staging) portal.
    # In tests / local dev the TestClient injects its own transport so this is unused.
    PORTAL_BASE_URL: str = "http://127.0.0.1:8000"

    # Set to "true" in local/dev only.  In production leave unset or set to "false"
    # so /mock/admin/scenario is rejected even if the route is reachable.
    MOCK_ADMIN_ENABLED: str = "false"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def mock_admin_enabled(self) -> bool:
        return self.MOCK_ADMIN_ENABLED.lower() in ("true", "1", "yes")


settings = Settings()
