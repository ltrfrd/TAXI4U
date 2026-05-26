from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    GOOGLE_MAPS_API_KEY: str = ""
    FIREBASE_CREDENTIALS_PATH: str = ""
    CORS_ORIGINS: str = "*"

    model_config = {"env_file": ".env"}


settings = Settings()
