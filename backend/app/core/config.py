from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="")

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/mlops"
    api_prefix: str = "/api"
    app_name: str = "ml-experiments"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60


settings = Settings()
