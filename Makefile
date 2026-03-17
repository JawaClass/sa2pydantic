.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make test      - run pytest"
	@echo "  make typecheck - run mypy on src"
	@echo "  make all       - run typecheck and tests"

.PHONY: test
test:
	uv run -m pytest ./tests

.PHONY: typecheck
typecheck:
	uv run -m mypy ./src

.PHONY: precommit
precommit:
	pre-commit run

.PHONY: lint
lint:
	uv run -m ruff format . && uv run -m ruff check . --fix

.PHONY: all
all: 
	typecheck test lint