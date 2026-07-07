from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://aimark:aimark@localhost:5432/aimark"
    cors_origins: str = "http://localhost:5173"

    # LLM (OpenAI) — used by the "fetch competitors" feature
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
