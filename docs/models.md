# Model licensing notes

Records the license basis for ML checkpoints StemDeck downloads at runtime.
Not exhaustive -- only entries where the decision wasn't a simple upstream
license file are documented here.

## Demucs (htdemucs_6s)

MIT, published by the `demucs` PyPI package (Meta/Facebook Research). No
audit needed -- an unambiguous upstream license.

## All-In-One (automatic song sections)

- **Runtime**: `all-in-one-infer` 3.x, the cross-platform inference fork of
  the All-In-One music-structure model.
- **Checkpoint**: `harmonix-all`, downloaded from the upstream Hugging Face
  repository during desktop warmup or on first use elsewhere.
- **License**: MIT for both the original All-In-One project and the
  `all-in-one-infer` runtime.
- **Upstream**: https://github.com/mir-aidj/all-in-one and
  https://github.com/openmirlab/all-in-one-infer

StemDeck runs this model on CPU after separation and passes its existing stems.
The checkpoint is not bundled in StemDeck installers.

## Whisper (lyrics transcription)

- **Runtime**: `openai-whisper` (PyPI, MIT, `openai/whisper`), on the torch
  StemDeck already ships for Demucs.
- **Checkpoints**: `large-v3-turbo` (1.6 GB) on a GPU with room for it,
  `small` (0.5 GB) on a CPU or a smaller GPU. Overridable with
  `STEMDECK_WHISPER_MODEL_GPU` / `STEMDECK_WHISPER_MODEL_CPU`.
- **License**: MIT for both the code and the published weights.
- **Upstream**: https://github.com/openai/whisper

Runs only when no lyrics were found for a job and the `transcribe_lyrics`
setting allows it (by default on a GPU only). Weights download on first use
into `<TORCH_HOME>/whisper`, or during desktop setup when transcription would
run, and are verified by Whisper's own SHA-256 check. Not bundled in StemDeck
installers.

## UVR-MDX-NET Karaoke 2 (on-demand lead/backing vocal split, #275)

- **File**: `UVR_MDXNET_KARA_2.onnx`
- **Distributed via**: `audio-separator` (PyPI, MIT,
  `nomadkaraoke/python-audio-separator`), which bundles/downloads models
  trained as part of the Ultimate Vocal Remover (UVR) project by Anjok07.
- **License**: MIT + attribution, per the `audio-separator` README:
  > "If you choose to integrate this project into some other project using
  > the default model or any other model trained as part of the UVR project,
  > please honor the MIT license by providing credit to UVR and its
  > developers."
- **Credit**: Ultimate Vocal Remover (Anjok07) -- https://github.com/Anjok07/ultimatevocalremovergui

This is the shipped default (`VOCAL_SPLIT_MODEL` in `app/core/config.py`,
overridable via `STEMDECK_KARAOKE_MODEL`).

### Rejected alternative: mel_band_roformer_karaoke (aufr33/viperx)

`audio-separator`'s community-trained roformer checkpoint
(`mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt`) has meaningfully
better reported SDR than the MDX-Net Karaoke 2 model above, and was the
originally preferred choice while scoping this feature. It was rejected after
directly verifying:

- No LICENSE file was ever published for this checkpoint, nor a stated
  license anywhere in its distribution.
- It was originally released through UVR's Boosty supporter-paywall page, not
  as a public open release.
- The public Hugging Face mirror (`jarredou/aufr33-viperx-karaoke-melroformer-model`)
  now returns 401 (gated/removed) -- confirmed directly, not secondhand.

A cleanly-licensed roformer alternative (Kimberley Jensen's
`Mel-Band-Roformer-Vocal-Model`) was also checked and found to have no
LICENSE file despite a claim to the contrary surfacing in a web search.

Since StemDeck is free/non-commercial, the practical risk of using an
unlicensed-but-freely-shared community checkpoint is low -- but a
Boosty-paywall origin is a step past "unlicensed," suggesting the author did
not intend it for free redistribution at all, and its already-dead HF mirror
makes it an unreliable thing to depend on regardless of the licensing
question. `STEMDECK_KARAOKE_MODEL` remains available as an env override for a
deployment that wants to accept that risk itself.


## BS-Roformer-SW (opt-in six-stem engine)

Selected with `STEMDECK_SEPARATION_ENGINE=roformer-sw`. Default stays Demucs
`htdemucs_6s`; nothing changes unless this is set.

- **Runtime**: `audio-separator` 0.38 to 0.45 (0.38 is the first release listing
  the model). `pyproject.toml` declares that range and `uv.lock` pins 0.45.0 on
  Linux, Windows and Apple Silicon, with numpy 2 and torch 2.6; plain `uv sync`
  is enough. Intel macOS keeps its torch 2.2 / numpy 1.26 pins and does not get
  audio-separator at all, so the Roformer engine and the lead/backing split are
  unavailable there, as before. 0.46+ needs torch 2.13 on Apple Silicon and is
  excluded until that pin is raised on purpose. The raised range also changes
  the lead/backing split's audio-separator from 0.30.2 to 0.45.0; that path was
  not re-run end to end (see below). Every audio-separator release in that range
  declares `onnx-weekly` and `onnx2torch-py313` (which also needs `onnx-weekly`)
  as hard dependencies, so the lock carries a nightly `onnx-weekly` build instead
  of the stable `onnx` the old lock had. No stable release in 0.38 to 0.45
  avoids it, and no override was added.
- **Checkpoint**: `BS-Roformer-SW.ckpt` (about 700 MB) and
  `BS-Roformer-SW.yaml`, fetched by audio-separator from
  `github.com/nomadkaraoke/python-audio-separator/releases/download/model-configs/`.
  Not bundled, and not fetched at startup or by warmup: only when a job runs
  with the engine selected and `STEMDECK_ROFORMER_SW_ACCEPT=1`.
- **Stems**: bass, drums, other, vocals, guitar, piano, written under the same
  names the Demucs engine produces as 16-bit WAV. audio-separator rescales every
  stem on its own and no option turns that off, so the worker replaces its
  normalise and write steps: stems are written as float32 with no rescaling,
  then one common gain (1/peak of the loudest stem, only if a stem exceeds full
  scale) is applied to all of them. Relative levels between stems are unchanged
  and their sum still reconstructs the separated mix. The replacement targets
  audio-separator 0.38 to 0.45 internals and the worker refuses to run if they
  are not there.
- **Loading the checkpoint**: `.ckpt` files are pickles. audio-separator's
  Roformer loader calls `torch.load` without `weights_only`, so safety would
  otherwise depend on torch's default (True from torch 2.6). The worker passes
  `weights_only=True` explicitly, refuses torch older than 2.6, and refuses to
  run if `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD` is set. A test shows a pickle with a
  code-executing payload is rejected. Restricted loading is narrower than
  default unpickling; it is not proof against every code-execution, resource or
  parser vulnerability, and it does not make the weights trustworthy. The
  yaml next to it is read with `yaml.FullLoader` by audio-separator (it contains
  `!!python/tuple`), which is less strict than `safe_load`; it is fetched from
  the same release as the checkpoint.
- **Licence: unresolved.** The weights have no stated licence and the trainer
  is unverified (the original `jarredou` Hugging Face account is gone; the
  current mirror lists `license: unknown`). The MIT licence of the surrounding
  code does not cover them. See
  https://github.com/openmirlab/bs-roformer-infer/issues/3. Do not redistribute
  them or ship them in an installer without a written statement from the
  trainer.
- **Quality evidence** (MVSep Multisong SDR, vendor benchmark of its own hosted
  models, not independently replicated): SW vocals 11.30, bass 14.62,
  drums 14.11, other 8.71, guitar 9.05, piano 7.83
  (https://www.mvsep.com/quality_checker/entry/8374); `htdemucs_6s` vocals
  8.18, bass 11.42, drums 10.59, other 2.64
  (https://www.mvsep.com/quality_checker/multisong_leaderboard?page=7).
  Guitar for `htdemucs_6s` is a separate run with other settings (5.25,
  https://www.mvsep.com/quality_checker/entry/6733), and the piano comparison
  MVSep publishes (Demucs 6s 2.23 vs SW 7.83) is a different validation set,
  so those two are directional only.
- **Not verified**: any real separation output (the checkpoint downloads and
  loads, but inference was killed by out-of-memory on a 1 GB test machine, so
  nothing was produced or listened to; the lead/backing ONNX model hit the same
  limit on a 3-second clip), Mac MPS behaviour, speed and memory (the model is
  heavy; it did not fit in a 1 GB, 2-CPU test machine), and how it sounds.
- **Run it**: `STEMDECK_SEPARATION_ENGINE=roformer-sw STEMDECK_ROFORMER_SW_ACCEPT=1 uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`
  (`/api/health` then reports `separation_engine` and `separation_model`).
- Lead/backing split is independent and unchanged (`STEMDECK_KARAOKE_MODEL`).
