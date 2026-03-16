# Makefile for sa2pydantic project

# Default command
.PHONY: help
:help:
	@echo "Available commands:"
	@echo "  make test      - run pytest"
	@echo "  make typecheck - run mypy on src"
	@echo "  make all       - run typecheck and tests"

# Run pytest
.PHONY: test
test:
	uv run -m pytest ./tests

# Run mypy type checker
.PHONY: typecheck
typecheck:
	uv run -m mypy ./src


.PHONY: precommit
precommit:
	pre-commit run


.PHONY: lint
lint:
    uv run -m ruff check .

# Run both
.PHONY: all
all: typecheck test