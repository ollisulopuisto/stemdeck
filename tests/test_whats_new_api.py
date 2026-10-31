"""The What's New endpoint serves the bundled changelog as markdown."""

from fastapi.testclient import TestClient

from app.api import whats_new
from app.main import app


def test_whats_new_serves_repo_changelog():
    with TestClient(app) as client:
        r = client.get("/api/whats-new")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    # The real repository changelog: released calver/semver sections.
    assert "## [0.20.0] - 2026-10-04" in r.text
    assert "## [Unreleased]" in r.text


def test_whats_new_404_when_not_bundled(monkeypatch, tmp_path):
    monkeypatch.setattr(whats_new, "STATIC_DIR", tmp_path / "no-static")
    monkeypatch.setattr(whats_new, "ROOT", tmp_path / "no-root")
    with TestClient(app) as client:
        assert client.get("/api/whats-new").status_code == 404


def test_whats_new_prefers_packaged_static_copy(monkeypatch, tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    (static / "CHANGELOG.md").write_text("packaged copy\n", encoding="utf-8")
    monkeypatch.setattr(whats_new, "STATIC_DIR", static)
    with TestClient(app) as client:
        r = client.get("/api/whats-new")
    assert r.status_code == 200
    assert r.text == "packaged copy\n"
