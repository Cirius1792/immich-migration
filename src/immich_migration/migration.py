"""Photo migration to Immich."""

import concurrent.futures
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.progress import Progress

from immich_migration.client import ImmichClient
from immich_migration.config import Config
import json
import os

console = Console()

# Filename for persisting asset upload checkpoint
CHECKPOINT_FILENAME = ".immich-migration-checkpoint.json"

# Image extensions we want to upload
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".tiff",
    ".tif",
    ".heic",
    ".heif",
    ".raw",
    ".arw",
    ".cr2",
    ".nef",
    ".orf",
    ".rw2",
}

# Video extensions we want to upload
VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".wmv",
    ".flv",
    ".webm",
    ".mkv",
    ".m4v",
    ".3gp",
    ".mpg",
    ".mpeg",
}

SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS.union(VIDEO_EXTENSIONS)


class PhotoMigration:
    """Handler for migrating photos to Immich."""

    def __init__(self, config: Config):
        """Initialize the migration handler.

        Args:
            config: The configuration to use.
        """
        self.config = config
        self.client = ImmichClient(config)
        self.album_cache: Dict[str, str] = {}  # Map album name -> album ID
    
    @staticmethod
    def _get_device_asset_id(file_path: Path) -> str:
        """Compute the deviceAssetId string for a file."""
        stats = file_path.stat()
        return f"{file_path}-{stats.st_mtime}"
    
    def _load_checkpoint(self) -> None:
        """Load checkpoint from disk, validating the Immich URL."""
        if self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path, 'r') as f:
                    data = json.load(f)
                if data.get("immich_url") == self.config.immich_url and isinstance(data.get("assets"), dict):
                    self.checkpoint = data
                else:
                    console.print("[yellow]Checkpoint server URL mismatch or corrupted; starting fresh[/yellow]")
                    self.checkpoint = {"immich_url": self.config.immich_url, "assets": {}}
            except Exception as e:
                console.print(f"[bold red]Error loading checkpoint file:[/] {e}")
                self.checkpoint = {"immich_url": self.config.immich_url, "assets": {}}
        else:
            self.checkpoint = {"immich_url": self.config.immich_url, "assets": {}}
    
    def _save_checkpoint(self) -> None:
        """Persist checkpoint to disk atomically."""
        if self.config.dry_run:
            return
        try:
            tmp_path = self.checkpoint_path.parent / (self.checkpoint_path.name + ".tmp")
            with open(tmp_path, 'w') as f:
                json.dump(self.checkpoint, f)
            os.replace(tmp_path, self.checkpoint_path)
        except Exception as e:
            console.print(f"[bold red]Error saving checkpoint file:[/] {e}")

    def migrate(self, root_dir: Path) -> None:
        """Migrate photos from root directory to Immich.

        Args:
            root_dir: The root directory to migrate.
        """
        console.print(f"Starting migration from: {root_dir}")
        if self.config.dry_run:
            console.print("[yellow]DRY RUN MODE: No changes will be made[/yellow]")

        # Prepare checkpoint file path and load existing data
        self.checkpoint_path = root_dir / CHECKPOINT_FILENAME
        self._load_checkpoint()
        # Process the root directory, then persist checkpoint
        try:
            self._process_directory(root_dir, [])
        finally:
            self._save_checkpoint()

    def _process_directory(self, directory: Path, parent_path: List[str]) -> None:
        """Process a directory, creating albums and uploading photos.

        Args:
            directory: The directory to process.
            parent_path: List of parent directory names, used for album naming.
        """
        # Collect all media files and subdirectories
        media_files: List[Path] = []
        subdirs: List[Tuple[Path, str]] = []

        for item in directory.iterdir():
            if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                media_files.append(item)
            elif item.is_dir():
                subdirs.append((item, item.name))

        # If we have media files, create an album and upload them
        if media_files:
            album_path = parent_path.copy()
            album_name = " - ".join(album_path) if album_path else directory.name
            self._upload_to_album(media_files, album_name)

        # Process subdirectories, ignoring the root folder in album naming
        for subdir, name in subdirs:
            new_parent_path = parent_path.copy()
            new_parent_path.append(name)
            self._process_directory(subdir, new_parent_path)

    def _get_or_create_album(self, album_name: str) -> str:
        """Get an album ID, creating it if necessary.

        Args:
            album_name: The name of the album.

        Returns:
            The album ID.
        """
        # Check cache first
        if album_name in self.album_cache:
            return self.album_cache[album_name]

        # Try to find existing album
        existing_album = self.client.find_album_by_name(album_name)
        if existing_album:
            console.print(f"Using existing album: {album_name}")
            self.album_cache[album_name] = existing_album.id
            return existing_album.id

        # Create new album
        new_album = self.client.create_album(album_name)
        if new_album:
            self.album_cache[album_name] = new_album.id
            return new_album.id

        # Fallback for dry run
        return "dry-run-album-id"

    def _upload_to_album(self, media_files: List[Path], album_name: str) -> None:
        """Upload media files to an album, skipping already-uploaded assets.

        Args:
            media_files: List of media files to upload.
            album_name: Name of the album to upload to.
        """
        album_id = self._get_or_create_album(album_name)
        total_files = len(media_files)

        console.print(f"[bold]Album:[/] {album_name}")
        console.print(f"[bold]Found[/] {total_files} media files to upload or skip")

        # Partition files into already-uploaded and new uploads
        skipped_ids: List[str] = []
        to_upload: List[Tuple[Path, str]] = []
        for file_path in media_files:
            device_id = self._get_device_asset_id(file_path)
            server_id = self.checkpoint.get("assets", {}).get(device_id)
            if server_id:
                skipped_ids.append(server_id)
            else:
                to_upload.append((file_path, device_id))

        new_ids: List[str] = []
        # Upload new files with progress
        with Progress() as progress:
            task = progress.add_task(f"Uploading to '{album_name}'", total=len(to_upload))
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.parallel_uploads
            ) as executor:
                futures = {
                    executor.submit(self._upload_file, file_path, album_id): (file_path, device_id)
                    for file_path, device_id in to_upload
                }
                for future in concurrent.futures.as_completed(futures):
                    file_path, device_id = futures[future]
                    try:
                        server_id = future.result()
                        if server_id:
                            # record in checkpoint
                            self.checkpoint.setdefault("assets", {})[device_id] = server_id
                            new_ids.append(server_id)
                    except Exception as e:
                        console.print(f"[bold red]Error uploading {file_path}:[/] {e}")
                    finally:
                        progress.update(task, advance=1)
            progress.stop()

        all_ids = skipped_ids + new_ids
        if self.config.dry_run:
            console.print(f"[yellow]Would add assets to album:[/] {album_name} - {all_ids}")
        else:
            if all_ids:
                console.print(f"[bold]Adding {len(all_ids)} items to Album:[/] {album_name}")
                self.client.add_assets_to_album(all_ids, album_id)

    def _upload_file(self, file_path: Path, album_id: Optional[str]=None) -> Optional[str]:
        """Upload a single file to Immich and add it to an album.

        Args:
            file_path: Path to the file to upload.
            album_id: ID of the album to add the file to.

        Returns:
            The asset ID if successful, None otherwise.
        """
        try:
            return self.client.upload_asset(file_path, album_id)
        except Exception as e:
            console.print(f"[bold red]Error uploading {file_path}:[/] {e}")
            return None
