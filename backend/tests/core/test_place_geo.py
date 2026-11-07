"""Pure tests for the distance helpers of `app.shared.places` (no database needed)."""

import math

import pytest

from app.shared.places import bounding_box, haversine_m

# Q001 (Tiny Cafe - Revolution) and a point about 4.6 km away from it
LAT, LNG = 20.9893215, 105.8406215
FAR_LAT, FAR_LNG = 21.0285, 105.8542


def test_distance_to_itself_is_zero():
    assert haversine_m(LAT, LNG, LAT, LNG) == 0


def test_distance_is_symmetric():
    assert haversine_m(LAT, LNG, FAR_LAT, FAR_LNG) == pytest.approx(haversine_m(FAR_LAT, FAR_LNG, LAT, LNG))


def test_known_distance():
    assert haversine_m(LAT, LNG, FAR_LAT, FAR_LNG) == pytest.approx(4579, abs=2)


def test_one_degree_of_latitude():
    assert haversine_m(0, 0, 1, 0) == pytest.approx(111_195, abs=1)


def test_box_is_centred_and_covers_twice_the_radius_north_south():
    lat_lo, lat_hi, lng_lo, lng_hi = bounding_box(LAT, LNG, 500)
    assert (lat_lo + lat_hi) / 2 == pytest.approx(LAT)
    assert (lng_lo + lng_hi) / 2 == pytest.approx(LNG)
    assert haversine_m(lat_lo, LNG, lat_hi, LNG) == pytest.approx(1000, abs=0.5)


def test_box_is_wider_in_longitude_than_in_latitude():
    lat_lo, lat_hi, lng_lo, lng_hi = bounding_box(LAT, LNG, 500)
    assert lng_hi - lng_lo == pytest.approx((lat_hi - lat_lo) / math.cos(math.radians(LAT)))


def test_box_does_not_divide_by_zero_at_the_pole():
    lat_lo, lat_hi, _, _ = bounding_box(90, 0, 100)
    assert lat_lo < lat_hi


@pytest.mark.parametrize("radius", [200, 500, 2000])
def test_every_point_inside_the_circle_is_inside_the_box(radius):
    """The box may only be too big, never too small, otherwise a place could be missed."""
    lat_lo, lat_hi, lng_lo, lng_hi = bounding_box(LAT, LNG, radius)
    step = 0.00025
    for i in range(-40, 41):
        for j in range(-40, 41):
            lat, lng = LAT + i * step, LNG + j * step
            if haversine_m(LAT, LNG, lat, lng) <= radius:
                assert lat_lo <= lat <= lat_hi and lng_lo <= lng <= lng_hi, (lat, lng)
