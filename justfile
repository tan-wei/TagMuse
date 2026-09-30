set positional-arguments := true

default:
    @just --list

sync:
    uv sync --all-groups

help:
    uv run tag-muse --help

export-tags library output:
    #!/bin/sh
    uv run tag-muse export-tags "$1" "$2"

export-force library output:
    #!/bin/sh
    uv run tag-muse export-tags "$1" "$2" --force

scan source:
    #!/bin/sh
    uv run tag-muse scan --source "$1"

test *args:
    #!/bin/sh
    uv run pytest "$@"

lint:
    uv run ruff check .

format:
    uv run ruff format .

format-check:
    uv run ruff format --check .

typecheck:
    uv run mypy

check: test lint format-check typecheck