"""The Settings choice between Demucs and BS-Roformer-SW.

The weights have no stated licence, so choosing them needs an explicit confirm; Intel Macs
cannot run them; a failure falls back to Demucs loudly when the choice came from Settings.
No model, download or GPU is used: the worker is a stub, as in test_roformer_engine.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core import config as _config
from app.core import settings as _settings
from app.core.models import Job
from app.pipeline import roformer as rf_mod
from app.pipeline import separate as sep_mod
from app.pipeline.errors import SeparationError


@pytest.fixture(autouse=True)
def _own_models_dir(tmp_path, monkeypatch):
    """A success run writes the ready marker; never into the real models directory."""
    monkeypatch.setattr(_config, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(rf_mod, "MODELS_DIR", tmp_path / "models")


@pytest.fixture
def can_run(monkeypatch):
    import app.main as main_mod

    monkeypatch.setattr(_config, "roformer_unavailable_reason", lambda: None)
    monkeypatch.setattr(main_mod, "roformer_unavailable_reason", lambda: None)


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


def test_default_is_demucs_and_not_accepted():
    assert _settings.get_separation_engine() == "demucs"
    assert _settings.separation_engine_from_settings() is False
    assert _settings.roformer_sw_accepted() is False


def test_roformer_needs_a_confirm(can_run):
    with pytest.raises(ValueError, match="confirmation"):
        _settings.set_separation_engine("roformer-sw")
    assert _settings.get_separation_engine() == "demucs"


def test_confirmed_roformer_is_saved_and_remembered(can_run):
    assert _settings.set_separation_engine("roformer-sw", accept=True) == "roformer-sw"
    assert _settings.get_separation_engine() == "roformer-sw"
    assert _settings.roformer_sw_accepted() is True
    # Switching back and forth later needs no second confirm.
    _settings.set_separation_engine("demucs")
    assert _settings.set_separation_engine("roformer-sw") == "roformer-sw"


def test_unknown_engine_is_refused():
    with pytest.raises(ValueError, match="separation_engine"):
        _settings.set_separation_engine("spleeter", accept=True)


def test_intel_mac_cannot_choose_roformer(monkeypatch):
    monkeypatch.setattr(_config, "roformer_unavailable_reason", lambda: "intel-mac")
    with pytest.raises(ValueError, match="Intel Macs"):
        _settings.set_separation_engine("roformer-sw", accept=True)
    assert _settings.get_separation_engine() == "demucs"


def test_a_machine_without_the_package_cannot_choose_roformer(monkeypatch):
    monkeypatch.setattr(_config, "roformer_unavailable_reason", lambda: "not-installed")
    with pytest.raises(ValueError, match="not installed"):
        _settings.set_separation_engine("roformer-sw", accept=True)


def test_the_environment_still_seeds_the_default_and_a_saved_choice_wins(monkeypatch):
    monkeypatch.setattr(_config, "SEPARATION_ENGINE", "roformer-sw")
    assert _settings.get_separation_engine() == "roformer-sw"
    assert _settings.separation_engine_from_settings() is False
    _settings.set_separation_engine("demucs")
    assert _settings.get_separation_engine() == "demucs"
    assert _settings.separation_engine_from_settings() is True


def test_the_env_accept_variable_still_counts_as_a_confirm(monkeypatch, can_run):
    monkeypatch.setattr(_config, "ROFORMER_SW_ACCEPTED", True)
    assert _settings.roformer_sw_accepted() is True
    assert _settings.set_separation_engine("roformer-sw") == "roformer-sw"


# ── API ──


def test_settings_payload_reports_engine_and_status(client, can_run):
    body = client.get("/api/settings").json()
    assert body["separation_engine"] == "demucs"
    status = body["separation_engine_status"]
    assert status["roformer_available"] is True
    assert status["model_ready"] is False
    assert status["downloading"] is False
    assert status["model_total_bytes"] > 0


def test_payload_says_why_roformer_is_unavailable(client, monkeypatch):
    monkeypatch.setattr(_config, "roformer_unavailable_reason", lambda: "intel-mac")
    import app.main as main_mod

    monkeypatch.setattr(main_mod, "roformer_unavailable_reason", lambda: "intel-mac")
    status = client.get("/api/settings").json()["separation_engine_status"]
    assert status["roformer_available"] is False
    assert status["roformer_unavailable_reason"] == "intel-mac"


def test_post_without_confirm_is_rejected(client, can_run):
    r = client.post("/api/settings", json={"separation_engine": "roformer-sw"})
    assert r.status_code == 422
    assert "confirmation" in r.json()["detail"]
    assert client.get("/api/settings").json()["separation_engine"] == "demucs"


def test_post_with_confirm_saves_it(client, can_run):
    r = client.post(
        "/api/settings", json={"separation_engine": "roformer-sw", "roformer_sw_accept": True}
    )
    assert r.status_code == 200
    assert r.json()["separation_engine"] == "roformer-sw"
    assert r.json()["separation_engine_status"]["roformer_accepted"] is True


def test_a_string_true_is_not_a_confirm(client, can_run):
    r = client.post(
        "/api/settings", json={"separation_engine": "roformer-sw", "roformer_sw_accept": "true"}
    )
    assert r.status_code == 422


def test_download_progress_is_the_partial_checkpoint_size(client, tmp_path, monkeypatch, can_run):
    import app.main as main_mod

    _settings.set_separation_engine("roformer-sw", accept=True)
    monkeypatch.setattr(main_mod, "roformer_model_ready", lambda: False)
    monkeypatch.setattr(main_mod, "roformer_model_bytes", lambda: 290 * 1024 * 1024)
    status = client.get("/api/settings").json()["separation_engine_status"]
    assert status["downloading"] is True
    assert status["model_bytes"] == 290 * 1024 * 1024


# ── pipeline ──

_SUCCESS = """
import os, sys
for n in ("vocals", "drums", "bass", "guitar", "piano", "other"):
    open(os.path.join(sys.argv[3], n + ".wav"), "wb").write(b"RIFF")
sys.stderr.write("@@DONE@@\\n")
"""
_FAIL = """
import json, sys
sys.stderr.write("@@ERROR@@" + json.dumps("checkpoint download failed") + "\\n")
sys.exit(1)
"""


def _stub(code: str):
    def spawn(device: str, source: Path, out_dir: Path) -> list[str]:
        return [sys.executable, "-c", code, device, str(source), str(out_dir)]

    return spawn


@pytest.fixture
def job_dir(tmp_path: Path) -> Path:
    d = tmp_path / "job"
    d.mkdir()
    return d


def _demucs_stub(monkeypatch, job_dir):
    ran = []

    def fake(job, source, jdir, device):
        ran.append(device)
        (jdir / sep_mod.DEMUCS_MODEL / source.stem).mkdir(parents=True)
        return 0, []

    monkeypatch.setattr(sep_mod, "_run_demucs", fake)
    return ran


def test_a_settings_pick_that_fails_falls_back_to_demucs_loudly(
    job_dir, monkeypatch, can_run, tmp_path
):
    _settings.set_separation_engine("roformer-sw", accept=True)
    monkeypatch.setattr(sep_mod, "get_demucs_device", lambda: "cpu")
    monkeypatch.setattr(rf_mod, "_spawn_cmd", _stub(_FAIL))
    ran = _demucs_stub(monkeypatch, job_dir)
    job = Job(id="engine0000001")
    stems = sep_mod.separate(job, job_dir / "song.wav", job_dir)
    assert ran == ["cpu"]
    assert stems.is_dir()
    assert job.separation_engine == "demucs"
    assert "checkpoint download failed" in (job.engine_fallback or "")
    assert job.to_state()["engine_fallback"] == job.engine_fallback


def test_a_settings_pick_that_works_is_recorded_and_marks_the_model_ready(
    job_dir, monkeypatch, can_run, tmp_path
):
    _settings.set_separation_engine("roformer-sw", accept=True)
    monkeypatch.setattr(sep_mod, "get_demucs_device", lambda: "cpu")
    monkeypatch.setattr(rf_mod, "_spawn_cmd", _stub(_SUCCESS))
    ran = _demucs_stub(monkeypatch, job_dir)
    job = Job(id="engine0000002")
    sep_mod.separate(job, job_dir / "song.wav", job_dir)
    assert ran == []
    assert job.separation_engine == "roformer-sw"
    assert job.engine_fallback is None
    assert _config.roformer_model_ready() is True


def test_the_env_engine_still_fails_the_job_instead_of_falling_back(job_dir, monkeypatch):
    monkeypatch.setattr(sep_mod, "SEPARATION_ENGINE", "roformer-sw")
    monkeypatch.setattr(sep_mod, "get_demucs_device", lambda: "cpu")
    monkeypatch.setattr(rf_mod, "_spawn_cmd", _stub(_FAIL))
    _demucs_stub(monkeypatch, job_dir)
    with pytest.raises(SeparationError):
        sep_mod.separate(Job(id="engine0000003"), job_dir / "song.wav", job_dir)


def test_a_settings_pick_on_a_machine_that_cannot_run_it_uses_demucs(job_dir, monkeypatch):
    monkeypatch.setattr(sep_mod, "get_demucs_device", lambda: "cpu")
    monkeypatch.setattr(sep_mod, "_chosen_engine", lambda: ("roformer-sw", True))
    monkeypatch.setattr(_config, "roformer_unavailable_reason", lambda: "intel-mac")
    ran = _demucs_stub(monkeypatch, job_dir)
    job = Job(id="engine0000004")
    sep_mod.separate(job, job_dir / "song.wav", job_dir)
    assert ran == ["cpu"]
    assert "not available" in (job.engine_fallback or "")


def test_the_accept_flag_reaches_the_worker_environment(job_dir, monkeypatch, can_run):
    _settings.set_separation_engine("roformer-sw", accept=True)
    monkeypatch.delenv("STEMDECK_ROFORMER_SW_ACCEPT", raising=False)
    seen = {}

    def spawn(device, source, out_dir):
        return [sys.executable, "-c", _SUCCESS, device, str(source), str(out_dir)]

    real_popen = rf_mod.subprocess.Popen

    def spy(cmd, **kw):
        seen["accept"] = kw["env"].get("STEMDECK_ROFORMER_SW_ACCEPT")
        return real_popen(cmd, **kw)

    monkeypatch.setattr(rf_mod, "_spawn_cmd", spawn)
    monkeypatch.setattr(rf_mod.subprocess, "Popen", spy)
    rf_mod.separate_roformer(Job(id="engine0000005"), job_dir / "song.wav", job_dir, "cpu")
    assert seen["accept"] == "1"


def test_the_last_fallback_reason_is_kept_for_settings_and_cleared_by_a_success(
    client, job_dir, monkeypatch, can_run
):
    _settings.set_separation_engine("roformer-sw", accept=True)
    monkeypatch.setattr(sep_mod, "get_demucs_device", lambda: "cpu")
    monkeypatch.setattr(rf_mod, "_spawn_cmd", _stub(_FAIL))
    _demucs_stub(monkeypatch, job_dir)
    sep_mod.separate(Job(id="engine0000006"), job_dir / "song.wav", job_dir)
    status = client.get("/api/settings").json()["separation_engine_status"]
    assert "checkpoint download failed" in status["last_failure"]

    monkeypatch.setattr(rf_mod, "_spawn_cmd", _stub(_SUCCESS))
    sep_mod.separate(Job(id="engine0000007"), job_dir / "song.wav", job_dir)
    assert client.get("/api/settings").json()["separation_engine_status"]["last_failure"] is None


def test_a_device_on_the_network_cannot_opt_in_while_network_access_is_off(can_run):
    """allow_network gates other devices reaching the app, not outbound traffic.
    So the guarantee for the model download is: with network access off, only the
    host machine can give the consent that starts it."""
    from app.main import app

    _settings.set_allow_network(False)
    try:
        with TestClient(app, client=("203.0.113.9", 50000)) as remote:
            r = remote.post(
                "/api/settings",
                json={"separation_engine": "roformer-sw", "roformer_sw_accept": True},
            )
        assert r.status_code == 403
        assert _settings.get_separation_engine() == "demucs"
        assert _settings.roformer_sw_accepted() is False
    finally:
        _settings.set_allow_network(True)
