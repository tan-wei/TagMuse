from __future__ import annotations

from pathlib import Path

import pytest

from tag_muse.cli import main


def test_scan_command_placeholder(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = main(["scan", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "scan command placeholder" in captured.out


def test_suggest_command_placeholder(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = main(["suggest", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "suggest command placeholder" in captured.out
