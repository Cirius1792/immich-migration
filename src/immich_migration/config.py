"""Configuration for Immich Migration."""

from pydantic import BaseModel


class Config(BaseModel):
    """Configuration for the migration process."""

    immich_url: str
    """Immich API URL."""

    api_key: str
    """Immich API key."""

    parallel_uploads: int = 4
    """Number of parallel uploads."""

    dry_run: bool = False
    """If True, don't make any changes."""
