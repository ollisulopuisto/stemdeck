"""Opt-in BS-Roformer-SW engine: routing, explicit failure, licence gate.

Uses the same stub-worker seam as test_pipeline_vocal_split.py, so no model,
no download and no GPU are needed. What these cannot show is that the real
checkpoint separates audio: that needs the ~700 MB weights and a machine with
the RAM to run them.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.core.config import STEM_NAMES
from app.core.models import Job
from app.pipeline import roformer as rf_mod
from app.pipeline import roformer_worker as rw_mod
from app.pipeline import safe_load as safe_load_mod
from app.pipeline import separate as sep_mod
from app.pipeline.errors import SeparationError

_SUCCESS = """
import os, sys
out = sys.argv[3]
for n in ("vocals", "drums", "bass", "guitar", "piano", "other"):
    open(os.path.join(out, n + ".wav"), "wb").write(b"RIFF")
sys.stderr.write("@@DONE@@\\n")
"""

_FAIL = """
import json, sys
sys.stderr.write("@@ERROR@@" + json.dumps("checkpoint download failed") + "\\n")
sys.exit(1)
"""

_PARTIAL = """
import os, sys
open(os.path.join(sys.argv[3], "vocals.wav"), "wb").write(b"RIFF")
sys.stderr.write("@@DONE@@\\n")
"""


def _stub(code: str):
    def spawn(device: str, source: Path, out_dir: Path) -> list[str]:
        return [sys.executable, "-c", code, device, str(source), str(out_dir)]

    return spawn


@pytest.fixture()
def job() -> Job:
    return Job(id="roformer00001")


@pytest.fixture()
def job_dir(tmp_path: Path) -> Path:
    d = tmp_path / "job"
    d.mkdir()
    (d / "source.wav").write_bytes(b"RIFF")
    return d


def test_success_returns_all_six_stems(job, job_dir, monkeypatch):
    monkeypatch.setattr(rf_mod, "_spawn_cmd", _stub(_SUCCESS))
    root = rf_mod.separate_roformer(job, job_dir / "source.wav", job_dir, "cpu")
    assert sorted(p.stem for p in root.glob("*.wav")) == sorted(STEM_NAMES)


def test_failure_is_explicit_and_names_the_engine(job, job_dir, monkeypatch):
    monkeypatch.setattr(rf_mod, "_spawn_cmd", _stub(_FAIL))
    with pytest.raises(SeparationError) as exc:
        rf_mod.separate_roformer(job, job_dir / "source.wav", job_dir, "cpu")
    assert "roformer-sw" in str(exc.value)
    assert "BS-Roformer-SW" in str(exc.value)
    assert "checkpoint download failed" in str(exc.value)


def test_success_without_all_stems_is_an_error(job, job_dir, monkeypatch):
    monkeypatch.setattr(rf_mod, "_spawn_cmd", _stub(_PARTIAL))
    with pytest.raises(SeparationError, match="did not write"):
        rf_mod.separate_roformer(job, job_dir / "source.wav", job_dir, "cpu")


def test_separate_routes_to_roformer_and_never_falls_back(job, job_dir, monkeypatch):
    monkeypatch.setattr(sep_mod, "SEPARATION_ENGINE", "roformer-sw")
    monkeypatch.setattr(sep_mod, "get_demucs_device", lambda: "cpu")
    monkeypatch.setattr(rf_mod, "_spawn_cmd", _stub(_FAIL))

    def boom(*a, **k):
        raise AssertionError("demucs must not run when the roformer engine fails")

    monkeypatch.setattr(sep_mod, "_run_demucs", boom)
    with pytest.raises(SeparationError):
        sep_mod.separate(job, job_dir / "source.wav", job_dir)


def test_prewarm_skips_demucs_worker_for_roformer(monkeypatch):
    monkeypatch.setattr(sep_mod, "PREWARM_WORKER", True)
    monkeypatch.setattr(sep_mod, "SEPARATION_ENGINE", "roformer-sw")

    def boom(*a, **k):
        raise AssertionError("no demucs worker for the roformer engine")

    monkeypatch.setattr(sep_mod, "_get_worker", boom)
    sep_mod.prewarm("cpu")


def test_worker_refuses_without_licence_opt_in(tmp_path, monkeypatch):
    monkeypatch.setattr(rw_mod, "ROFORMER_SW_ACCEPTED", False)
    with pytest.raises(RuntimeError, match="no stated licence"):
        rw_mod._run("cpu", str(tmp_path / "x.wav"), str(tmp_path / "out"))
    # Refusal happens before any output dir or download is created.
    assert not (tmp_path / "out").exists()


def test_old_audio_separator_is_reported_not_ignored(monkeypatch):
    import importlib.metadata as md

    monkeypatch.setattr(md, "version", lambda name: "0.30.2")
    with pytest.raises(RuntimeError, match="needs 0.38 or newer"):
        rw_mod._check_audio_separator_version()


def test_unknown_engine_value_is_rejected(monkeypatch):
    import importlib

    import app.core.config as cfg

    monkeypatch.setenv("STEMDECK_SEPARATION_ENGINE", "roformer")
    with pytest.raises(RuntimeError, match="not supported"):
        importlib.reload(cfg)
    monkeypatch.delenv("STEMDECK_SEPARATION_ENGINE")
    importlib.reload(cfg)


# --- gain handling, writer replacement and checkpoint loading safety -------------
# These run against the real installed audio-separator and torch, not stubs.


@pytest.fixture()
def restore_patches():
    import torch
    from audio_separator.separator.common_separator import CommonSeparator
    from audio_separator.separator.uvr_lib_v5 import spec_utils

    saved = (torch.load, CommonSeparator.write_audio, spec_utils.normalize)
    yield
    torch.load, CommonSeparator.write_audio, spec_utils.normalize = saved


def test_finalize_applies_one_gain_and_keeps_relative_levels(tmp_path):
    np = pytest.importorskip("numpy")
    sf = pytest.importorskip("soundfile")
    loud = np.full((4410, 2), 2.0, dtype=np.float32)
    quiet = np.full((4410, 2), 0.5, dtype=np.float32)
    for name in STEM_NAMES:
        sf.write(
            tmp_path / f"{name}.wav", loud if name == "vocals" else quiet, 44100, subtype="FLOAT"
        )

    gain = rw_mod.finalize_stems(str(tmp_path))

    assert gain == pytest.approx(0.5)
    v, _ = sf.read(tmp_path / "vocals.wav")
    d, _ = sf.read(tmp_path / "drums.wav")
    assert sf.info(tmp_path / "vocals.wav").subtype == "PCM_16"
    assert v.max() == pytest.approx(1.0, abs=1e-3)
    assert d.max() == pytest.approx(0.25, abs=1e-3)
    assert (v.max() / d.max()) == pytest.approx(4.0, rel=1e-2)  # 2.0 / 0.5 before


def test_finalize_leaves_levels_alone_when_nothing_clips(tmp_path):
    np = pytest.importorskip("numpy")
    sf = pytest.importorskip("soundfile")
    for i, name in enumerate(STEM_NAMES):
        sf.write(
            tmp_path / f"{name}.wav",
            np.full((1000, 2), 0.1 * (i + 1), dtype=np.float32),
            44100,
            subtype="FLOAT",
        )
    assert rw_mod.finalize_stems(str(tmp_path)) == 1.0
    for i, name in enumerate(STEM_NAMES):
        data, _ = sf.read(tmp_path / f"{name}.wav")
        assert data.max() == pytest.approx(0.1 * (i + 1), abs=1e-3)


def test_replaced_writer_keeps_overrange_float_and_no_normalisation(tmp_path, restore_patches):
    np = pytest.importorskip("numpy")
    sf = pytest.importorskip("soundfile")
    from types import SimpleNamespace

    from audio_separator.separator.common_separator import CommonSeparator
    from audio_separator.separator.uvr_lib_v5 import spec_utils

    rw_mod._install_gain_preserving_writer()

    loud = np.full((100, 2), 1.5, dtype=np.float32)
    assert spec_utils.normalize(loud.copy(), max_peak=0.9, min_peak=0.5).max() == pytest.approx(1.5)

    me = SimpleNamespace(output_dir=str(tmp_path), sample_rate=44100)
    CommonSeparator.write_audio(me, "vocals.wav", loud)
    data, sr = sf.read(tmp_path / "vocals.wav")
    assert sr == 44100
    assert sf.info(tmp_path / "vocals.wav").subtype == "FLOAT"
    assert data.max() == pytest.approx(1.5)  # not clipped, not rescaled, not wrapped to int16


def test_weights_only_guard_blocks_malicious_pickle(tmp_path, monkeypatch, restore_patches):
    torch = pytest.importorskip("torch")
    import pickle

    marker = tmp_path / "pwned"

    class Evil:
        def __reduce__(self):
            return (Path(marker).write_text, ("x",))

    bad = tmp_path / "bad.ckpt"
    with open(bad, "wb") as f:
        pickle.dump(Evil(), f)

    monkeypatch.delenv("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", raising=False)
    safe_load_mod.require_weights_only_loading()
    with pytest.raises(pickle.UnpicklingError):
        torch.load(bad, map_location="cpu")  # no weights_only argument, as audio-separator calls it
    assert not marker.exists()


def test_guard_refuses_when_environment_disables_weights_only(monkeypatch, restore_patches):
    pytest.importorskip("torch")
    monkeypatch.setenv("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")
    with pytest.raises(RuntimeError, match="weights_only"):
        safe_load_mod.require_weights_only_loading()
