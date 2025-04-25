# Immich Migration

A utility script to migrate a photo library into Immich.

## Features

- Recursively scans folders containing photos
- Creates albums in Immich based on folder structure
- Uploads photos to corresponding albums
- Preserves folder hierarchy in album names
- Persists upload state to `.immich-migration-checkpoint.json`, allowing resuming migrations and skipping already-uploaded assets on subsequent runs

## Installation

```bash
# Install with uv
uv pip install .
```

## Usage

```bash
# Run the migration with required parameters
immich-migration migrate \
  --root-dir /path/to/photos \
  --immich-url http://your-immich-instance:2283/api \
  --api-key your_api_key
  ```

By default, the migration process writes a checkpoint file named `.immich-migration-checkpoint.json` to the root directory. On subsequent runs, this file is used to skip assets that were already uploaded (based on file path and modification time), enabling resumable migrations. To force a fresh migration, delete or rename the checkpoint file.

## Options

```
--root-dir          Root directory containing photos [required]
--immich-url        Immich API URL [required]
--api-key           Immich API key [required]
--dry-run           Show what would be done without making changes
--parallel          Number of parallel uploads (default: 4)
--help              Show help message
```