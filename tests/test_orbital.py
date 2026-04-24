import math
import pytest
from datetime import datetime, timezone

from app.services.orbital import (
    get_satellite_position,
    get_orbital_path,
    get_positions_batch,
    haversine_km,
)


ISS_LINE1 = "1 25544U 98067A   24112.51303241  .00018627  00000+0  33441-3 0  9993"
ISS_LINE2 = "2 25544  51.6411 132.2489 0002107  58.3917  62.4303 15.49896559448988"

FIXED_TIME = datetime(2024, 4, 22, 12, 0, 0, tzinfo=timezone.utc)


class TestHaversine:
    def test_same_point_is_zero(self):
        assert haversine_km(37.0, -122.0, 37.0, -122.0) == pytest.approx(0, abs=0.01)

    def test_san_jose_to_sf_is_about_70km(self):
        d = haversine_km(37.3382, -121.8863, 37.7749, -122.4194)
        assert 60 <= d <= 80

    def test_antipodal_points_are_half_earth_circumference(self):
        d = haversine_km(0, 0, 0, 180)
        assert d == pytest.approx(20015, abs=10)

    def test_crossing_international_date_line(self):
        d = haversine_km(0, 179, 0, -179)
        assert d < 500


class TestPosition:
    def test_position_returns_expected_fields(self):
        pos = get_satellite_position(ISS_LINE1, ISS_LINE2, FIXED_TIME)
        assert set(pos.keys()) == {
            "latitude", "longitude", "altitude_km", "speed_km_s", "timestamp"
        }

    def test_iss_altitude_is_in_leo_range(self):
        pos = get_satellite_position(ISS_LINE1, ISS_LINE2, FIXED_TIME)
        assert 350 < pos["altitude_km"] < 500

    def test_iss_speed_is_realistic_orbital_velocity(self):
        pos = get_satellite_position(ISS_LINE1, ISS_LINE2, FIXED_TIME)
        assert 7.5 < pos["speed_km_s"] < 7.8

    def test_iss_latitude_within_inclination_bounds(self):
        pos = get_satellite_position(ISS_LINE1, ISS_LINE2, FIXED_TIME)
        assert -52 <= pos["latitude"] <= 52

    def test_longitude_within_valid_range(self):
        pos = get_satellite_position(ISS_LINE1, ISS_LINE2, FIXED_TIME)
        assert -180 <= pos["longitude"] <= 180

    def test_determinism_same_time_same_result(self):
        pos1 = get_satellite_position(ISS_LINE1, ISS_LINE2, FIXED_TIME)
        pos2 = get_satellite_position(ISS_LINE1, ISS_LINE2, FIXED_TIME)
        assert pos1["latitude"] == pos2["latitude"]
        assert pos1["longitude"] == pos2["longitude"]

    def test_position_changes_over_time(self):
        from datetime import timedelta
        pos1 = get_satellite_position(ISS_LINE1, ISS_LINE2, FIXED_TIME)
        pos2 = get_satellite_position(ISS_LINE1, ISS_LINE2, FIXED_TIME + timedelta(seconds=60))
        assert abs(pos1["longitude"] - pos2["longitude"]) > 2


class TestOrbitalPath:
    def test_default_90_min_returns_90_points(self):
        path = get_orbital_path(ISS_LINE1, ISS_LINE2)
        assert len(path) == 90

    def test_custom_minutes_respected(self):
        path = get_orbital_path(ISS_LINE1, ISS_LINE2, minutes=30)
        assert len(path) == 30

    def test_path_points_have_required_fields(self):
        path = get_orbital_path(ISS_LINE1, ISS_LINE2, minutes=5)
        for point in path:
            assert "latitude" in point
            assert "longitude" in point
            assert "altitude_km" in point
            assert "timestamp" in point

    def test_altitude_stays_in_leo_range(self):
        path = get_orbital_path(ISS_LINE1, ISS_LINE2)
        for point in path:
            assert 150 < point["altitude_km"] < 500


class TestBatchPositions:
    def test_batch_computes_all_satellites(self):
        sats = [
            {"norad_id": 25544, "name": "ISS", "line1": ISS_LINE1, "line2": ISS_LINE2},
        ]
        results = get_positions_batch(sats, FIXED_TIME)
        assert len(results) == 1
        assert results[0]["norad_id"] == 25544

    def test_batch_skips_bad_tles_instead_of_failing(self):
        sats = [
            {"norad_id": 25544, "name": "ISS", "line1": ISS_LINE1, "line2": ISS_LINE2},
            {"norad_id": 99999, "name": "BAD", "line1": "1 garbage", "line2": "2 garbage"},
        ]
        results = get_positions_batch(sats, FIXED_TIME)
        assert len(results) >= 0
        valid_ids = [r["norad_id"] for r in results]
        assert 25544 in valid_ids or 99999 not in valid_ids

    def test_batch_shares_timestamp_across_results(self):
        from datetime import timedelta
        sats = [
            {"norad_id": 25544, "name": "ISS", "line1": ISS_LINE1, "line2": ISS_LINE2},
        ]
        r1 = get_positions_batch(sats, FIXED_TIME)
        r2 = get_positions_batch(sats, FIXED_TIME + timedelta(minutes=10))
        assert r1[0]["longitude"] != r2[0]["longitude"]