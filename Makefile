.PHONY: dev test lint format

dev:
	mkdir -p playground
	cd playground && claude --plugin-dir ..

test:
	uv run pytest tests/

format:
	uv run ruff format src/ tests/

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/
	uv run mypy src/shinkoku/ --ignore-missing-imports
