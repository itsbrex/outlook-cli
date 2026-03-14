"""Tests for pin command — pin_message, get_pin_status, model field."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from outlook_cli.client import OutlookClient
from outlook_cli.constants import PIN_PROPERTY_ID
from outlook_cli.models import Email


FAKE_MSG_ID = "AAMk_test_pin_message_id_long_enough_to_pass_resolve_check_1234567"


@pytest.fixture
def client():
    with patch.object(OutlookClient, "_load_id_map", return_value={}):
        c = OutlookClient("fake-token")
    return c


# ── pin_message ───────────────────────────────────────────


class TestPinMessage:
    def test_pin(self, client):
        with patch.object(client, "_patch", return_value={}) as mock_patch, \
             patch.object(client, "_save_id_map"):
            client.pin_message(FAKE_MSG_ID, pinned=True)

        payload = mock_patch.call_args[1]["json"]
        props = payload["SingleValueExtendedProperties"]
        assert len(props) == 1
        assert props[0]["PropertyId"] == PIN_PROPERTY_ID
        assert props[0]["Value"] == "true"

    def test_unpin(self, client):
        with patch.object(client, "_patch", return_value={}) as mock_patch, \
             patch.object(client, "_save_id_map"):
            client.pin_message(FAKE_MSG_ID, pinned=False)

        payload = mock_patch.call_args[1]["json"]
        assert payload["SingleValueExtendedProperties"][0]["Value"] == "false"

    def test_resolves_display_id(self, client):
        client._id_map["3"] = FAKE_MSG_ID
        with patch.object(client, "_patch", return_value={}) as mock_patch, \
             patch.object(client, "_save_id_map"):
            client.pin_message("3")

        path_arg = mock_patch.call_args[0][0]
        assert FAKE_MSG_ID in path_arg


# ── get_pin_status ────────────────────────────────────────


class TestGetPinStatus:
    def test_pinned_message(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "Id": FAKE_MSG_ID,
            "SingleValueExtendedProperties": [{
                "PropertyId": PIN_PROPERTY_ID,
                "Value": "true",
            }]
        }
        with patch("outlook_cli.client.httpx.get", return_value=mock_resp), \
             patch.object(client, "_save_id_map"):
            result = client.get_pin_status(FAKE_MSG_ID)

        assert result is True

    def test_not_pinned_message(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "Id": FAKE_MSG_ID,
            "SingleValueExtendedProperties": [{
                "PropertyId": PIN_PROPERTY_ID,
                "Value": "false",
            }]
        }
        with patch("outlook_cli.client.httpx.get", return_value=mock_resp), \
             patch.object(client, "_save_id_map"):
            result = client.get_pin_status(FAKE_MSG_ID)

        assert result is False

    def test_no_extended_properties(self, client):
        """Message without pin property should return False."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"Id": FAKE_MSG_ID}

        with patch("outlook_cli.client.httpx.get", return_value=mock_resp), \
             patch.object(client, "_save_id_map"):
            result = client.get_pin_status(FAKE_MSG_ID)

        assert result is False


# ── Email model is_pinned field ───────────────────────────


class TestEmailIsPinned:
    def test_default_not_pinned(self):
        data = {"Id": "AAMk_test"}
        email = Email.from_api(data)
        assert email.is_pinned is False

    def test_is_pinned_field_settable(self):
        data = {"Id": "AAMk_test"}
        email = Email.from_api(data)
        email.is_pinned = True
        assert email.is_pinned is True


# ── PIN_PROPERTY_ID constant ─────────────────────────────


class TestPinPropertyId:
    def test_property_id_format(self):
        assert "Boolean" in PIN_PROPERTY_ID
        assert "IsPinned" in PIN_PROPERTY_ID
        assert "{23239608-685D-4732-9C55-4C95CB4E8E33}" in PIN_PROPERTY_ID
