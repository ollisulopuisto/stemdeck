"""Replace a JSON file without ever leaving a torn one behind."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path


def write_json_atomic(path: Path, data: dict) -> None:
    """Durably replace the JSON file at ``path``.

    ``Path.write_text`` truncates first and writes second, so a crash, a full disk
    or a power cut between the two leaves an empty or half-written file where the
    old one was. This writes a uniquely named temp file beside it, flushes it to
    disk, then renames it over the original and syncs the directory so the rename survives power loss: readers see the old file or the new
    one, never a mix. A failed write leaves the old file and no temp file behind.
    """
    temp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(data, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    _fsync_directory(path.parent)


def _fsync_directory(directory: Path) -> None:
    """Flush the rename itself: without this the new name can be lost on power loss.

    Best effort. Windows cannot open a directory for syncing, and some filesystems
    refuse it; the file is already replaced either way, so a failure here is not an error.
    """
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)
