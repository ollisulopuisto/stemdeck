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


def test_cookie_rejects_null_byte_in_path(tmp_path, monkeypatch):
    """A NUL byte can truncate a path on some filesystems and is an injection
    marker; it must be rejected before the string ever becomes a Path."""
    monkeypatch.setattr(settings, "_state", {})
    monkeypatch.setattr(settings, "_SETTINGS_PATH", tmp_path / "settings.json")
    real = tmp_path / "cookies.txt"
    real.write_text("# Netscape HTTP Cookie File\n")
    with pytest.raises(ValueError, match="path is not allowed"):
        settings.set_cookies_file(str(real) + "\x00")
    assert settings.get_cookies_file() is None


def test_library_rejects_null_byte_in_path(tmp_path):
    """Same NUL-byte guard for the stems folder: rejected at the raw-string
    level, before Path() ever sees it."""
    current = tmp_path / "current"
    current.mkdir()
    with pytest.raises(StemsLocationError, match="not allowed"):
        validate_target(str(tmp_path / "elsewhere") + "\x00", current)
    assert not (tmp_path / "elsewhere").exists()
