import pytest
from app.services.satellite_service import (
    upsert_satellites,
    get_all_satellites,
    get_satellite_by_norad,
    search_satellites,
)

pytestmark = pytest.mark.asyncio


SAMPLE_SATS = [
    {
        "norad_id": 25544,
        "name": "ISS (ZARYA)",
        "line1": "1 25544U ...",
        "line2": "2 25544 ...",
    },
    {
        "norad_id": 20580,
        "name": "HST",
        "line1": "1 20580U ...",
        "line2": "2 20580 ...",
    },
]


async def test_upsert_creates_new_satellites(db):
    count = await upsert_satellites(db, SAMPLE_SATS, "stations")
    assert count == 2

    results = await get_all_satellites(db)
    assert len(results) == 2


async def test_upsert_is_idempotent(db):
    await upsert_satellites(db, SAMPLE_SATS, "stations")
    await upsert_satellites(db, SAMPLE_SATS, "stations")

    results = await get_all_satellites(db)
    assert len(results) == 2


async def test_upsert_updates_existing(db):
    await upsert_satellites(db, SAMPLE_SATS, "stations")

    modified = [{**SAMPLE_SATS[0], "name": "ISS UPDATED"}]
    await upsert_satellites(db, modified, "stations")

    sat = await get_satellite_by_norad(db, 25544)
    assert sat.name == "ISS UPDATED"


async def test_group_filter(db):
    await upsert_satellites(db, [SAMPLE_SATS[0]], "stations")
    await upsert_satellites(db, [SAMPLE_SATS[1]], "visual")

    stations = await get_all_satellites(db, "stations")
    visual = await get_all_satellites(db, "visual")

    assert len(stations) == 1
    assert stations[0].norad_id == 25544
    assert len(visual) == 1
    assert visual[0].norad_id == 20580


async def test_get_missing_returns_none(db):
    result = await get_satellite_by_norad(db, 99999)
    assert result is None


async def test_search_case_insensitive(db):
    await upsert_satellites(db, SAMPLE_SATS, "stations")

    results = await search_satellites(db, "iss")
    assert len(results) == 1
    assert results[0].norad_id == 25544


async def test_search_substring_match(db):
    await upsert_satellites(db, SAMPLE_SATS, "stations")

    results = await search_satellites(db, "zarya")
    assert len(results) == 1


async def test_search_with_group_filter(db):
    await upsert_satellites(db, [SAMPLE_SATS[0]], "stations")
    await upsert_satellites(db, [SAMPLE_SATS[1]], "visual")

    results = await search_satellites(db, "", group="stations")
    iss_results = await search_satellites(db, "iss", group="visual")
    assert len(iss_results) == 0