import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./intent_money.db"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    AI_API_KEY: str | None = None
    AI_BASE_URL: str = "https://openrouter.ai/api/v1"
    AI_MODEL: str = "deepseek/deepseek-chat-v3-0324:free"
    XHS_COOKIE: str = ""
    ENV: str = "development"
    SMS_GATEWAY: str = ""
    SMS_ACCESS_KEY: str = ""
    SMS_SECRET_KEY: str = ""
    SMS_SIGN_NAME: str = ""
    SMS_TEMPLATE_CODE: str = ""
    SMS_ENABLED: bool = False
    DOUYIN_COOKIE: str = ""
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_ENABLED: bool = True
    SENTIMENT_ENABLED: bool = True
    AUTO_PUBLISH_ENABLED: bool = False
    SOCIAL_AUTO_UPLOAD_PATH: str = ""
    COOKIE_DIR: str = "cookies"
    COOKIE_EXPIRE_DAYS: int = 7
    # 优先从环境变量读取，如果没有则使用默认值
    COOKIE_ENCRYPTION_KEY: str = os.environ.get("COOKIE_ENCRYPTION_KEY", "")
    PER_USER_SCRAPING: bool = True

    # Development mode settings
    DEV_MODE: bool = False  # 开发模式开关，开启后无限换条

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
