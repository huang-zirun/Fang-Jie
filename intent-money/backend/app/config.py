from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./intent_money.db"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    AI_API_KEY: str | None = None
    AI_BASE_URL: str = "https://openrouter.ai/api/v1"
    AI_MODEL: str = "deepseek/deepseek-chat-v3-0324:free"
    ENV: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
