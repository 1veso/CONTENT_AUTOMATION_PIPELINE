"""
R57 — Modal serverless app.

Wraps the existing local tools in `R57_content_engine/tools/` as Modal
functions. Each function is exposed both as an importable `@app.function`
(callable via `modal run`) and as a FastAPI POST endpoint (callable from
n8n once the tunnel/reverse-proxy work is done — explicitly NOT wired
into n8n in this rollout).

Build context:
  • Image: Python 3.11 + tools/requirements.txt + tools/ source mounted
    in. The R57 toolchain is pure Python (Fal HTTP + Airtable HTTP), no
    Node/ffmpeg/system deps needed.
  • Secrets: `r57-secrets` — operator must create this before deploying:
        modal secret create r57-secrets \\
            FAL_KEY=<from R57/.env> \\
            FAL_API_KEY=<from R57/.env> \\
            AIRTABLE_API_KEY=<from R57/.env> \\
            BLOTATO_API_KEY=<from R57/.env> \\
            GOOGLE_API_KEY=<from R57/.env> \\
            TELEGRAM_BOT_TOKEN=<bot token> \\
            TELEGRAM_CHAT_ID=1077552316
    The pipeline tools read these via os.environ; the local-only
    `load_dotenv()` calls silently no-op in Modal (no .env file present).
    TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID drive per-record progress pings —
    if unset, notify_progress() silently no-ops.

Deploy:
        modal deploy R57_content_engine/modal_app.py

Local invocation while developing:
        modal run R57_content_engine/modal_app.py::generate_images
        modal run R57_content_engine/modal_app.py::schedule_blotato
"""

from __future__ import annotations

import sys
from pathlib import Path

import modal


# ---------------------------------------------------------------- App + Image

app = modal.App("r57-content-engine")

# Python deps come from the same requirements.txt the local pipeline uses.
LOCAL_PROJECT = Path(__file__).parent

r57_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements(
        str(LOCAL_PROJECT / "tools" / "requirements.txt")
    )
    # FastAPI is required for `@modal.fastapi_endpoint` in Modal 1.4+;
    # it's no longer auto-installed.
    .pip_install("fastapi[standard]")
    # Mount the tools/ package and providers/ subpackage into the image.
    .add_local_dir(
        str(LOCAL_PROJECT / "tools"),
        remote_path="/root/tools",
    )
)

# `r57-secrets` is created by the operator out-of-band (see module docstring).
r57_secret = modal.Secret.from_name("r57-secrets")


# --------------------------------------------------------------- Helper shims
#
# Each Modal function imports the local tool module fresh on every cold-start.
# The tools call `load_dotenv(...)` against a path that won't exist inside the
# container; dotenv ignores the miss and the os.environ values from the secret
# carry through. The `if FAL_KEY missing` bridge in the tools is preserved.


def _bootstrap_env():
    """Mirror the local-tools env shim: FAL_KEY ⇆ FAL_API_KEY."""
    import os
    if os.getenv("FAL_KEY") is None and os.getenv("FAL_API_KEY"):
        os.environ["FAL_KEY"] = os.environ["FAL_API_KEY"]
    elif os.getenv("FAL_API_KEY") is None and os.getenv("FAL_KEY"):
        os.environ["FAL_API_KEY"] = os.environ["FAL_KEY"]


# ----------------------------------------------------------- Modal functions

@app.function(image=r57_image, secrets=[r57_secret], timeout=60 * 30)
def generate_images(record_ids: list[str] | None = None,
                    dry_run: bool = False) -> dict:
    """Generate R57 images for specific record ids (or all pending)."""
    _bootstrap_env()
    sys.path.insert(0, "/root")
    from tools import image_gen, airtable, notify  # noqa: E402

    rows = airtable.get_records()
    if record_ids:
        rows = [r for r in rows if r.get("id") in set(record_ids)]
    total = len(rows)
    summary = {"requested": total, "ok": 0, "failed": 0, "ids": []}
    for r in rows:
        try:
            if not dry_run:
                image_gen.generate_for_record(r)
            summary["ok"] += 1
            summary["ids"].append(r.get("id"))
            notify.notify_progress(
                "R57", "Images", summary["ok"], total, "generated", emoji="🖼"
            )
        except Exception as e:
            summary["failed"] += 1
            summary.setdefault("errors", []).append(
                {"id": r.get("id"), "error": str(e)[:200]}
            )
    return summary


@app.function(image=r57_image, secrets=[r57_secret], timeout=60 * 10)
def schedule_blotato(record_ids: list[str] | None = None,
                     dry_run: bool = False) -> dict:
    """Schedule R57 records into Blotato. Always future scheduledTime."""
    _bootstrap_env()
    sys.path.insert(0, "/root")
    # R57's Blotato scheduler lives in the providers package historically.
    # If the tool name differs in the local repo, this import will fail
    # loudly inside the Modal container and the operator will know to add
    # the wrapping module before re-deploy.
    try:
        from tools import blotato_schedule as scheduler  # type: ignore
        from tools import notify  # type: ignore
    except ImportError as e:
        return {"status": "error", "reason": f"R57 has no blotato_schedule tool: {e}"}
    rows = scheduler.get_pending_records()
    if record_ids:
        rows = [r for r in rows if r.get("id") in set(record_ids)]
    total = len(rows)
    result = scheduler.run_batch(rows, dry_run=dry_run)
    # Run-level summary — per-record progress lives inside scheduler.run_batch,
    # which we don't refactor here. Operator sees a single confirmation ping.
    ok = result.get("scheduled", result.get("ok", 0))
    notify.notify_progress("R57", "Scheduled", ok, total, "posts", emoji="📅")
    return result


# ------------------------------------------------------------ HTTP endpoints
#
# Modal 1.4 uses `@modal.fastapi_endpoint` (was `@modal.web_endpoint` in 0.x).
# These are exposed only when deployed; running `modal run` calls the function
# directly without standing up a webserver. n8n integration is intentionally
# deferred — the URLs printed by `modal deploy` are noted in
# obsidian-brain/knowledge/webhook_registry.md but not yet wired into
# any n8n nodes.


@app.function(image=r57_image, secrets=[r57_secret], timeout=60 * 30)
@modal.fastapi_endpoint(method="POST")
def generate_images_http(payload: dict) -> dict:
    """POST {record_ids: [...], dry_run: bool} → generate_images.remote(...)"""
    record_ids = payload.get("record_ids") if payload else None
    dry_run = bool(payload.get("dry_run", False)) if payload else False
    return generate_images.local(record_ids=record_ids, dry_run=dry_run)


@app.function(image=r57_image, secrets=[r57_secret], timeout=60 * 10)
@modal.fastapi_endpoint(method="POST")
def schedule_blotato_http(payload: dict) -> dict:
    """POST {record_ids: [...], dry_run: bool} → schedule_blotato.remote(...)"""
    record_ids = payload.get("record_ids") if payload else None
    dry_run = bool(payload.get("dry_run", False)) if payload else False
    return schedule_blotato.local(record_ids=record_ids, dry_run=dry_run)


# ------------------------------------------------------------- Local entry

@app.local_entrypoint()
def main(record_id: str | None = None, dry_run: bool = True):
    """Manual smoke-test entry point: `modal run modal_app.py`."""
    ids = [record_id] if record_id else None
    print(generate_images.remote(record_ids=ids, dry_run=dry_run))
