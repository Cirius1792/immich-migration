"""Test checkpoint persistence and upload skipping functionality in migration."""
import unittest
import tempfile
import os
import json
from pathlib import Path

from immich_migration.migration import PhotoMigration, CHECKPOINT_FILENAME
from immich_migration.config import Config
from unittest.mock import Mock, patch


class TestCheckpointLoadSave(unittest.TestCase):
    """Test loading and saving of the checkpoint file."""

    def setUp(self):
        # Patch out the real ImmichClient to avoid HTTP calls
        self.client_patcher = patch(
            'immich_migration.migration.ImmichClient', return_value=Mock()
        )
        self.client_patcher.start()
        self.addCleanup(self.client_patcher.stop)
        # Create a temporary directory to act as root_dir
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        # Prepare a config with dry_run disabled for saving
        self.config = Config(
            immich_url="http://example.com/api",
            api_key="key",
            parallel_uploads=1,
            dry_run=False,
        )
        # Instantiate migration without triggering real HTTP
        self.pm = PhotoMigration(self.config)
        # Assign the checkpoint path under root
        self.pm.checkpoint_path = self.root / CHECKPOINT_FILENAME

    def tearDown(self):
        self.tempdir.cleanup()

    def test_save_and_load_checkpoint(self):
        # Initialize checkpoint and save
        data = {"immich_url": self.config.immich_url, "assets": {"a": "1"}}
        self.pm.checkpoint = data.copy()
        self.pm._save_checkpoint()
        # File should exist and content match
        with open(self.pm.checkpoint_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, data)
        # Modify in-memory and reload from disk
        self.pm.checkpoint = {}
        self.pm._load_checkpoint()
        self.assertEqual(self.pm.checkpoint, data)

    def test_load_missing_file(self):
        # Remove any existing checkpoint
        if self.pm.checkpoint_path.exists():
            self.pm.checkpoint_path.unlink()
        # Load should create fresh checkpoint
        self.pm._load_checkpoint()
        expected = {"immich_url": self.config.immich_url, "assets": {}}
        self.assertEqual(self.pm.checkpoint, expected)

    def test_load_url_mismatch(self):
        # Write a checkpoint with wrong URL
        wrong = {"immich_url": "http://wrong/api", "assets": {"x": "y"}}
        with open(self.pm.checkpoint_path, 'w') as f:
            json.dump(wrong, f)
        # Load should detect mismatch and reset assets
        self.pm._load_checkpoint()
        expected = {"immich_url": self.config.immich_url, "assets": {}}
        self.assertEqual(self.pm.checkpoint, expected)

    def test_load_invalid_json(self):
        # Write invalid JSON
        with open(self.pm.checkpoint_path, 'w') as f:
            f.write("not a json")
        # Load should catch exception and reset
        self.pm._load_checkpoint()
        expected = {"immich_url": self.config.immich_url, "assets": {}}
        self.assertEqual(self.pm.checkpoint, expected)


class TestGetDeviceAssetId(unittest.TestCase):
    """Test computation of device asset ID."""

    def test_get_device_asset_id(self):
        # Create a temporary file and set a known mtime
        with tempfile.TemporaryDirectory() as tmpdir:
            fp = Path(tmpdir) / "file.txt"
            fp.write_text("data")
            mtime = 12345.0
            os.utime(fp, (mtime, mtime))
            # Call static method
            result = PhotoMigration._get_device_asset_id(fp)
            # Expect path and mtime concatenation
            self.assertEqual(result, f"{fp}-{mtime}")


class DummyProgress:
    """Stub for rich.progress.Progress to suppress output in tests."""
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def add_task(self, *args, **kwargs):
        return None

    def update(self, *args, **kwargs):
        pass

    def stop(self):
        pass


class TestUploadToAlbum(unittest.TestCase):
    """Test skipping already-uploaded assets and uploading new ones."""

    def setUp(self):
        # Patch out the real ImmichClient to avoid HTTP calls
        self.client_patcher = patch(
            'immich_migration.migration.ImmichClient', return_value=Mock()
        )
        self.client_patcher.start()
        self.addCleanup(self.client_patcher.stop)
        # Config with dry_run disabled
        self.config = Config(
            immich_url="http://example.com/api",
            api_key="key",
            parallel_uploads=1,
            dry_run=False,
        )
        # Instantiate migration without triggering real HTTP
        self.pm = PhotoMigration(self.config)
        # Stub out album creation to return a fixed ID
        self.pm._get_or_create_album = lambda name: "ALBUMID"
        # Stub out client methods
        self.pm.client = Mock()
        # upload_asset returns a synthetic server ID
        self.pm.client.upload_asset = lambda path, album: f"{path.name}-uploaded"
        self.pm.client.add_assets_to_album = Mock()
        # Suppress progress output
        self.progress_patcher = patch(
            'immich_migration.migration.Progress', new=DummyProgress
        )
        self.progress_patcher.start()

    def tearDown(self):
        self.progress_patcher.stop()

    def test_upload_skips_and_uploads(self):
        # Monkey-patch device ID to control skip logic
        self.pm._get_device_asset_id = lambda p: f"DEV-{p.name}"
        # Prepare checkpoint with one pre-uploaded asset
        self.pm.checkpoint = {"immich_url": self.config.immich_url, "assets": {"DEV-file1.jpg": "SID1"}}
        files = [Path("file1.jpg"), Path("file2.jpg")]
        # Run upload
        self.pm._upload_to_album(files, "AlbumName")
        # Check that new file was added to checkpoint
        self.assertIn("DEV-file2.jpg", self.pm.checkpoint["assets"])
        self.assertEqual(self.pm.checkpoint["assets"]["DEV-file2.jpg"], "file2.jpg-uploaded")
        # add_assets_to_album should be called with skipped + new IDs
        expected_ids = ["SID1", "file2.jpg-uploaded"]
        self.pm.client.add_assets_to_album.assert_called_once_with(expected_ids, "ALBUMID")

    def test_upload_dry_run_skips_call(self):
        # Reconfigure for dry_run
        self.pm.config.dry_run = True
        self.pm._get_device_asset_id = lambda p: f"DEV-{p.name}"
        self.pm.checkpoint = {"immich_url": self.config.immich_url, "assets": {}}
        files = [Path("fileA.jpg")]
        # Run upload
        self.pm._upload_to_album(files, "AlbumName")
        # In dry run, add_assets_to_album should not be called
        self.pm.client.add_assets_to_album.assert_not_called()