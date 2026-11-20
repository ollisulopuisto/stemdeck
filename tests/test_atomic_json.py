"""metadata.json is what the library is rebuilt from, so a crash while writing it must not corrupt it."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.core.atomic_json import write_json_atomic


def test_writes_readable_json(tmp_path: Path):
    folder = tmp_path / "job"
    folder.mkdir()
    path = folder / "metadata.json"
    write_json_atomic(path, {"title": "Song", "n": 1})
    assert json.loads(path.read_text(encoding="utf-8")) == {"title": "Song", "n": 1}
    assert list(folder.iterdir()) == [path]


def test_replaces_an_existing_file(tmp_path: Path):
    folder = tmp_path / "job"
    folder.mkdir()
    path = folder / "metadata.json"
    path.write_text(json.dumps({"title": "Old"}), encoding="utf-8")
    write_json_atomic(path, {"title": "New"})
    assert json.loads(path.read_text(encoding="utf-8")) == {"title": "New"}


def test_a_crash_before_the_rename_keeps_the_old_file_and_leaves_no_temp(
    tmp_path: Path, monkeypatch
):
    folder = tmp_path / "job"
    folder.mkdir()
    path = folder / "metadata.json"
    path.write_text(json.dumps({"title": "Old"}), encoding="utf-8")

    def die(*_args, **_kwargs):
        raise OSError("power cut")

    monkeypatch.setattr(os, "replace", die)
    with pytest.raises(OSError):
        write_json_atomic(path, {"title": "New"})
    assert json.loads(path.read_text(encoding="utf-8")) == {"title": "Old"}
    assert list(folder.iterdir()) == [path]


def test_unserialisable_data_keeps_the_old_file(tmp_path: Path):
    folder = tmp_path / "job"
    folder.mkdir()
    path = folder / "metadata.json"
    path.write_text(json.dumps({"title": "Old"}), encoding="utf-8")
    with pytest.raises(TypeError):
        write_json_atomic(path, {"bad": object()})
    assert json.loads(path.read_text(encoding="utf-8")) == {"title": "Old"}
    assert list(folder.iterdir()) == [path]


def test_the_directory_is_synced_after_the_rename(tmp_path: Path, monkeypatch):
    """Syncing the file is not enough: the rename lives in the directory entry, so the
    directory must be fsynced after os.replace. Checked as an ordered call sequence; real
    power-loss survival cannot be exercised from a unit test."""
    folder = tmp_path / "job"
    folder.mkdir()
    path = folder / "metadata.json"
    events: list[str] = []
    real_replace, real_fsync = os.replace, os.fsync

    def replace(src, dst):
        events.append("replace")
        real_replace(src, dst)

    def fsync(fd):
        is_dir = os.path.isdir(f"/proc/self/fd/{fd}") if os.path.exists("/proc/self/fd") else None
        events.append("fsync-dir" if is_dir else "fsync")
        real_fsync(fd)

    monkeypatch.setattr(os, "replace", replace)
    monkeypatch.setattr(os, "fsync", fsync)
    write_json_atomic(path, {"a": 1})
    assert events[:2] == ["fsync", "replace"]
    assert events[2:] in (["fsync-dir"], ["fsync"])  # "fsync" when /proc is unavailable
    assert len(events) == 3


def test_a_directory_that_cannot_be_synced_is_not_an_error(tmp_path: Path, monkeypatch):
    folder = tmp_path / "job"
    folder.mkdir()
    path = folder / "metadata.json"
    real_open = os.open

    def open_(target, flags, *args, **kwargs):
        if Path(target) == folder:
            raise PermissionError("cannot open a directory here")
        return real_open(target, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", open_)
    write_json_atomic(path, {"a": 1})
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1}
