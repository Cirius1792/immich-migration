"""Main module that can be used to run the migration directly."""

from pathlib import Path
import sys
import argparse

from immich_migration.config import Config
from immich_migration.migration import PhotoMigration


def main():
    """Run the migration from the command line."""
    parser = argparse.ArgumentParser(description="Migrate photos to Immich")
    parser.add_argument("root_dir", help="Root directory containing photos")
    parser.add_argument("--immich-url", required=True, help="Immich API URL")
    parser.add_argument("--api-key", required=True, help="Immich API key")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Dry run mode")
    parser.add_argument("--parallel", type=int, default=4, help="Number of parallel uploads")
    
    args = parser.parse_args()
    
    root_dir = Path(args.root_dir)
    if not root_dir.exists():
        print(f"Error: Directory {root_dir} does not exist")
        sys.exit(1)
        
    # Use command line arguments
    api_key = args.api_key
    immich_url = args.immich_url
    dry_run = args.dry_run

    config = Config(
        immich_url=immich_url,
        api_key=api_key,
        parallel_uploads=args.parallel,
        dry_run=dry_run,
    )

    migrator = PhotoMigration(config)
    migrator.migrate(root_dir)


if __name__ == "__main__":
    main()
