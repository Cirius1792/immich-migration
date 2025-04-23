# Contributing to Immich Migration

Thank you for your interest in contributing to Immich Migration! This document provides guidelines and instructions for contributing.

## Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/immich-migration.git
cd immich-migration
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. Install development dependencies:
```bash
uv pip install pytest ruff
```

## Development Workflow

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Run tests:
```bash
uv run pytest
```

4. Format and lint your code:
```bash
uv run ruff format .
uv run ruff check .
```

5. Submit a pull request

## Testing

- Write tests for new features or bug fixes
- Run tests with `uv run pytest`
- You can run specific tests with `uv run pytest tests/test_specific.py`

## Code Style

This project follows PEP 8 guidelines with some modifications:
- Line length: 88 characters (Black default)
- Prefer double quotes for strings
- Use type hints for all function definitions

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the CHANGELOG.md to document your changes
3. The PR should work in CI and pass all tests
4. A maintainer will review and merge your PR