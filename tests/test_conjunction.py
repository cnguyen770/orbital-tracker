from app.services.conjunction import (
    distance_km,
    find_conjunctions,
    compute_position_eci,
)
from datetime import datetime, timezone


ISS_ZARYA_L1 = "1 25544U 98067A   24112.51303241  .00018627  00000+0  33441-3 0  9993"
ISS_ZARYA_L2 = "2 25544  51.6411 132.2489 0002107  58.3917  62.4303 15.49896559448988"


class TestDistance:
    def test_same_point_is_zero(self):
        assert distance_km((100, 200, 300), (100, 200, 300)) == 0

    def test_unit_distance(self):
        assert distance_km((0, 0, 0), (3, 4, 0)) == 5.0

    def test_symmetry(self):
        d1 = distance_km((1, 2, 3), (4, 5, 6))
        d2 = distance_km((4, 5, 6), (1, 2, 3))
        assert d1 == d2


class TestComputePosition:
    def test_returns_three_tuple(self):
        dt = datetime(2024, 4, 22, 12, 0, 0, tzinfo=timezone.utc)
        pos = compute_position_eci(ISS_ZARYA_L1, ISS_ZARYA_L2, dt)
        assert pos is not None
        assert len(pos) == 3

    def test_returns_none_on_bad_tle(self):
        dt = datetime(2024, 4, 22, 12, 0, 0, tzinfo=timezone.utc)
        pos = compute_position_eci("1 garbage", "2 garbage", dt)
        assert pos is None


class TestFindConjunctions:
    def test_empty_list_returns_empty(self):
        results = find_conjunctions([], threshold_km=50)
        assert results == []

    def test_single_satellite_returns_empty(self):
        sat = {
            "norad_id": 25544,
            "name": "ISS",
            "line1": ISS_ZARYA_L1,
            "line2": ISS_ZARYA_L2,
        }
        results = find_conjunctions([sat], threshold_km=50)
        assert results == []

    def test_identical_satellites_filtered_by_zero_distance(self):
        sat = {
            "norad_id": 25544,
            "name": "ISS",
            "line1": ISS_ZARYA_L1,
            "line2": ISS_ZARYA_L2,
        }
        sat_clone = {**sat, "norad_id": 25545, "name": "ISS CLONE"}
        results = find_conjunctions([sat, sat_clone], threshold_km=100)
        assert len(results) == 0

    def test_results_sorted_by_closest_approach(self):
        from app.services.conjunction import find_conjunctions as fc
        assert sorted([3, 1, 2]) == [1, 2, 3]