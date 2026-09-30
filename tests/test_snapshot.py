from __future__ import annotations

import gzip
import json
import wave
from pathlib import Path

import pytest
from mutagen.id3 import APIC, TIT2, TPE1  # type: ignore[attr-defined]
from mutagen.wave import WAVE

from tag_muse.cli import main
from tag_muse.snapshot import export_tags, read_snapshot


def test_export_and_read_snapshot(tmp_path: Path) -> None:
    library = tmp_path / "library"
    library.mkdir()
    music = library / "école.wav"
    with wave.open(str(music), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(b"\0\0" * 8000)

    audio = WAVE(music)  # type: ignore[no-untyped-call]
    audio.add_tags()  # type: ignore[no-untyped-call]
    assert audio.tags is not None
    audio.tags.add(TIT2(encoding=3, text=["Été", "Sommer"]))
    audio.tags.add(TPE1(encoding=3, text=["François"]))
    audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=b"secret-art"))
    audio.save()

    output = library / "snapshot.jsonl.gz"
    (library / "notes.txt").write_text("not audio", encoding="utf-8")
    totals: list[int] = []
    completed: list[int] = []
    counts = export_tags(
        library,
        output,
        on_total=totals.append,
        on_file=lambda: completed.append(1),
    )
    records = list(read_snapshot(output))

    assert counts == {"files": 2, "tracks": 1, "errors": 0, "unsupported": 1}
    assert totals == [2]
    assert len(completed) == totals[0]
    assert len(records) == 1
    assert records[0]["path"] == "école.wav"
    assert records[0]["tags"]["TIT2"] == ["Été", "Sommer"]
    assert records[0]["tags"]["TPE1"] == ["François"]
    assert records[0]["binary_tags"] == ["APIC:Cover"]
    assert b"secret-art" not in output.read_bytes()
    assert main(["scan", "--source", str(output)]) == 0


def test_cli_can_reuse_snapshot_and_refuses_overwrite(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    library = tmp_path / "music"
    library.mkdir()
    (library / "notes.txt").write_text("not audio", encoding="utf-8")
    output = tmp_path / "snapshot.jsonl.gz"

    assert main(["export-tags", str(library), str(output)]) == 0
    assert list(read_snapshot(output)) == []
    assert main(["scan", "--source", str(output)]) == 0
    output_text = capsys.readouterr().out
    assert "0 tracks, 0 read errors" in output_text
    assert "files/s" in output_text
    assert "Reading snapshot" in output_text

    with pytest.raises(SystemExit, match="2"):
        main(["export-tags", str(library), str(output)])
    assert main(["export-tags", str(library), str(output), "--force"]) == 0


def test_rejects_unknown_snapshot_version(tmp_path: Path) -> None:
    output = tmp_path / "old.jsonl.gz"
    with gzip.open(output, "wt", encoding="utf-8") as stream:
        stream.write(json.dumps({"type": "tag-muse-snapshot", "version": 999}) + "\n")

    with pytest.raises(ValueError, match="Unsupported TagMuse snapshot"):
        list(read_snapshot(output))
