"""Regression coverage for the path guards, independent of pipeline setup."""

import pytest

from app.core import settings
from app.core.stems_location import StemsLocationError, validate_target


def test_cookie_symlink_is_rejected_before_resolve(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "_state", {})
    monkeypatch.setattr(settings, "_SETTINGS_PATH", tmp_path / "settings.json")
    real = tmp_path / "cookies.txt"
    real.write_text("# Netscape HTTP Cookie File\n")
    link = tmp_path / "link.txt"
    link.symlink_to(real)
    with pytest.raises(ValueError, match="path is not allowed"):
        settings.set_cookies_file(str(link))
    assert settings.get_cookies_file() is None
    assert settings.set_cookies_file(str(real)) == str(real.resolve())


def test_library_rejects_symlink_and_traversal_without_creating_target(tmp_path):
    current = tmp_path / "current"
    current.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    link = tmp_path / "link"
    link.symlink_to(other, target_is_directory=True)
    for candidate in (link, tmp_path / "unused" / ".." / "new"):
        with pytest.raises(StemsLocationError, match="not allowed"):
            validate_target(candidate, current)
    assert list(other.iterdir()) == []
    assert not (tmp_path / "unused").exists()
    assert not (tmp_path / "new").exists()


def test_library_rejects_intermediate_symlink_without_creating_target(tmp_path):
    """An intermediate symlinked directory resolves outside the path supplied.
    The final component is not itself a symlink, so a last-component-only guard
    would let it through and even create a folder under the symlink target."""
    current = tmp_path / "current"
    current.mkdir()
    real = tmp_path / "real"
    real.mkdir()
    link_dir = tmp_path / "link"
    link_dir.symlink_to(real, target_is_directory=True)
    candidate = link_dir / "nested"
    with pytest.raises(StemsLocationError, match="not allowed"):
        validate_target(candidate, current)
    assert not candidate.exists()
    assert not list(real.iterdir()), "nothing may be created through the symlink"


def test_traversal_is_rejected_on_raw_string_before_path_built(tmp_path):
    """CodeQL py/path-injection: traversal markers in the raw user string must be
    rejected before a Path is built from it. The check must run on the un-expanded
    input so resolve() cannot collapse ".." and hide the evidence."""
    current = tmp_path / "current"
    current.mkdir()
    with pytest.raises(StemsLocationError, match="not allowed"):
        validate_target(tmp_path / "child" / ".." / "escape", current)
    assert not (tmp_path / "child").exists()
    assert not (tmp_path / "escape").exists()
