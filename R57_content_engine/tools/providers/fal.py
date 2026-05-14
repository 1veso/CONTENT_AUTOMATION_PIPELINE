"""
Fal.ai provider — image generation (Nano Banana / Pro) and video generation
(Kling, Sora 2 Pro) via the fal_client SDK.

All generation is ASYNCHRONOUS (submit returns a request_id; poll blocks
on handler.get()). Handlers are cached so polling can be deferred and
parallelized.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import fal_client

from .. import config
from ..utils import print_status

# Ensure fal_client sees the key under its expected env var name.
# Users put FAL_API_KEY in .env; fal_client reads FAL_KEY.
if config.FAL_API_KEY and not os.environ.get("FAL_KEY"):
    os.environ["FAL_KEY"] = config.FAL_API_KEY

# Provider sync flags — Fal is async (queue-backed)
image_IS_SYNC = False
video_IS_SYNC = False

# --- Fal endpoint IDs ---
# Nano Banana (Gemini 2.5 Flash Image) hosted on Fal.
# Use the /edit variant when reference images are provided.
_IMAGE_ENDPOINT = "fal-ai/nano-banana"
_IMAGE_EDIT_ENDPOINT = "fal-ai/nano-banana/edit"

_VIDEO_ENDPOINTS = {
    # Closest stable Fal equivalent for "Kling 3.0".
    "kling-3.0": "fal-ai/kling-video/v2.1/master/image-to-video",
    "sora-2-pro": "fal-ai/sora-2/image-to-video/pro",
}

# Cache of submitted handlers, keyed by request_id, so poll_* can re-find them.
_handlers = {}


def _normalize_aspect_ratio(ar, valid):
    """Snap an aspect ratio string to the nearest one the endpoint accepts."""
    if ar in valid:
        return ar
    # Common fallbacks
    if ar in ("portrait",):
        return "9:16" if "9:16" in valid else valid[0]
    if ar in ("landscape",):
        return "16:9" if "16:9" in valid else valid[0]
    return valid[0]


# ---------------------------------------------------------------------------
# Image Generation
# ---------------------------------------------------------------------------

def submit_image(prompt, reference_urls=None, aspect_ratio="9:16",
                 resolution="1K", model="nano-banana-pro", **kwargs):
    """
    Submit an image generation task to Fal.

    Args:
        prompt: Image generation prompt
        reference_urls: List of hosted reference image URLs (uploaded to fal storage)
        aspect_ratio: Aspect ratio string ("9:16", "16:9", "1:1", etc.)
        resolution: "1K", "2K", or "4K" (passed through; not all endpoints honor it)
        model: Internal model name (kept for API compatibility; Fal uses one nano-banana)

    Returns:
        str: request_id for polling
    """
    if reference_urls:
        endpoint = _IMAGE_EDIT_ENDPOINT
        arguments = {
            "prompt": prompt,
            "image_urls": reference_urls,
            "aspect_ratio": aspect_ratio,
            "num_images": 1,
            "output_format": "png",
        }
    else:
        endpoint = _IMAGE_ENDPOINT
        arguments = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "num_images": 1,
            "output_format": "png",
        }

    handler = fal_client.submit(endpoint, arguments=arguments)
    _handlers[handler.request_id] = (handler, endpoint)
    return handler.request_id


def poll_image(task_id, max_wait=300, poll_interval=5, quiet=False):
    """Block until a Fal image task completes. Returns GenerationResult dict."""
    return _block_and_extract(task_id, kind="image", quiet=quiet)


# ---------------------------------------------------------------------------
# Video Generation
# ---------------------------------------------------------------------------

def submit_video(prompt, image_url=None, model="sora-2-pro",
                 duration="5", mode="pro", aspect_ratio="9:16", **kwargs):
    """
    Submit a video generation task to Fal.

    Args:
        prompt: Video prompt text
        image_url: Source image URL (start frame). Required for these endpoints.
        model: "kling-3.0" or "sora-2-pro"
        duration: Video duration in seconds (Kling: "5"/"10", Sora: 4/8/12/16/20)
        mode: kept for compatibility (Fal Kling master implies pro quality)
        aspect_ratio: Aspect ratio string

    Returns:
        str: request_id for polling
    """
    endpoint = _VIDEO_ENDPOINTS.get(model)
    if not endpoint:
        raise ValueError(f"Fal doesn't support video model: '{model}'. "
                         f"Available: {list(_VIDEO_ENDPOINTS.keys())}")
    if not image_url:
        raise ValueError(f"Fal '{model}' is image-to-video and requires image_url")

    if model == "kling-3.0":
        kling_duration = "10" if str(duration) in ("10", "15") else "5"
        arguments = {
            "prompt": prompt,
            "image_url": image_url,
            "duration": kling_duration,
            "aspect_ratio": _normalize_aspect_ratio(aspect_ratio, ["16:9", "9:16", "1:1"]),
            "negative_prompt": "blur, distort, and low quality",
            "cfg_scale": 0.5,
        }

    elif model == "sora-2-pro":
        sora_valid = [4, 8, 12, 16, 20]
        try:
            dur_int = int(duration)
        except (TypeError, ValueError):
            dur_int = 8
        sora_duration = min(sora_valid, key=lambda v: abs(v - dur_int))
        arguments = {
            "prompt": prompt,
            "image_url": image_url,
            "duration": sora_duration,
            "aspect_ratio": _normalize_aspect_ratio(aspect_ratio, ["auto", "9:16", "16:9"]),
            "resolution": "auto",
        }
    else:
        raise ValueError(f"No payload builder for model: {model}")

    handler = fal_client.submit(endpoint, arguments=arguments)
    _handlers[handler.request_id] = (handler, endpoint)
    return handler.request_id


def poll_video(task_id, max_wait=600, poll_interval=10, quiet=False):
    """Block until a Fal video task completes. Returns GenerationResult dict."""
    return _block_and_extract(task_id, kind="video", quiet=quiet)


# ---------------------------------------------------------------------------
# Polling helpers
# ---------------------------------------------------------------------------

def _block_and_extract(task_id, kind, quiet=False):
    """
    Block on a cached fal handler and pull a hosted URL out of the result.
    fal_client handler.get() blocks until the queued task completes.
    """
    entry = _handlers.get(task_id)
    if not entry:
        raise Exception(f"No cached fal handler for request_id: {task_id}")
    handler, endpoint = entry

    if not quiet:
        print_status(f"Waiting on fal {kind} task {task_id[:12]}...", "..")

    result = handler.get()

    url = _extract_url(result, kind)
    if not url:
        raise Exception(f"No result URL in fal response: {result}")

    if not quiet:
        print_status("Task completed successfully!", "OK")

    # Free the cached handler — single-use.
    _handlers.pop(task_id, None)

    return {
        "status": "success",
        "task_id": task_id,
        "result_url": url,
    }


def _extract_url(result, kind):
    """Pull the primary asset URL from a fal result payload."""
    if not isinstance(result, dict):
        return None
    if kind == "image":
        images = result.get("images") or []
        if images and isinstance(images[0], dict):
            return images[0].get("url")
    elif kind == "video":
        video = result.get("video")
        if isinstance(video, dict):
            return video.get("url")
    return None


def poll_tasks_parallel(task_ids, max_wait=300, poll_interval=5):
    """Poll multiple Fal tasks concurrently. Returns dict task_id → result."""
    if not task_ids:
        return {}

    total = len(task_ids)
    completed = []
    results = {}

    # Decide kind per task by sniffing the endpoint cached at submit time.
    def _kind_for(tid):
        entry = _handlers.get(tid)
        if not entry:
            return "image"
        _, endpoint = entry
        return "video" if "video" in endpoint or "sora" in endpoint else "image"

    def _poll_one(tid):
        result = _block_and_extract(tid, kind=_kind_for(tid), quiet=True)
        completed.append(tid)
        print_status(f"Task {tid[:12]}... done ({len(completed)}/{total})", "OK")
        return result

    max_workers = min(total, 20)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_poll_one, tid): tid for tid in task_ids}
        for future in as_completed(futures):
            tid = futures[future]
            try:
                results[tid] = future.result()
            except Exception as e:
                completed.append(tid)
                print_status(f"Task {tid[:12]}... failed: {e}", "XX")
                results[tid] = {"status": "error", "task_id": tid, "error": str(e)}

    return results
