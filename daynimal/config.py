from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///daynimal.db"

    # Data directory for dumps
    data_dir: Path = Path("data")

    # API settings
    httpx_timeout: float = 30.0

    # Wikipedia language preference (order of preference)
    wikipedia_languages: list[str] = ["fr", "en"]

    # Rate limiting (requests per second)
    api_rate_limit: float = 1.0

    class Config:
        env_prefix = "DAYNIMAL_"
        env_file = ".env"


settings = Settings()
