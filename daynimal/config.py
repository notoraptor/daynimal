import os
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


def get_app_data_dir() -> Path:
    """Répertoire de données persistantes (DB, config, cache).

    Sur mobile (Flet), utilise FLET_APP_STORAGE_DATA.
    Sur desktop, utilise le répertoire courant.
    """
    flet_data = os.getenv("FLET_APP_STORAGE_DATA")
    if flet_data:
        return Path(flet_data)
    return Path(".")


def get_app_temp_dir() -> Path:
    """Répertoire temporaire (téléchargements, décompression).

    Sur mobile (Flet), utilise FLET_APP_STORAGE_TEMP.
    Sur desktop, utilise tmp/ relatif.
    """
    flet_temp = os.getenv("FLET_APP_STORAGE_TEMP")
    if flet_temp:
        return Path(flet_temp)
    return Path("tmp")


def is_mobile() -> bool:
    """True si l'app tourne dans un environnement mobile Flet."""
    return os.getenv("FLET_APP_STORAGE_DATA") is not None


class Settings(BaseSettings):
    # Database
    database_url: str = f"sqlite:///{get_app_data_dir() / 'daynimal.db'}"

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
    image_cache_dir: Path = get_app_data_dir() / "cache" / "images"
    image_cache_max_size_mb: int = 500
    image_cache_hd: bool = True

    model_config = ConfigDict(env_prefix="DAYNIMAL_", env_file=".env")


settings = Settings()
