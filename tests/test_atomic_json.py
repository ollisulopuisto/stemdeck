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
