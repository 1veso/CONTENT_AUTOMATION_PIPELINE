"""
Fal storage upload module.
Uploads local files (reference product images, generated media) to fal.media
and returns the public CDN URL.
"""

import os
from pathlib import Path

import fal_client

from . import config
from .utils import print_status

# Make sure fal_client sees the credential.
if config.FAL_API_KEY and not os.environ.get("FAL_KEY"):
    os.environ["FAL_KEY"] = config.FAL_API_KEY


def upload_reference(file_path, api_key=None):
    """
    Upload a file to fal storage and return the public URL.

    Args:
        file_path: Path to the local file
        api_key: Optional API key override (defaults to config.FAL_API_KEY)

    Returns:
        str: The hosted v3.fal.media URL

    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If upload fails
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if api_key:
        os.environ["FAL_KEY"] = api_key
    elif not os.environ.get("FAL_KEY"):
        if not config.FAL_API_KEY:
            raise ValueError("FAL_API_KEY is required")
        os.environ["FAL_KEY"] = config.FAL_API_KEY

    print_status(f"Uploading to fal storage: {file_path.name}")

    url = fal_client.upload_file(str(file_path))
    if not url:
        raise Exception(f"fal upload returned empty URL for {file_path}")

    print_status(f"Upload successful: {url}", "OK")
    return url


def upload_references(file_paths, api_key=None):
    """Upload multiple files and return their hosted URLs."""
    return [upload_reference(p, api_key) for p in file_paths]
