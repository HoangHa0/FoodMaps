"""Tests of the Food Journey request/response models (no database needed)."""

from datetime import time

import pytest
from pydantic import ValidationError

from app.modules.journey import constants
from app.modules.journey.schemas import JourneyIn, PlaceOut, ShareIn, StopIn
from app.shared.places import PlaceRef


def stop(place_id: str = "gid_Q001", **kw) -> dict:
    return {"place_id": place_id, **kw}


def test_minimal_journey_is_valid():
    j = JourneyIn.model_validate({})
    assert (j.title, j.planned_date, j.stops) == (None, None, [])


def test_text_is_trimmed_and_blank_becomes_none():
    j = JourneyIn.model_validate({"title": "  Cuối tuần  ", "stops": [stop(note="   ")]})
    assert j.title == "Cuối tuần"
    assert j.stops[0].note is None
    assert JourneyIn.model_validate({"title": "   "}).title is None


def test_title_and_note_length_limits():
    JourneyIn.model_validate({"title": "x" * constants.TITLE_MAX_LENGTH})
    with pytest.raises(ValidationError):
        JourneyIn.model_validate({"title": "x" * (constants.TITLE_MAX_LENGTH + 1)})
    StopIn.model_validate(stop(note="x" * constants.NOTE_MAX_LENGTH))
    with pytest.raises(ValidationError):
        StopIn.model_validate(stop(note="x" * (constants.NOTE_MAX_LENGTH + 1)))


def test_stop_count_limit():
    JourneyIn.model_validate({"stops": [stop()] * constants.MAX_STOPS_PER_JOURNEY})
    with pytest.raises(ValidationError):
        JourneyIn.model_validate({"stops": [stop()] * (constants.MAX_STOPS_PER_JOURNEY + 1)})


def test_same_place_twice_is_allowed():
    assert len(JourneyIn.model_validate({"stops": [stop("a"), stop("a")]}).stops) == 2


def test_place_id_is_required():
    with pytest.raises(ValidationError):
        StopIn.model_validate({"place_id": ""})
    with pytest.raises(ValidationError):
        StopIn.model_validate({})


def test_time_keeps_hours_and_minutes_only():
    assert StopIn.model_validate(stop(planned_time="08:30:45")).planned_time == time(8, 30)
    assert StopIn.model_validate(stop(planned_time="08:30")).planned_time == time(8, 30)


@pytest.mark.parametrize("bad", ["25:00", "abc", "08:30+07:00"])
def test_bad_times_are_rejected(bad):
    with pytest.raises(ValidationError):
        StopIn.model_validate(stop(planned_time=bad))


def test_a_share_needs_at_least_one_stop():
    with pytest.raises(ValidationError):
        ShareIn.model_validate({"stops": []})
    assert len(ShareIn.model_validate({"stops": [stop()]}).stops) == 1


def test_share_has_the_same_stop_limit():
    with pytest.raises(ValidationError):
        ShareIn.model_validate({"stops": [stop()] * (constants.MAX_STOPS_PER_JOURNEY + 1)})


def test_extra_fields_are_ignored():
    j = JourneyIn.model_validate({"title": "x", "id": "whatever", "stops": [stop(id="s1")]})
    assert not hasattr(j, "id") and not hasattr(j.stops[0], "id")


def test_place_out_is_built_from_a_place_ref():
    ref = PlaceRef(
        place_id="gid_Q001",
        place_code="Q001",
        name="Tiny Cafe - Revolution",
        category="Cà phê & Trà",
        lat=20.98,
        lng=105.84,
        tiktok_urls=["https://www.tiktok.com/a"],
    )
    out = PlaceOut.model_validate(ref)
    assert (out.place_id, out.name, out.lat) == ("gid_Q001", "Tiny Cafe - Revolution", 20.98)
    assert "tiktok_urls" not in out.model_dump()