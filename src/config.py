from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 30
    database_url: str
    redis_url: str

    class Config:
        env_file = ".env"

settings = Settings()