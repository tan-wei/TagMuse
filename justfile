set positional-arguments := true

default:
    @just --list

sync:
    uv sync --all-groups

setup:
    uv sync --all-groups
    npm ci

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

coverage:
    just test --cov=tag_muse --cov-report=term-missing --cov-report=xml:coverage.xml

lint:
    uv run ruff check .

format:
    uv run ruff format .

format-check:
    uv run ruff format --check .

typecheck:
    uv run mypy

commitlint:
    git log -1 --format=%B | npm exec --no -- commitlint

commitlint-message message:
    #!/bin/sh
    printf '%s\n' "$1" | npm exec --no -- commitlint

commitlint-range from to:
    #!/bin/sh
    npm exec --no -- commitlint --from "$1" --to "$2"

install-hooks:
    uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

uninstall-hooks:
    uv run pre-commit uninstall --hook-type pre-commit --hook-type commit-msg

check: test lint format-check typecheck