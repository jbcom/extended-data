"""Tests for Meshy task-id API helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from extended_data.connectors.meshy import animate, image3d, retexture, rigging, text3d
from extended_data.connectors.meshy.models import (
    AnimationRequest,
    Image3DRequest,
    RetextureRequest,
    RiggingRequest,
    Text3DRequest,
)
from extended_data.containers import ExtendedString


def _task_response(task_id: str) -> MagicMock:
    response = MagicMock()
    response.json.return_value = {"result": task_id}
    return response


def test_text3d_task_ids_are_extended_strings() -> None:
    with patch("extended_data.connectors.meshy.text3d.base.request", return_value=_task_response("text-task")):
        created = text3d.create(Text3DRequest(prompt="a sword"))
        refined = text3d.refine("text-task")

    assert isinstance(created, ExtendedString)
    assert isinstance(refined, ExtendedString)
    assert created == "text-task"
    assert refined == "text-task"


def test_image3d_task_ids_are_extended_strings() -> None:
    with patch("extended_data.connectors.meshy.image3d.base.request", return_value=_task_response("image-task")):
        created = image3d.create(Image3DRequest(image_url="https://example.com/source.png"))
        refined = image3d.refine("image-task")

    assert isinstance(created, ExtendedString)
    assert isinstance(refined, ExtendedString)
    assert created == "image-task"
    assert refined == "image-task"


def test_animation_task_id_is_extended_string() -> None:
    request = AnimationRequest(rig_task_id="rig-task", action_id=42)

    with patch("extended_data.connectors.meshy.animate.base.request", return_value=_task_response("animation-task")):
        created = animate.create(request)

    assert isinstance(created, ExtendedString)
    assert created == "animation-task"


def test_rigging_task_id_is_extended_string() -> None:
    request = RiggingRequest(input_task_id="model-task")

    with patch("extended_data.connectors.meshy.rigging.base.request", return_value=_task_response("rig-task")):
        created = rigging.create(request)

    assert isinstance(created, ExtendedString)
    assert created == "rig-task"


def test_retexture_task_id_is_extended_string() -> None:
    request = RetextureRequest(input_task_id="model-task", text_style_prompt="gold")

    with patch("extended_data.connectors.meshy.retexture.base.request", return_value=_task_response("retexture-task")):
        created = retexture.create(request)

    assert isinstance(created, ExtendedString)
    assert created == "retexture-task"
