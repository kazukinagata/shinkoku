.PHONY: dev test lint

dev:
	claude --plugin-dir .

test:
	uv run pytest tests/

lint:
	uv run ruff check src/ tests/
