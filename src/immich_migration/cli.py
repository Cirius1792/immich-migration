"""Command-line interface for Immich Migration utility."""

from pathlib import Path

import click
from rich.console import Console

from immich_migration.config import Config
from immich_migration.migration import PhotoMigration

console = Console()


@click.group()
def cli():
    """Migrate your photo library to Immich."""
    pass


@cli.command()
@click.option(
    "--root-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Root directory containing photos to migrate",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--parallel",
    type=int,
    default=4,
    help="Number of parallel uploads",
)
@click.option(
    "--immich-url",
    type=str,
    required=True,
    help="Immich API URL (e.g., http://your-immich-instance:2283/api)",
)
@click.option(
    "--api-key",
    type=str,
    required=True,
    help="Immich API key",
)
def migrate(root_dir, dry_run, parallel, immich_url, api_key):
    """Migrate photos from root directory to Immich."""

    config = Config(
        immich_url=immich_url,
        api_key=api_key,
        parallel_uploads=parallel,
        dry_run=dry_run,
    )

    migrator = PhotoMigration(config)
    migrator.migrate(root_dir)


def main():
    """Entry point for the CLI."""
    cli()
