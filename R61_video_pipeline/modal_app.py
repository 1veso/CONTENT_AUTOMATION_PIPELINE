"""
R61 — Modal serverless app.

Wraps every R61 generation tool as a Modal function:
  - frame_gen        Fal Nano Banana Pro first/last frame
  - video_gen        Higgsfield first/last → 5s clip
  - voiceover_gen    ElevenLabs TTS → R2
  - hf_stitch        FFmpeg pre-mix + HyperFrames composition + R2 upload
  - blotato_schedule Blotato scheduled-post submission
  - sync_r57_to_video R57 → R61 row insertion

Each function is callable via `modal run`/`modal deploy` and additionally
exposed as a `POST` FastAPI endpoint. The endpoints are NOT wired into
n8n in this rollout — that happens later when the
ops.getautomata.ai ↔ Modal tunnel/reverse-proxy work is in place.

Build context:
  • Image: Debian slim + Python 3.11 + Node 20 + ffmpeg + npm hyperframes.
    The Node toolchain is required for hf_stitch (`npx hyperframes lint`
    and `render` shell-outs inside the per-record workdir).
  • Volume: `r61-work` mounted at /work — used as PROJECT_ROOT for the
    tools so `references/outputs/tmp/`, `hf_work/`, and `final/<tag>/`
    persist across invocations (intermediate FFmpeg mixes are expensive
    to re-do on every cold start).
  • Secrets: `r61-secrets` — operator must create before deploying:
        modal secret create r61-secrets \\
            FAL_KEY=<from R61/.env> \\
            HIGGSFIELD_API_KEY=<from R61/.env> \\
            HIGGSFIELD_SECRET=<from R61/.env> \\
            R2_ACCOUNT_ID=<...> \\
            R2_ACCESS_KEY_ID=<...> \\
            R2_SECRET_ACCESS_KEY=<...> \\
            R2_BUCKET_NAME=<...> \\
            R2_PUBLIC_URL=<...> \\
            AIRTABLE_API_KEY=<...> \\
            AIRTABLE_BASE_ID=<...> \\
            BLOTATO_API_KEY=<...> \\
            GOOGLE_API_KEY=<...> \\
            R61_VERSION_TAG=v3

Deploy:
        modal deploy R61_video_pipeline/modal_app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import modal


app = modal.App("r61-video-pipeline")

LOCAL_PROJECT = Path(__file__).parent

# ---------------------------------------------------------------- Image build
#
# Layer order: base → apt → pip → node → npm install → mount local tools.
# Node 20.x installed from the official NodeSource apt repository so that
# `npx hyperframes` resolves consistently regardless of host packaging.
# HyperFrames CLI is pulled into the image via `npm install -g`; the CLI
# uses Playwright under the hood, so we also let Modal cache the Playwright
# browser download on first use (the CLI does `npx playwright install
# chromium` on demand).

r61_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "ffmpeg",
        "curl",
        "ca-certificates",
        "gnupg",
        # Playwright system deps for the HyperFrames render path
        "libnss3", "libnspr4", "libatk1.0-0", "libatk-bridge2.0-0",
        "libcups2", "libdrm2", "libxkbcommon0", "libxcomposite1",
        "libxdamage1", "libxfixes3", "libxrandr2", "libgbm1",
        "libpango-1.0-0", "libcairo2", "libasound2",
    )
    .run_commands(
        # Install Node 20.x from NodeSource
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
        # Install HyperFrames CLI globally
        "npm install -g hyperframes@latest",
        # Pre-warm Playwright for HF's headless renderer
        "npx playwright install --with-deps chromium || true",
    )
    .pip_install_from_requirements(
        str(LOCAL_PROJECT / "tools" / "requirements.txt")
    )
    .add_local_dir(
        str(LOCAL_PROJECT / "tools"),
        remote_path="/root/tools",
    )
)

r61_secret = modal.Secret.from_name("r61-secrets")

# Persistent volume for working dirs (tmp mixes, hf_work, final/<tag>/).
# Lets a cold start reuse already-mixed audio and already-rendered finals.
r61_volume = modal.Volume.from_name("r61-work", create_if_missing=True)
WORK_MOUNT = "/work"


def _bootstrap_env_and_paths():
    """Pre-flight inside each Modal container.

    1. Bridge FAL_KEY ⇆ FAL_API_KEY (the tools accept either name).
    2. Re-root the tools' PROJECT_ROOT to the mounted /work volume so
       references/outputs/ persists across invocations. The tools read
       PROJECT_ROOT from `Path(__file__).resolve().parent.parent` which
       inside Modal resolves to /root → /work/r61, so we make /root a
       symlink to /work/r61 the first time we run.
    """
    if os.getenv("FAL_KEY") is None and os.getenv("FAL_API_KEY"):
        os.environ["FAL_KEY"] = os.environ["FAL_API_KEY"]
    elif os.getenv("FAL_API_KEY") is None and os.getenv("FAL_KEY"):
        os.environ["FAL_API_KEY"] = os.environ["FAL_KEY"]

    work_root = Path(WORK_MOUNT) / "r61"
    (work_root / "references" / "outputs").mkdir(parents=True, exist_ok=True)
    (work_root / "references" / "inputs").mkdir(parents=True, exist_ok=True)
    # Symlink /root/references → /work/r61/references so the tools' relative
    # PROJECT_ROOT resolution lands in the volume.
    refs_link = Path("/root/references")
    if not refs_link.exists():
        refs_link.symlink_to(work_root / "references", target_is_directory=True)
    sys.path.insert(0, "/root")


# ------------------------------------------------------------ Modal functions

@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 60)
def frame_gen(record_id: str | None = None, dry_run: bool = False) -> dict:
    _bootstrap_env_and_paths()
    from tools import frame_gen as fg  # type: ignore
    argv = ["--dry-run"] if dry_run else []
    if record_id:
        argv += ["--record-id", record_id]
    return {"exit_code": fg.main(argv)}


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 60)
def video_gen(record_id: str | None = None, dry_run: bool = False,
              limit: int | None = None) -> dict:
    _bootstrap_env_and_paths()
    from tools import video_gen as vg  # type: ignore
    argv = ["--dry-run"] if dry_run else []
    if record_id:
        argv += ["--record-id", record_id]
    if limit:
        argv += ["--limit", str(limit)]
    return {"exit_code": vg.main(argv)}


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 30)
def voiceover_gen(record_id: str | None = None, dry_run: bool = False,
                  confirm: str = "go") -> dict:
    _bootstrap_env_and_paths()
    from tools import voiceover_gen as vg  # type: ignore
    argv = ["--dry-run"] if dry_run else ["--confirm", confirm]
    if record_id:
        argv += ["--record-id", record_id]
    return {"exit_code": vg.main(argv)}


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 90,
              cpu=4, memory=8192)
def hf_stitch(record_id: str | None = None, all_voiceover_done: bool = False,
              skip_publish: bool = False) -> dict:
    """Hyperframes stitch — the heavy one. Higher CPU + memory for ffmpeg + render."""
    _bootstrap_env_and_paths()
    from tools import hf_stitch as hs  # type: ignore
    if record_id:
        argv = ["--record-id", record_id]
    elif all_voiceover_done:
        argv = ["--all-voiceover-done"]
    else:
        argv = ["--all-approved-or-scheduled"]
    if skip_publish:
        argv.append("--skip-publish")
    return {"exit_code": hs.main(argv)}


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 15)
def blotato_schedule(record_id: str | None = None, dry_run: bool = False,
                     limit: int | None = None) -> dict:
    _bootstrap_env_and_paths()
    from tools import blotato_schedule as bs  # type: ignore
    argv = ["--dry-run"] if dry_run else []
    if record_id:
        argv += ["--record-id", record_id]
    if limit:
        argv += ["--limit", str(limit)]
    return {"exit_code": bs.main(argv)}


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 10)
def sync_r57_to_video(dry_run: bool = False) -> dict:
    _bootstrap_env_and_paths()
    from tools import sync_r57_to_video as sync  # type: ignore
    argv = ["--dry-run"] if dry_run else []
    return {"exit_code": sync.main(argv)}


# --------------------------------------------------------------- HTTP endpoints

def _coerce_payload(payload):
    return payload or {}


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 60)
@modal.fastapi_endpoint(method="POST")
def frame_gen_http(payload: dict) -> dict:
    p = _coerce_payload(payload)
    return frame_gen.local(record_id=p.get("record_id"),
                           dry_run=bool(p.get("dry_run", False)))


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 60)
@modal.fastapi_endpoint(method="POST")
def video_gen_http(payload: dict) -> dict:
    p = _coerce_payload(payload)
    return video_gen.local(record_id=p.get("record_id"),
                           dry_run=bool(p.get("dry_run", False)),
                           limit=p.get("limit"))


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 30)
@modal.fastapi_endpoint(method="POST")
def voiceover_gen_http(payload: dict) -> dict:
    p = _coerce_payload(payload)
    return voiceover_gen.local(record_id=p.get("record_id"),
                               dry_run=bool(p.get("dry_run", False)),
                               confirm=p.get("confirm", "go"))


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 90,
              cpu=4, memory=8192)
@modal.fastapi_endpoint(method="POST")
def hf_stitch_http(payload: dict) -> dict:
    p = _coerce_payload(payload)
    return hf_stitch.local(record_id=p.get("record_id"),
                           all_voiceover_done=bool(p.get("all_voiceover_done", False)),
                           skip_publish=bool(p.get("skip_publish", False)))


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 15)
@modal.fastapi_endpoint(method="POST")
def blotato_schedule_http(payload: dict) -> dict:
    p = _coerce_payload(payload)
    return blotato_schedule.local(record_id=p.get("record_id"),
                                  dry_run=bool(p.get("dry_run", False)),
                                  limit=p.get("limit"))


@app.function(image=r61_image, secrets=[r61_secret],
              volumes={WORK_MOUNT: r61_volume}, timeout=60 * 10)
@modal.fastapi_endpoint(method="POST")
def sync_r57_to_video_http(payload: dict) -> dict:
    p = _coerce_payload(payload)
    return sync_r57_to_video.local(dry_run=bool(p.get("dry_run", False)))


# ------------------------------------------------------------ Local entrypoint

@app.local_entrypoint()
def main(stage: str = "sync", record_id: str | None = None,
         dry_run: bool = True):
    """Manual smoke-test: `modal run modal_app.py -- stage=frame record_id=rec...`"""
    if stage == "sync":
        print(sync_r57_to_video.remote(dry_run=dry_run))
    elif stage == "frame":
        print(frame_gen.remote(record_id=record_id, dry_run=dry_run))
    elif stage == "video":
        print(video_gen.remote(record_id=record_id, dry_run=dry_run))
    elif stage == "vo":
        print(voiceover_gen.remote(record_id=record_id, dry_run=dry_run))
    elif stage == "stitch":
        print(hf_stitch.remote(record_id=record_id, skip_publish=dry_run))
    elif stage == "blotato":
        print(blotato_schedule.remote(record_id=record_id, dry_run=dry_run))
    else:
        raise SystemExit(
            f"unknown stage {stage!r}; expected one of "
            "sync|frame|video|vo|stitch|blotato"
        )
