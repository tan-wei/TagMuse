# TagMuse

TagMuse is a local-first Python application for auditing and normalizing music tag metadata.

The project starts with two goals:

1. Scan a music library, read tag metadata, and surface missing fields, typos, and unmatched values.
2. Learn formatting patterns from the existing library and apply consistent suggestions to new files.

## Project Standards

- `uv` manages dependencies, environments, and lockfiles.
- `src/` layout keeps application code isolated from project tooling.
- `pytest`, `ruff`, and `mypy` enforce a clean baseline before feature work starts.

## Runtime Stack

- `rich` provides rich terminal output and scan progress displays.
- `structlog` provides structured application logging.
- `mutagen` reads audio metadata across common tagging formats.
- `rapidfuzz` provides fuzzy matching for typo detection and candidate selection.
- `ftfy` repairs mojibake and other broken Unicode text.
- `lark` is available for future grammar-based parsing and rule DSL work.

## Getting Started

Install dependencies (requires `uv` and `just`):

```bash
just sync
```

Export tags and reuse the snapshot:

```bash
just export-tags /path/to/music-library /path/to/library-tags.jsonl.gz
just scan /path/to/library-tags.jsonl.gz
```

Run `just export-force LIBRARY OUTPUT` to replace a snapshot, `just help` for CLI
help, or `just` to list all tasks. The equivalent commands without `just` are
`uv run tag-muse export-tags LIBRARY OUTPUT` and
`uv run tag-muse scan --source OUTPUT`.

`export-tags` reads the library without modifying audio files. It streams a versioned,
gzip-compressed JSON Lines snapshot with relative paths, format-specific tag keys,
text values (including multiple values), and per-file read errors. Embedded artwork
and other binary tags are omitted; their tag keys are recorded instead. Files that
Mutagen does not recognize are skipped and counted. Existing snapshots are not
overwritten unless you pass `--force`. Snapshots may contain personal metadata and
are ignored by Git by default.

`scan --source` currently reports basic counts from a snapshot; tag-quality analysis
and direct directory scanning are not implemented yet. Snapshot format version 1
can be read later without accessing the original audio files.
Both export and snapshot reading show processed files and files per second using
Rich. Export also shows a percentage and remaining time after counting files;
snapshot reading has no known total, so it shows an indeterminate progress bar.

Run quality checks:

```bash
just check
just test tests/test_snapshot.py
just format
```

Individual checks are `just test`, `just lint`, `just format-check`, and
`just typecheck`. Without `just`, use `uv sync --all-groups`, `uv run pytest`,
`uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy`.

If you decide to initialize Git later, you can enable local hooks with:

```bash
uv run pre-commit install
```
