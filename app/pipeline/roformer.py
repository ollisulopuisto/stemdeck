"""Opt-in six-stem separation with BS-Roformer-SW (STEMDECK_SEPARATION_ENGINE=roformer-sw).

Spawns app/pipeline/roformer_worker.py once per job and returns the directory
holding vocals/drums/bass/guitar/piano/other .wav, the same shape collect()
already takes from the demucs engine. There is deliberately no fallback to
demucs here: if this fails the job fails, and the error names this engine
and model so a Roformer problem is never reported as a Demucs result.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from app.core.config import (
    ROFORMER_OUT_DIRNAME,
    ROFORMER_SW_MODEL,
    STEM_NAMES,
    TIMEOUT_DEMUCS_STALL,
)
from app.core.models import Job, JobCancelled, _set
from app.core.registry import set_proc
from app.pipeline.errors import SeparationError

logger = logging.getLogger("stemdeck.pipeline")

_PCT_RE = re.compile(r"(\d{1,3})%")


def _spawn_cmd(device: str, source: Path, out_dir: Path) -> list[str]:
    """Module-level seam so tests can swap in a stub worker."""
    return [sys.executable, "-m", "app.pipeline.roformer_worker", device, str(source), str(out_dir)]


def separate_roformer(job: Job, source: Path, job_dir: Path, device: str) -> Path:
    """Run BS-Roformer-SW on `source`. Returns the stems directory.

    Raises SeparationError (with the stderr tail) on any failure, and
    JobCancelled when the exit was caused by POST /cancel."""
    out_dir = job_dir / ROFORMER_OUT_DIRNAME / source.stem
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["STEMDECK_PARENT_PID"] = str(os.getpid())
    env["PYTHONIOENCODING"] = "utf-8:replace"
    try:
        import certifi

        env.setdefault("SSL_CERT_FILE", certifi.where())
        env.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
    except ModuleNotFoundError:
        pass

    _set(job, progress=0.0, stage=f"Separating with {ROFORMER_SW_MODEL}...")
    proc = subprocess.Popen(
        _spawn_cmd(device, source, out_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )
    set_proc(job.id, proc)

    tail: list[str] = []
    last_output = [time.monotonic()]
    done_evt = threading.Event()

    def _watchdog() -> None:
        while not done_evt.wait(timeout=30):
            if proc.poll() is not None:
                return
            if time.monotonic() - last_output[0] > TIMEOUT_DEMUCS_STALL:
                logger.warning(
                    "roformer worker stalled for %ss with no output, terminating job %s",
                    TIMEOUT_DEMUCS_STALL,
                    job.id,
                )
                proc.terminate()
                return

    wt = threading.Thread(target=_watchdog, daemon=True)
    wt.start()
    job_ok = False
    try:
        assert proc.stderr is not None
        for raw_line in proc.stderr:
            last_output[0] = time.monotonic()
            line = raw_line.strip()
            if not line:
                continue
            if line == "@@DONE@@":
                job_ok = True
                break
            if line.startswith("@@ERROR@@"):
                msg = line[len("@@ERROR@@") :]
                try:
                    msg = json.loads(msg)
                except json.JSONDecodeError:
                    pass
                tail.append(str(msg))
                break
            m = _PCT_RE.search(line)
            if m:
                pct = max(0, min(100, int(m.group(1))))
                _set(job, progress=pct / 100.0, stage=f"Separating {pct}% (BS-Roformer-SW)")
            else:
                tail.append(line)
                if len(tail) > 40:
                    tail.pop(0)
    finally:
        done_evt.set()
        set_proc(job.id, None)
        wt.join(timeout=2)
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()

    if job.cancel_requested:
        raise JobCancelled()
    if not job_ok:
        detail = "\n".join(tail[-15:]) if tail else "(no stderr captured)"
        logger.error("[%s] %s failed on %s:\n%s", job.id, ROFORMER_SW_MODEL, device, detail)
        last = tail[-1] if tail else "worker exited without a result"
        raise SeparationError(
            f"{ROFORMER_SW_MODEL} separation failed (engine roformer-sw, not demucs): {last}",
            tail=tail[-40:],
            device=device,
        )
    missing = [n for n in STEM_NAMES if not (out_dir / f"{n}.wav").is_file()]
    if missing:
        raise SeparationError(
            f"{ROFORMER_SW_MODEL} reported success but did not write: {', '.join(missing)}",
            device=device,
        )
    return out_dir
