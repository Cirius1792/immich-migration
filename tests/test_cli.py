"""Test the CLI functionality."""

import unittest
from unittest.mock import patch

from click.testing import CliRunner

from immich_migration.cli import cli


class TestCli(unittest.TestCase):
    """Test the CLI functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test the CLI help command."""
        result = self.runner.invoke(cli, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Migrate your photo library to Immich", result.output)
        self.assertIn("migrate", result.output)

    def test_migrate_command_help(self):
        """Test the migrate command help."""
        result = self.runner.invoke(cli, ["migrate", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Migrate photos from root directory to Immich", result.output)
        self.assertIn("--root-dir", result.output)
        self.assertIn("--dry-run", result.output)
        self.assertIn("--parallel", result.output)

    @patch("immich_migration.cli.PhotoMigration")
    def test_migrate_command(self, mock_migration):
        """Test the migrate command with mocked dependencies."""
        with self.runner.isolated_filesystem():
            with open("test.jpg", "w") as f:
                f.write("test")
                
            result = self.runner.invoke(
                cli, [
                    "migrate", 
                    "--root-dir", ".", 
                    "--dry-run",
                    "--immich-url", "http://example.com",
                    "--api-key", "test-key"
                ]
            )
            
            self.assertEqual(result.exit_code, 0)
            mock_migration.return_value.migrate.assert_called_once()


if __name__ == "__main__":
    unittest.main()