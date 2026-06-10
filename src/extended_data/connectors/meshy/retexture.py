"""Retexture API - apply new textures to models.

Usage:
    from extended_data.connectors.meshy import retexture

    result = retexture.apply(model_task_id, "golden with gems")
"""

from __future__ import annotations

import time

from extended_data.connectors.meshy import base
from extended_data.connectors.meshy.models import RetextureRequest, RetextureResult, TaskStatus


def create(request: RetextureRequest) -> str:
    """Create retexture task. Returns task_id."""
    response = base.request(
        "POST",
        "retexture",
        version="v1",
        json=request.model_dump(exclude_none=True),
    )
    return response.json().get("result")


def get(task_id: str) -> RetextureResult:
    """Get task status."""
    response = base.request("GET", f"retexture/{task_id}", version="v1")
    return RetextureResult(**response.json())


def poll(task_id: str, interval: float = 5.0, timeout: float = 600.0) -> RetextureResult:
    """Poll until complete or failed."""
    start = time.time()
    while True:
        result = get(task_id)
        if result.status == TaskStatus.SUCCEEDED:
            return result
        if result.status == TaskStatus.FAILED:
            error = getattr(result, "task_error", {})
            msg = error.get("message", "Unknown error") if isinstance(error, dict) else str(error)
            msg = f"Task failed: {msg}"
            raise RuntimeError(msg)
        if result.status == TaskStatus.EXPIRED:
            msg = "Task expired"
            raise RuntimeError(msg)
        if time.time() - start > timeout:
            msg = f"Task timed out after {timeout}s"
            raise TimeoutError(msg)
        time.sleep(interval)


def apply(
    model_task_id: str,
    prompt: str,
    *,
    enable_original_uv: bool = True,
    enable_pbr: bool = True,
    wait: bool = True,
) -> RetextureResult | str:
    """Apply new textures to a model.

    Args:
        model_task_id: Task ID of model to retexture
        prompt: Text description of new texture
        enable_original_uv: Keep original UV mapping
        enable_pbr: Generate PBR maps
        wait: Wait for completion (default True)

    Returns:
        RetextureResult if wait=True, task_id if wait=False
    """
    request = RetextureRequest(
        input_task_id=model_task_id,
        text_style_prompt=prompt,
        enable_original_uv=enable_original_uv,
        enable_pbr=enable_pbr,
    )

    task_id = create(request)

    if not wait:
        return task_id

    return poll(task_id)


def apply_from_image(
    model_task_id: str,
    style_image_url: str,
    *,
    enable_original_uv: bool = True,
    enable_pbr: bool = True,
    wait: bool = True,
) -> RetextureResult | str:
    """Apply textures based on reference image.

    Args:
        model_task_id: Task ID of model
        style_image_url: URL to style reference image
        enable_original_uv: Keep original UV mapping
        enable_pbr: Generate PBR maps
        wait: Wait for completion (default True)

    Returns:
        RetextureResult if wait=True, task_id if wait=False
    """
    request = RetextureRequest(
        input_task_id=model_task_id,
        image_style_url=style_image_url,
        enable_original_uv=enable_original_uv,
        enable_pbr=enable_pbr,
    )

    task_id = create(request)

    if not wait:
        return task_id

    return poll(task_id)
