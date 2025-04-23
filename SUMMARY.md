# Immich Migration Utility

## Overview

This utility helps you migrate your photo library to Immich, preserving folder structures as albums. The tool recursively scans directories containing photos and videos, creating albums in Immich that match your folder hierarchy.

## Key Features

- **Album Structure Preservation**: Creates Immich albums based on your folder structure
- **Recursive Directory Scanning**: Processes nested folders automatically
- **Hierarchical Album Naming**: Uses parent folder names for nested albums
- **Parallel Uploads**: Configurable parallel processing for faster migration
- **Dry Run Mode**: Preview changes without modifying Immich
- **Media File Detection**: Identifies common image and video formats

## Technical Implementation

### Architecture

The project follows a modular architecture:

1. **CLI Layer** (`cli.py`): Handles command-line interface using Click
2. **Config Layer** (`config.py`): Manages configuration settings
3. **Client Layer** (`client.py`): Communicates with the Immich API
4. **Migration Layer** (`migration.py`): Core migration logic

### Code Quality

- **Type Hints**: Throughout the codebase for better IDE support and safety
- **Comprehensive Testing**: Unit tests for core functionality
- **Documentation**: Docstrings and comments explain the code
- **Error Handling**: Graceful handling of API errors

### Dependencies

- **click**: Command-line interface
- **requests**: API communication
- **pydantic**: Data validation
- **rich**: Terminal UI enhancements
- **pytest**: Testing

## Usage Example

```bash
# Run the migration in dry-run mode first
immich-migration migrate \
    --root-dir /path/to/photos \
    --immich-url http://your-immich-server:2283/api \
    --api-key your_api_key \
    --dry-run

# When satisfied with the dry run, perform the actual migration
immich-migration migrate \
    --root-dir /path/to/photos \
    --immich-url http://your-immich-server:2283/api \
    --api-key your_api_key \
    --parallel 8
```

This creates albums in Immich matching your folder structure, and uploads all photos to their respective albums.

## Future Improvements

Potential enhancements for future versions:

1. **Checksum Verification**: Ensure photos are not duplicated
2. **Incremental Migration**: Only upload new or changed files
3. **Metadata Preservation**: Ensure all metadata is correctly maintained
4. **Progress Persistence**: Resume interrupted migrations
5. **Advanced Filtering**: Select photos by date range, file type, etc.