"""Runpod Serverless queue worker for Loyal Bear image processing."""

from __future__ import annotations

import base64
import binascii
import io
import os
from typing import Any

from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 16 * 1024 * 1024
MAX_IMAGE_PIXELS = 36_000_000
MODEL_PATH = os.environ.get(
    "LOYALBEAR_MODEL_PATH", "/runpod-volume/models/epicrealismXL_pureFix.safetensors"
)
STRENGTHS = {"Light": 0.05, "Strong": 0.1}

_pipe = None


def _decode_image(value: Any) -> Image.Image:
    if not isinstance(value, str) or not value:
        raise ValueError("input.image_base64 must be a nonempty base64 string")
    if value.startswith("data:"):
        header, separator, value = value.partition(",")
        if not separator or not header.endswith(";base64"):
            raise ValueError("image_base64 data URL must be base64 encoded")
    if len(value) > ((MAX_IMAGE_BYTES + 2) // 3) * 4:
        raise ValueError("image_base64 exceeds the 16 MiB image limit")
    try:
        data = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("image_base64 is not valid base64") from exc
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("image_base64 must contain an image of at most 16 MiB")
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.format not in {"PNG", "JPEG", "WEBP"}:
                raise ValueError("image_base64 must contain a PNG, JPEG, or WebP image")
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise ValueError("image exceeds the 36 megapixel limit")
            source.load()
            return source.copy()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("image_base64 does not contain a readable image") from exc


def _get_pipeline():
    global _pipe
    if _pipe is None:
        from src.pipeline import load_pipeline

        _pipe = load_pipeline(MODEL_PATH, device="cuda")
    return _pipe


def handler(job: dict[str, Any]) -> dict[str, Any]:
    request = job.get("input")
    if not isinstance(request, dict):
        raise ValueError("job.input must be an object")
    prompt = request.get("prompt", "")
    if not isinstance(prompt, str) or len(prompt) > 1000:
        raise ValueError("input.prompt must be a string of at most 1000 characters")
    strength = request.get("strength", "Light")
    if not isinstance(strength, str) or strength not in STRENGTHS:
        raise ValueError("input.strength must be Light or Strong")
    image = _decode_image(request.get("image_base64"))

    from src.metadata import strip_metadata
    from src.pipeline import run_img2img

    result = run_img2img(
        _get_pipeline(), image=image, prompt=prompt, denoise=STRENGTHS[strength],
        steps=5, cfg=6.6, seed=-1,
    )
    result = strip_metadata(result)
    output = io.BytesIO()
    result.save(output, format="PNG")
    processed = output.getvalue()
    if len(processed) > MAX_IMAGE_BYTES:
        raise RuntimeError("output exceeds the 16 MiB image limit")
    return {
        "image_base64": base64.b64encode(processed).decode("ascii"),
        "mime_type": "image/png",
        "strength": strength,
    }


if __name__ == "__main__":
    import runpod

    runpod.serverless.start({"handler": handler})
