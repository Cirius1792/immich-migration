"""Test the migration functionality."""

import unittest
from unittest.mock import patch

from immich_migration.config import Config
from immich_migration.migration import PhotoMigration


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


if __name__ == "__main__":
    unittest.main()
