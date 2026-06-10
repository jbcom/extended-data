"""Tests for Meshy task-id API helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from extended_data.connectors.meshy import animate, image3d, retexture, rigging, text3d
from extended_data.connectors.meshy.models import (
    AnimationRequest,
    Image3DRequest,
    RetextureRequest,
    RiggingRequest,
    Text3DRequest,
)
from extended_data.containers import ExtendedDict, ExtendedString


def _task_response(task_id: str) -> MagicMock:
    response = MagicMock()
    response.json.return_value = {"result": task_id}
    return response


def _json_response(payload: dict[str, object]) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
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


def test_text3d_get_returns_extended_payload() -> None:
    payload = {
        "id": "text-task",
        "status": "SUCCEEDED",
        "progress": 100,
        "created_at": 1700000000,
        "model_urls": {"glb": "https://example.com/model.glb"},
    }
    with patch("extended_data.connectors.meshy.text3d.base.request", return_value=_json_response(payload)):
        result = text3d.get("text-task")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["id"], ExtendedString)
    assert isinstance(result["model_urls"], ExtendedDict)
    assert result["model_urls"]["glb"] == "https://example.com/model.glb"


def test_image3d_get_returns_extended_payload() -> None:
    payload = {
        "id": "image-task",
        "status": "SUCCEEDED",
        "progress": 100,
        "created_at": 1700000000,
        "model_urls": {"glb": "https://example.com/image.glb"},
    }
    with patch("extended_data.connectors.meshy.image3d.base.request", return_value=_json_response(payload)):
        result = image3d.get("image-task")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["model_urls"], ExtendedDict)
    assert result["model_urls"]["glb"] == "https://example.com/image.glb"


def test_animation_get_returns_extended_payload() -> None:
    payload = {
        "id": "animation-task",
        "status": "SUCCEEDED",
        "progress": 100,
        "created_at": 1700000000,
        "animation_glb_url": "https://example.com/animation.glb",
    }
    with patch("extended_data.connectors.meshy.animate.base.request", return_value=_json_response(payload)):
        result = animate.get("animation-task")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["animation_glb_url"], ExtendedString)
    assert result["animation_glb_url"] == "https://example.com/animation.glb"


def test_rigging_get_returns_extended_payload() -> None:
    payload = {
        "id": "rig-task",
        "status": "SUCCEEDED",
        "progress": 100,
        "created_at": 1700000000,
        "result": {"rigged_character_glb_url": "https://example.com/rig.glb"},
    }
    with patch("extended_data.connectors.meshy.rigging.base.request", return_value=_json_response(payload)):
        result = rigging.get("rig-task")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["result"], ExtendedDict)
    assert result["result"]["rigged_character_glb_url"] == "https://example.com/rig.glb"


def test_retexture_get_returns_extended_payload() -> None:
    payload = {
        "id": "retexture-task",
        "status": "SUCCEEDED",
        "progress": 100,
        "created_at": 1700000000,
        "model_urls": {"glb": "https://example.com/retexture.glb"},
    }
    with patch("extended_data.connectors.meshy.retexture.base.request", return_value=_json_response(payload)):
        result = retexture.get("retexture-task")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["model_urls"], ExtendedDict)
    assert result["model_urls"]["glb"] == "https://example.com/retexture.glb"


@pytest.mark.parametrize("module", [text3d, image3d, retexture, rigging, animate])
def test_meshy_poll_redacts_failed_task_errors(monkeypatch: pytest.MonkeyPatch, module: object) -> None:
    """All Meshy polling helpers should redact vendor task failure messages."""
    monkeypatch.setattr(
        module,
        "get",
        lambda task_id: {
            "id": task_id,
            "status": "FAILED",
            "task_error": {"message": "denied password=hunter2 Authorization: Bearer raw_token"},
            "error": "denied api_key=key_123",
        },
    )

    with pytest.raises(RuntimeError) as exc_info:
        module.poll("task-secret", interval=0, timeout=1)

    message = str(exc_info.value)
    assert "hunter2" not in message
    assert "raw_token" not in message
    assert "key_123" not in message
    assert "[REDACTED]" in message


def test_image3d_create_redacts_unexpected_response() -> None:
    """Image3D create diagnostics should not echo secret-bearing response payloads."""
    response = _json_response({"password": "hunter2", "authorization": "Bearer raw_token"})

    with patch("extended_data.connectors.meshy.image3d.base.request", return_value=response):
        with pytest.raises(RuntimeError) as exc_info:
            image3d.create(Image3DRequest(image_url="https://example.com/source.png"))

    message = str(exc_info.value)
    assert "hunter2" not in message
    assert "raw_token" not in message
    assert "[REDACTED]" in message
