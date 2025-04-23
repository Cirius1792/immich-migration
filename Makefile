.PHONY: install test lint format clean

# Install the package in development mode
install:
	uv pip install -e .

# Run tests
test:
	uv run pytest

# Run linting checks
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .

# Clean up build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete

# Run sample migration in dry run mode
sample-dry-run:
	uv run python -m immich_migration.main sample --dry-run \
	--immich-url http://localhost:2283/api \
	--api-key test-key