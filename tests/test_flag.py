"""Tests for flag command — set_flag client method, date parsing, model parsing."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from outlook_cli.client import OutlookClient
from outlook_cli.commands.manage import _parse_due_date
from outlook_cli.models import Email


# ── Fixtures ──────────────────────────────────────────────

FAKE_MSG_ID = "AAMk_test_flag_message_id_long_enough_to_pass_resolve_check_12345"


@pytest.fixture
def client():
    with patch.object(OutlookClient, "_load_id_map", return_value={}):
        c = OutlookClient("fake-token")
    return c


# ── Email.from_api flag parsing ───────────────────────────


class TestEmailFlagParsing:
    def test_not_flagged_default(self):
        data = {"Id": "AAMk_noflag"}
        email = Email.from_api(data)
        assert email.flag_status == "notFlagged"
        assert email.flag_due is None

    def test_flagged_status(self):
        data = {
            "Id": "AAMk_flagged",
            "Flag": {"FlagStatus": "flagged"},
        }
        email = Email.from_api(data)
        assert email.flag_status == "flagged"
        assert email.flag_due is None

    def test_flagged_with_due_date(self):
        data = {
            "Id": "AAMk_due",
            "Flag": {
                "FlagStatus": "flagged",
                "DueDateTime": {
                    "DateTime": "2026-03-20T23:59:59",
                    "TimeZone": "UTC",
                },
            },
        }
        email = Email.from_api(data)
        assert email.flag_status == "flagged"
        assert email.flag_due is not None
        assert email.flag_due.year == 2026
        assert email.flag_due.month == 3
        assert email.flag_due.day == 20

    def test_complete_status(self):
        data = {
            "Id": "AAMk_complete",
            "Flag": {"FlagStatus": "complete"},
        }
        email = Email.from_api(data)
        assert email.flag_status == "complete"

    def test_empty_flag_object(self):
        data = {"Id": "AAMk_empty", "Flag": {}}
        email = Email.from_api(data)
        assert email.flag_status == "notFlagged"

    def test_null_flag(self):
        data = {"Id": "AAMk_null", "Flag": None}
        email = Email.from_api(data)
        assert email.flag_status == "notFlagged"


# ── set_flag client method ────────────────────────────────


class TestSetFlag:
    def test_flag_message(self, client):
        with patch.object(client, "_patch", return_value={}) as mock_patch, \
             patch.object(client, "_save_id_map"):
            client.set_flag(FAKE_MSG_ID, status="flagged")

        payload = mock_patch.call_args[1]["json"]
        assert payload["Flag"]["FlagStatus"] == "flagged"

    def test_flag_with_due_date(self, client):
        with patch.object(client, "_patch", return_value={}) as mock_patch, \
             patch.object(client, "_save_id_map"):
            client.set_flag(FAKE_MSG_ID, status="flagged", due_date="2026-03-20")

        payload = mock_patch.call_args[1]["json"]
        assert payload["Flag"]["FlagStatus"] == "flagged"
        assert payload["Flag"]["DueDateTime"]["DateTime"] == "2026-03-20T23:59:59"
        assert payload["Flag"]["StartDateTime"]["DateTime"] == "2026-03-20T00:00:00"

    def test_complete_flag(self, client):
        with patch.object(client, "_patch", return_value={}) as mock_patch, \
             patch.object(client, "_save_id_map"):
            client.set_flag(FAKE_MSG_ID, status="complete")

        payload = mock_patch.call_args[1]["json"]
        assert payload["Flag"]["FlagStatus"] == "complete"

    def test_clear_flag(self, client):
        with patch.object(client, "_patch", return_value={}) as mock_patch, \
             patch.object(client, "_save_id_map"):
            client.set_flag(FAKE_MSG_ID, status="notFlagged")

        payload = mock_patch.call_args[1]["json"]
        assert payload["Flag"]["FlagStatus"] == "notFlagged"

    def test_due_date_ignored_when_not_flagged(self, client):
        """Due date should only be set when status is 'flagged'."""
        with patch.object(client, "_patch", return_value={}) as mock_patch, \
             patch.object(client, "_save_id_map"):
            client.set_flag(FAKE_MSG_ID, status="complete", due_date="2026-03-20")

        payload = mock_patch.call_args[1]["json"]
        assert "DueDateTime" not in payload["Flag"]

    def test_resolves_display_id(self, client):
        client._id_map["7"] = FAKE_MSG_ID
        with patch.object(client, "_patch", return_value={}) as mock_patch, \
             patch.object(client, "_save_id_map"):
            client.set_flag("7", status="flagged")

        path_arg = mock_patch.call_args[0][0]
        assert FAKE_MSG_ID in path_arg


# ── _parse_due_date ───────────────────────────────────────


class TestParseDueDate:
    def test_today(self):
        result = _parse_due_date("today")
        assert result == datetime.now().date().isoformat()

    def test_tomorrow(self):
        result = _parse_due_date("tomorrow")
        expected = (datetime.now().date() + timedelta(days=1)).isoformat()
        assert result == expected

    def test_relative_days(self):
        result = _parse_due_date("+3d")
        expected = (datetime.now().date() + timedelta(days=3)).isoformat()
        assert result == expected

    def test_iso_date(self):
        result = _parse_due_date("2026-03-20")
        assert result == "2026-03-20"

    def test_invalid_date_raises(self):
        with pytest.raises(Exception):
            _parse_due_date("not-a-date")

    def test_case_insensitive(self):
        result = _parse_due_date("TODAY")
        assert result == datetime.now().date().isoformat()
