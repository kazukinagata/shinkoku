.PHONY: dev test lint

dev:
	mkdir -p playground
	cd playground && claude --plugin-dir ..

test:
	uv run pytest tests/

lint:
	uv run ruff check src/ tests/
