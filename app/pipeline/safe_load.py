"""Restricted checkpoint loading for workers that open third-party .ckpt files.

Shared by the BS-Roformer-SW worker and the lead/backing split worker.
"""

from __future__ import annotations

import os


def require_weights_only_loading() -> None:
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
