from __future__ import annotations

import gzip
import json
import os
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from mutagen import File

VERSION = 1
HEADER = {"type": "tag-muse-snapshot", "version": VERSION}


def _is_binary(value: Any) -> bool:
    if isinstance(value, bytes) or isinstance(getattr(value, "data", None), bytes):
        return True
    if isinstance(value, (list, tuple)):
        return any(_is_binary(item) for item in value)
    return False


def _tag_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_tag_value(item) for item in value]
    if hasattr(value, "text"):
        return _tag_value(value.text)
    if hasattr(value, "url"):
        return str(value.url)
    return str(value)


def export_tags(
    library: Path,
    output: Path,
    *,
    overwrite: bool = False,
    on_total: Callable[[int], None] | None = None,
    on_file: Callable[[], None] | None = None,
) -> dict[str, int]:
    library = library.resolve()
    output = output.resolve()
    if not library.is_dir():
        raise ValueError(f"Not a directory: {library}")
    if output.exists() and not overwrite:
        raise ValueError(f"Output already exists: {output} (use --force to replace it)")
    if not output.parent.is_dir():
        raise ValueError(f"Output directory does not exist: {output.parent}")

    counts = {"files": 0, "tracks": 0, "errors": 0, "unsupported": 0}
    descriptor, temp_name = tempfile.mkstemp(
        prefix=".tag-muse-", suffix=".jsonl.gz", dir=output.parent
    )
    os.close(descriptor)
    temp_path = Path(temp_name)

    def files() -> Iterator[Path]:
        for path in library.rglob("*"):
            if path.is_file() and path.resolve() not in (output, temp_path):
                yield path

    try:
        if on_total is not None:
            on_total(sum(1 for _ in files()))
        with gzip.open(temp_path, "wt", encoding="utf-8") as stream:
            stream.write(json.dumps(HEADER) + "\n")
            for path in files():
                counts["files"] += 1
                record: dict[str, Any] = {
                    "type": "track",
                    "path": path.relative_to(library).as_posix(),
                }
                try:
                    audio = File(path, easy=False)
                    if audio is None:
                        counts["unsupported"] += 1
                        if on_file is not None:
                            on_file()
                        continue
                    record["format"] = type(audio).__name__
                    record["tags"] = {}
                    record["binary_tags"] = []
                    if audio.tags is not None:
                        for key, value in audio.tags.items():
                            if _is_binary(value):
                                record["binary_tags"].append(str(key))
                            else:
                                record["tags"][str(key)] = _tag_value(value)
                    counts["tracks"] += 1
                except Exception as exc:
                    record["error"] = f"{type(exc).__name__}: {exc}"
                    counts["errors"] += 1
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                if on_file is not None:
                    on_file()
        os.replace(temp_path, output)
    finally:
        temp_path.unlink(missing_ok=True)
    return counts


def read_snapshot(source: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(source, "rt", encoding="utf-8") as stream:
        header = json.loads(next(stream))
        if header != HEADER:
            raise ValueError("Unsupported TagMuse snapshot version or format")
        for line in stream:
            record = json.loads(line)
            if not isinstance(record, dict) or record.get("type") != "track":
                raise ValueError("Invalid TagMuse snapshot record")
            yield record
