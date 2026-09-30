from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.text import Text

from tag_muse.snapshot import export_tags, read_snapshot


class FileSpeedColumn(ProgressColumn):
    def render(self, task: Task) -> Text:
        return Text(f"{(task.speed or 0):,.1f} files/s")


def file_progress(console: Console) -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("{task.completed:.0f} files"),
        FileSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tag-muse",
        description="Audit and normalize music tag metadata.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a music library and inspect tag quality.",
    )
    scan_parser.add_argument(
        "library",
        nargs="?",
        default=".",
        help="Path to the music library.",
    )
    scan_parser.add_argument(
        "--source",
        type=Path,
        help="Read a previously exported TagMuse snapshot instead of a directory.",
    )

    export_parser = subparsers.add_parser(
        "export-tags", help="Export audio tags to a compressed, reusable snapshot."
    )
    export_parser.add_argument("library", type=Path, help="Music library directory.")
    export_parser.add_argument("output", type=Path, help="Destination .jsonl.gz file.")
    export_parser.add_argument("--force", action="store_true", help="Replace an existing snapshot.")

    suggest_parser = subparsers.add_parser(
        "suggest",
        help="Preview normalization suggestions for a music library.",
    )
    suggest_parser.add_argument(
        "library",
        nargs="?",
        default=".",
        help="Path to the music library.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()

    if args.command == "scan":
        if args.source is not None:
            try:
                tracks = errors = 0
                with file_progress(console) as progress:
                    task = progress.add_task("Reading snapshot", total=None)
                    for record in read_snapshot(args.source):
                        if "error" in record:
                            errors += 1
                        else:
                            tracks += 1
                        progress.advance(task)
            except (OSError, ValueError, EOFError, StopIteration) as exc:
                parser.error(f"Cannot read snapshot: {exc}")
            console.print(f"Snapshot: {tracks} tracks, {errors} read errors")
            return 0
        print(f"scan command placeholder for {args.library}")
        return 0

    if args.command == "export-tags":
        try:
            with file_progress(console) as progress:
                task = progress.add_task("Counting files", total=None)
                counts = export_tags(
                    args.library,
                    args.output,
                    overwrite=args.force,
                    on_total=lambda total: progress.update(
                        task, total=total, description="Exporting"
                    ),
                    on_file=lambda: progress.advance(task),
                )
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        console.print(
            f"Exported {counts['tracks']} tracks to {args.output} "
            f"({counts['errors']} errors, {counts['unsupported']} unsupported files)"
        )
        return 0

    if args.command == "suggest":
        print(f"suggest command placeholder for {args.library}")
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2
