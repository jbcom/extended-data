"""Animation API - apply animations to rigged models.

Usage:
    from extended_data.connectors.meshy import animate
    from extended_data.connectors.meshy.animations import ANIMATIONS

    result = animate.apply(rigged_task_id, animation_id=0)

    # Browse animations
    for anim in ANIMATIONS.values():
        print(f"{anim.id}: {anim.name}")
"""

from __future__ import annotations

import time

from extended_data.connectors.meshy import base
from extended_data.connectors.meshy.models import AnimationRequest, AnimationResult, TaskStatus
from extended_data.containers import extend_data


def create(request: AnimationRequest) -> str:
    """Create animation task. Returns task_id."""
    response = base.request(
        "POST",
        "animations",
        version="v1",
        json=request.model_dump(exclude_none=True),
    )
    return extend_data(response.json().get("result"))


def get(task_id: str) -> AnimationResult:
    """Get task status."""
    response = base.request("GET", f"animations/{task_id}", version="v1")
    return AnimationResult(**response.json())


def poll(task_id: str, interval: float = 5.0, timeout: float = 600.0) -> AnimationResult:
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
    rigged_task_id: str,
    animation_id: int,
    *,
    loop: bool = True,
    frame_rate: int = 30,
    wait: bool = True,
) -> AnimationResult | str:
    """Apply animation to a rigged model.

    Args:
        rigged_task_id: Task ID of rigged model
        animation_id: Animation ID (0-677, see animations.ANIMATIONS)
        loop: Whether animation loops
        frame_rate: Animation frame rate
        wait: Wait for completion (default True)

    Returns:
        AnimationResult if wait=True, task_id if wait=False
    """
    request = AnimationRequest(
        rig_task_id=rigged_task_id,
        action_id=animation_id,
        loop=loop,
        frame_rate=frame_rate,
    )

    task_id = create(request)

    if not wait:
        return task_id

    return poll(task_id)
