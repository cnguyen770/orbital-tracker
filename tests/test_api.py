import pytest
from app.services.satellite_service import upsert_satellites

pytestmark = pytest.mark.asyncio


SAMPLE_SATS = [
    {
        "norad_id": 25544,
        "name": "ISS (ZARYA)",
        "line1": "1 25544U 98067A   24112.51303241  .00018627  00000+0  33441-3 0  9993",
        "line2": "2 25544  51.6411 132.2489 0002107  58.3917  62.4303 15.49896559448988",
    },
]


async def test_health_check(api_client):
    response = await api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_list_groups(api_client):
    response = await api_client.get("/api/satellites/groups")
    assert response.status_code == 200
    data = response.json()
    assert "groups" in data
    assert "stations" in data["groups"]


async def test_list_satellites_empty(api_client):
    response = await api_client.get("/api/satellites/")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_satellites_populated(api_client, db):
    await upsert_satellites(db, SAMPLE_SATS, "stations")

    response = await api_client.get("/api/satellites/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["norad_id"] == 25544


async def test_get_satellite_by_norad(api_client, db):
    await upsert_satellites(db, SAMPLE_SATS, "stations")

    response = await api_client.get("/api/satellites/25544")
    assert response.status_code == 200
    assert response.json()["name"] == "ISS (ZARYA)"


async def test_get_satellite_not_found(api_client):
    response = await api_client.get("/api/satellites/99999")
    assert response.status_code == 404


async def test_get_position(api_client, db):
    await upsert_satellites(db, SAMPLE_SATS, "stations")

    response = await api_client.get("/api/satellites/25544/position")
    assert response.status_code == 200
    data = response.json()
    assert "latitude" in data
    assert "longitude" in data
    assert "altitude_km" in data
    assert -90 <= data["latitude"] <= 90
    assert -180 <= data["longitude"] <= 180


async def test_get_position_missing_satellite(api_client):
    response = await api_client.get("/api/satellites/99999/position")
    assert response.status_code == 404


async def test_batch_positions(api_client, db):
    await upsert_satellites(db, SAMPLE_SATS, "stations")

    response = await api_client.get("/api/satellites/positions")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert "timestamp" in data
    assert len(data["positions"]) == data["count"]


async def test_search_finds_satellite(api_client, db):
    await upsert_satellites(db, SAMPLE_SATS, "stations")

    response = await api_client.get("/api/satellites/search?q=iss")
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_search_requires_min_length(api_client):
    response = await api_client.get("/api/satellites/search?q=a")
    assert response.status_code == 400


async def test_overhead_returns_empty_for_no_satellites(api_client):
    response = await api_client.get("/api/satellites/overhead?lat=37.3&lon=-121.9")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["satellites"] == []


async def test_overhead_validates_coordinates(api_client):
    response = await api_client.get("/api/satellites/overhead?lat=200&lon=0")
    assert response.status_code == 400

    response = await api_client.get("/api/satellites/overhead?lat=0&lon=200")
    assert response.status_code == 400

    response = await api_client.get("/api/satellites/overhead?lat=0&lon=0&radius_km=-100")
    assert response.status_code == 400


async def test_featured_endpoint(api_client):
    response = await api_client.get("/api/satellites/featured")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "satellites" in data
    for sat in data["satellites"]:
        assert "tagline" in sat
        assert "available" in sat


async def test_conjunctions_empty_for_insufficient_satellites(api_client):
    response = await api_client.get("/api/satellites/conjunctions?group=stations")
    assert response.status_code == 200
    data = response.json()
    assert data["conjunction_count"] == 0


async def test_conjunctions_rejects_unknown_group(api_client):
    response = await api_client.get("/api/satellites/conjunctions?group=fake_group")
    assert response.status_code == 400


async def test_scheduler_status(api_client):
    response = await api_client.get("/api/satellites/scheduler/status")
    assert response.status_code == 200
    data = response.json()
    assert "running"