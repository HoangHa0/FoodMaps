"""Tests of the pure rules of the Food Journey module (no database needed)."""

import json
import re
from datetime import UTC, date, datetime, time, timedelta

import pytest

from app.modules.journey import constants, rules
from app.modules.journey.rules import StopData

NOW = datetime(2026, 11, 8, 9, 0, tzinfo=UTC)


# --- clean_text ------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, None), ("", None), ("   ", None), ("\n\t", None), ("  hi  ", "hi"), ("a  b", "a  b")],
)
def test_clean_text(raw, expected):
    assert rules.clean_text(raw) == expected


# --- limits ----------------------------------------------------------------------------------
def test_journey_limit_boundaries():
    assert not rules.journey_limit_reached(0)
    assert not rules.journey_limit_reached(constants.MAX_JOURNEYS_PER_USER - 1)
    assert rules.journey_limit_reached(constants.MAX_JOURNEYS_PER_USER)
    assert rules.journey_limit_reached(constants.MAX_JOURNEYS_PER_USER + 1)


def test_share_limit_boundaries():
    assert not rules.share_limit_reached(constants.SHARES_PER_IP_PER_HOUR - 1)
    assert rules.share_limit_reached(constants.SHARES_PER_IP_PER_HOUR)


def test_share_window_is_one_hour_back():
    assert rules.share_window_start(NOW) == NOW - timedelta(hours=1)


# --- share links -----------------------------------------------------------------------------
def test_share_code_is_url_safe_and_fits_the_column():
    code = rules.new_share_code()
    assert re.fullmatch(r"[A-Za-z0-9_-]+", code)
    assert len(code) <= constants.CODE_COLUMN_LENGTH


def test_share_codes_do_not_repeat():
    assert len({rules.new_share_code() for _ in range(2000)}) == 2000


def test_share_expires_after_the_configured_number_of_days():
    assert rules.share_expires_at(NOW) == NOW + timedelta(days=constants.SHARE_LIFETIME_DAYS)


def test_expiry_boundary():
    expires = rules.share_expires_at(NOW)
    assert not rules.is_expired(expires, expires - timedelta(seconds=1))
    assert rules.is_expired(expires, expires)
    assert rules.is_expired(expires, expires + timedelta(seconds=1))


def test_ip_hash_is_stable_keyed_and_hides_the_address():
    h = rules.hash_client_ip("203.0.113.7", "secret-a")
    assert h == rules.hash_client_ip("203.0.113.7", "secret-a")
    assert re.fullmatch(r"[0-9a-f]{64}", h)
    assert "203" not in h
    assert h != rules.hash_client_ip("203.0.113.8", "secret-a")
    assert h != rules.hash_client_ip("203.0.113.7", "secret-b")


# --- snapshot --------------------------------------------------------------------------------
STOPS = [
    StopData("gid_Q001", time(8, 30), "đặt bàn trước"),
    StopData("gid_Q002", None, None),
    StopData("gid_Q001", time(21, 0), None),  # the same place twice is allowed
]


def test_snapshot_round_trip_keeps_order_and_values():
    data = rules.make_snapshot("Cuối tuần", date(2026, 11, 14), STOPS)
    back = rules.read_snapshot(data)
    assert back.title == "Cuối tuần"
    assert back.planned_date == date(2026, 11, 14)
    assert back.stops == STOPS


def test_snapshot_survives_json_storage():
    data = rules.make_snapshot("x", date(2026, 11, 14), STOPS)
    assert rules.read_snapshot(json.loads(json.dumps(data))).stops == STOPS


def test_snapshot_with_nothing_optional():
    data = rules.make_snapshot(None, None, [StopData("gid_Q001")])
    assert data == {
        "title": None,
        "planned_date": None,
        "stops": [{"place_id": "gid_Q001", "planned_time": None, "note": None}],
    }
    assert rules.read_snapshot(data).planned_date is None


def test_snapshot_times_are_written_as_hours_and_minutes():
    data = rules.make_snapshot(None, None, [StopData("p", time(7, 5, 59))])
    assert data["stops"][0]["planned_time"] == "07:05"


def test_empty_snapshot_has_no_stops():
    assert rules.read_snapshot({}).stops == []
