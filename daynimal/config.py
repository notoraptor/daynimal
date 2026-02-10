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

    # Distribution release URL for first-launch setup
    distribution_base_url: str = (
        "https://github.com/notoraptor/daynimal/releases/download/v1.0.0"
    )

    # Image cache
    image_cache_dir: Path = Path("~/.daynimal/cache/images").expanduser()
    image_cache_max_size_mb: int = 500
    image_cache_hd: bool = True

    class Config:
        env_prefix = "DAYNIMAL_"
        env_file = ".env"


settings = Settings()
