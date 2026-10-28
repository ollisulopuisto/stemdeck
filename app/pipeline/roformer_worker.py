"""Six-stem BS-Roformer-SW worker (opt-in engine, STEMDECK_SEPARATION_ENGINE=roformer-sw).

Run as its own process: `python -m app.pipeline.roformer_worker <device> <source>
<out_dir>`. One job per process, like vocal_split_worker.py: the model is
~700 MB and an explicit failure is better than a half-warm persistent worker.

Writes vocals/drums/bass/guitar/piano/other .wav into out_dir -- the same stem
names the demucs engine produces -- via the `audio-separator` package, then
exactly one of (same protocol as the other workers):
  "@@DONE@@"                        -- all six stems written
  "@@ERROR@@<json-encoded message>" -- failure; process exits(1)

The weights have no stated licence, so this refuses to download them unless
STEMDECK_ROFORMER_SW_ACCEPT=1. A checkpoint that is already on disk is still
refused without it: the opt-in is about use, not only about the download.
"""

from __future__ import annotations

import json
import os
import sys

from app.core.config import ROFORMER_SW_ACCEPTED, ROFORMER_SW_MODEL, ROFORMER_SW_NOTICE, STEM_NAMES
from app.core.process import arm_parent_watchdog

# audio-separator learned BS-Roformer-SW in 0.38.0.
MIN_AUDIO_SEPARATOR = (0, 38)
_BLOCK = 1 << 18


def _check_audio_separator_version() -> None:
    from importlib.metadata import version

    raw = version("audio-separator")
    parts = []
    for piece in raw.split(".")[:2]:
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    if tuple(parts) < MIN_AUDIO_SEPARATOR:
        raise RuntimeError(
            f"audio-separator {raw} is installed but BS-Roformer-SW needs 0.38 or newer "
            "(it also needs numpy 2). Install a newer audio-separator for this "
            "environment, or set STEMDECK_SEPARATION_ENGINE=demucs."
        )


def _require_weights_only_loading() -> None:
    """Make every torch.load in this process refuse arbitrary pickle.

    audio-separator's Roformer loader calls torch.load(path, map_location=...)
    without weights_only, so safety rests on torch's default (True from 2.6).
    The weights here come from an unverified trainer, so do not rest on a
    default: refuse an environment that turns it off, and pass it explicitly.
    """
    import torch

    if os.environ.get("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "").strip().lower() not in (
        "",
        "0",
        "false",
    ):
        raise RuntimeError(
            "TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD is set; refusing to unpickle an "
            "unverified checkpoint without weights_only loading."
        )
    major_minor = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
    if major_minor < (2, 6):
        raise RuntimeError(
            f"torch {torch.__version__} cannot be relied on for weights_only loading "
            "of an unverified checkpoint; need torch 2.6 or newer."
        )
    original = torch.load

    def load(*args, **kwargs):
        kwargs.setdefault("weights_only", True)
        return original(*args, **kwargs)

    torch.load = load


def _install_gain_preserving_writer() -> None:
    """Stop audio-separator rescaling each stem on its own.

    Its multi-stem path normalises every stem to a peak threshold (twice: once
    when splitting, once when writing) and then converts to int16, and no
    Separator option turns that off. Independent rescaling changes the gain
    between stems, so they no longer add up to the mix. Replace both steps:
    normalisation becomes a no-op and stems are written as float32, then
    finalize_stems() applies one gain to all of them.
    """
    import numpy as np
    import soundfile as sf
    from audio_separator.separator.common_separator import CommonSeparator
    from audio_separator.separator.uvr_lib_v5 import spec_utils

    if not callable(getattr(spec_utils, "normalize", None)) or not hasattr(
        CommonSeparator, "write_audio"
    ):
        raise RuntimeError(
            "installed audio-separator no longer matches the writer this worker "
            "replaces; refusing to run with per-stem normalisation (use 0.38 to 0.45)."
        )

    def no_normalize(wave, max_peak=1.0, min_peak=None):
        return np.asarray(wave)

    def write_audio(self, stem_path, stem_source):
        data = np.asarray(stem_source, dtype=np.float32)
        if not np.isfinite(data).all():
            raise RuntimeError("separated audio contains non-finite samples")
        path = os.path.join(self.output_dir, stem_path) if self.output_dir else stem_path
        sf.write(path, data, self.sample_rate, subtype="FLOAT")

    spec_utils.normalize = no_normalize
    CommonSeparator.write_audio = write_audio


def finalize_stems(out_dir: str, names=STEM_NAMES) -> float:
    """Convert the float32 stems to 16-bit WAV with ONE gain for all of them.

    The gain is 1/peak of the loudest stem when any stem exceeds full scale and
    1.0 otherwise, so relative levels between stems are untouched and their sum
    still reconstructs the separated mix. Returns the gain applied. Streams in
    blocks; a 20-minute stereo stem is ~400 MB as float32.
    """
    import numpy as np
    import soundfile as sf

    peak = 0.0
    for name in names:
        with sf.SoundFile(os.path.join(out_dir, f"{name}.wav")) as f:
            for block in f.blocks(blocksize=_BLOCK, dtype="float32"):
                if block.size:
                    peak = max(peak, float(np.abs(block).max()))
    gain = 1.0 / peak if peak > 1.0 else 1.0
    for name in names:
        path = os.path.join(out_dir, f"{name}.wav")
        tmp = path + ".tmp.wav"
        with (
            sf.SoundFile(path) as src,
            sf.SoundFile(
                tmp, "w", samplerate=src.samplerate, channels=src.channels, subtype="PCM_16"
            ) as dst,
        ):
            for block in src.blocks(blocksize=_BLOCK, dtype="float32"):
                dst.write(np.clip(block * gain, -1.0, 1.0))
        os.replace(tmp, path)
    return gain


def _run(device: str, source: str, out_dir: str) -> None:
    if not ROFORMER_SW_ACCEPTED:
        raise RuntimeError(ROFORMER_SW_NOTICE)
    if device == "cpu":
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    elif device == "mps":
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

    _check_audio_separator_version()
    _require_weights_only_loading()
    _install_gain_preserving_writer()
    from audio_separator.separator import Separator

    from app.core.config import MODELS_DIR
    from app.core.model_cache import load_or_heal, roformer_artifacts

    os.makedirs(out_dir, exist_ok=True)
    separator = Separator(
        log_level=40,
        model_file_dir=str(MODELS_DIR / "audio-separator"),
        output_dir=out_dir,
        output_format="WAV",
    )
    load_or_heal(
        lambda: separator.load_model(model_filename=ROFORMER_SW_MODEL),
        lambda: roformer_artifacts(MODELS_DIR, ROFORMER_SW_MODEL),
    )
    separator.separate(source, {name: name for name in STEM_NAMES})

    missing = [n for n in STEM_NAMES if not os.path.isfile(os.path.join(out_dir, f"{n}.wav"))]
    if missing:
        raise RuntimeError(f"BS-Roformer-SW did not write: {', '.join(missing)}")
    finalize_stems(out_dir)


def main() -> None:
    arm_parent_watchdog()
    if len(sys.argv) < 4:
        sys.stderr.write("@@ERROR@@usage: roformer_worker <device> <source> <out_dir>\n")
        sys.stderr.flush()
        sys.exit(1)
    device, source, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        _run(device, source, out_dir)
    except Exception as e:
        sys.stderr.write(f"@@ERROR@@{json.dumps(str(e))}\n")
        sys.stderr.flush()
        sys.exit(1)
    sys.stderr.write("@@DONE@@\n")
    sys.stderr.flush()


if __name__ == "__main__":
    main()
