"""Immich API client."""
import os
import mimetypes
from pathlib import Path
from typing import List, Optional
from datetime import datetime

import requests
from pydantic import BaseModel, TypeAdapter
from rich.console import Console

from immich_migration.config import Config

console = Console()


class Album(BaseModel):
    """Immich album model."""

    id: str
    albumName: str


class ImmichClient:
    """Client for interacting with the Immich API."""

    def __init__(self, config: Config):
        """Initialize the client with the given configuration.

        Args:
            config: The configuration to use.
        """
        self.config = config
        self.base_url = config.immich_url.rstrip("/")
        self.headers = {"x-api-key": config.api_key, "Accept": "application/json"}

        # Skip connection verification in dry-run mode
        if not config.dry_run:
            self._verify_connection()

    def _verify_connection(self) -> None:
        """Verify connection to the Immich API."""
        try:
            response = requests.get(
                f"{self.base_url}/server/about", headers=self.headers, timeout=10
            )
            response.raise_for_status()
            console.print("[green]Connected to Immich API successfully[/green]")
        except requests.RequestException as e:
            console.print(f"[bold red]Error connecting to Immich API:[/] {e}")
            raise

    def create_album(self, album_name: str) -> Optional[Album]:
        """Create a new album in Immich.

        Args:
            album_name: The name of the album to create.

        Returns:
            The created album object, or None if in dry-run mode.
        """
        if self.config.dry_run:
            console.print(f"[yellow]Would create album:[/] {album_name}")
            # Return a mock album in dry-run mode
            return Album(id='dry-run-id', albumName=album_name)

        console.print(f"Creating album: {album_name}")
        response = requests.post(
            f"{self.base_url}/albums",
            headers=self.headers,
            json={"albumName": album_name},
            timeout=30,
        )
        response.raise_for_status()
        return Album.model_validate(response.json())

    def get_albums(self) -> List[Album]:
        """Get all albums from Immich.

        Returns:
            List of all albums.
        """
        if self.config.dry_run:
            console.print("[yellow]Would get all albums[/yellow]")
            return []
            
        response = requests.get(
            f"{self.base_url}/albums", headers=self.headers, timeout=30
        )
        response.raise_for_status()
        ta = TypeAdapter(List[Album])
        try:
            return ta.validate_python(response.json())
        except Exception as e:
            console.print(f"[bold red]Error validating albums:[/] {e}")
            raise
        # return [Album.model_validate(album) for album in response.json()]

    def find_album_by_name(self, album_name: str) -> Optional[Album]:
        """Find an album by name.

        Args:
            album_name: The name of the album to find.

        Returns:
            The album if found, None otherwise.
        """
        if self.config.dry_run:
            console.print(f"[yellow]Would search for album:[/yellow] {album_name}")
            return None
            
        albums = self.get_albums()
        for album in albums:
            if album.albumName == album_name:
                return album
        return None

    def upload_asset(
        self, file_path: Path, album_id: Optional[str] = None, verbose=False
    ) -> Optional[str]:
        """Upload an asset to Immich.

        Args:
            file_path: Path to the file to upload.
            album_id: Optional album ID to add the asset to.

        Returns:
            The asset ID if successful, None otherwise.
        """
        if self.config.dry_run:
            console.print(f"[yellow]Would upload asset:[/] {file_path}")
            return "dry-run-asset-id"

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        if verbose:
            console.print(f"Uploading: {file_path}")
        stats = os.stat(file_path)
        
        data = {
            'deviceAssetId': f'{file_path}-{stats.st_mtime}',
            'deviceId': 'python',
            'fileCreatedAt': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'fileModifiedAt': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'isFavorite': 'false',
            'albumId': album_id
        }

        with open(file_path, 'rb') as asset_data:
            files = {
                'assetData': asset_data
            }

            try:
                response = requests.post(
                    f'{self.base_url}/assets', headers=self.headers, data=data, files=files
                )

                response.raise_for_status()
                asset_id = response.json().get("id")

                # If album_id is provided, add the asset to the album
                if asset_id and album_id:
                    self.add_asset_to_album(asset_id, album_id)

                return asset_id
            except requests.RequestException as e:
                console.print(f"[bold red]Error uploading {file_path}:[/] {e}")
                return None

    def add_assets_to_album(self, asset_ids: List[str], album_id: str) -> bool:
        """Add a set of assets to an album.

        Args:
            asset_id: The ID of the asset to add.
            album_id: The ID of the album to add the asset to.

        Returns:
            True if successful, False otherwise.
        """
        assert len(asset_ids) > 0, "No asset IDs provided"
        assert album_id is not None, "No album ID provided"

        if self.config.dry_run:
            console.print(
                f"[yellow]Would add assets to album:[/] {asset_ids} -> {album_id}"
            )
            return True

        response = requests.put(
            f"{self.base_url}/albums/{album_id}/assets",
            headers=self.headers,
            json={"ids": asset_ids},
            timeout=30,
        )
        response.raise_for_status()
        return True

    def add_asset_to_album(self, asset_id: str, album_id: str) -> bool:
        """Add an asset to an album.

        Args:
            asset_id: The ID of the asset to add.
            album_id: The ID of the album to add the asset to.

        Returns:
            True if successful, False otherwise.
        """
        return self.add_assets_to_album([asset_id], album_id)
