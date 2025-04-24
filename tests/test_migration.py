"""Test the migration functionality."""

import unittest
from unittest.mock import patch

from immich_migration.config import Config
from immich_migration.migration import PhotoMigration
from pathlib import Path
import tempfile


class TestMigration(unittest.TestCase):
    """Test the migration functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = Config(
            immich_url="http://localhost:2283/api",
            api_key="test-api-key",
            parallel_uploads=1,
            dry_run=True,
        )

    def test_album_name_generation(self):
        """Test that album names are generated correctly."""
        # Create a mock client
        with patch("immich_migration.client.ImmichClient") as MockClient:
            # Configure the mock
            mock_client = MockClient.return_value
            mock_client.create_album.return_value.id = "test-album-id"
            mock_client.find_album_by_name.return_value = None

            # Create migrator with the mock
            migrator = PhotoMigration(self.config)
            migrator.client = mock_client

            # Test root album name
            album_id = migrator._get_or_create_album("Root")
            self.assertEqual(album_id, "test-album-id")
            mock_client.create_album.assert_called_with("Root")

            # Test nested album name
            mock_client.create_album.reset_mock()
            album_id = migrator._get_or_create_album("Root - Subfolder")
            self.assertEqual(album_id, "test-album-id")
            mock_client.create_album.assert_called_with("Root - Subfolder")
    
    @patch("immich_migration.client.ImmichClient.create_album")
    def test_ignore_root_folder_in_album_naming(self, mock_create):
        """Ensure albums are named without the root directory prefix via create_album calls."""
        # Mock create_album to return a dummy with an id
        mock_create.return_value.id = "dummy-id"
        # Build a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Folder A and its subfolder
            folder_a = root / "FolderA"
            folder_a.mkdir()
            (folder_a / "img1.jpg").write_text("data")
            sub_a = folder_a / "FolderA1"
            sub_a.mkdir()
            (sub_a / "img2.jpg").write_text("data")
            # Folder B
            folder_b = root / "FolderB"
            folder_b.mkdir()
            (folder_b / "img3.jpg").write_text("data")
            # Execute migration
            migrator = PhotoMigration(self.config)
            migrator.migrate(root)
        # Collect album names used in create_album calls
        called_album_names = [call.args[-1] for call in mock_create.call_args_list]
        # Should only include the subfolders without the root prefix
        expected = {"FolderA", "FolderA - FolderA1", "FolderB"}
        self.assertEqual(set(called_album_names), expected)


if __name__ == "__main__":
    unittest.main()
