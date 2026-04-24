from app.core.featured import FEATURED_SATELLITES
from app.services.orbital import get_satellite_position, get_orbital_path, get_positions_batch
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.satellite_service import (
    get_all_satellites,
    get_satellite_by_norad,
    upsert_satellites,
)
from app.services.tle_client import fetch_tle_group
from app.services.orbital import get_satellite_position, get_orbital_path
from app.services.conjunction import find_conjunctions
from app.models.responses import (
    PositionResponse,
    SinglePositionResponse,
    OrbitalPathResponse,
    BatchPositionResponse,
    SatelliteSummary,
    SatelliteDetail,
    ConjunctionResponse,
    IngestResponse,
    GroupsResponse,
    SchedulerStatus,
    OverheadResponse,
    FeaturedResponse,
)
from app.services.satellite_service import (
    get_all_satellites,
    get_satellite_by_norad,
    upsert_satellites,
    search_satellites,
)
from app.services.orbital import (
    get_satellite_position,
    get_orbital_path,
    get_positions_batch,
    haversine_km,
)

router = APIRouter()

AVAILABLE_GROUPS = [
    "stations",
    "starlink",
    "gps-ops",
    "weather",
    "visual",
]


@router.get("/groups", response_model=GroupsResponse)
async def list_groups():
    return {"groups": AVAILABLE_GROUPS}

@router.get("/scheduler/status", response_model=SchedulerStatus)
async def scheduler_status():
    from app.services.scheduler import scheduler
    jobs = scheduler.get_jobs()
    return {
        "running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "next_run": str(job.next_run_time),
            }
            for job in jobs
        ]
    }

@router.post("/ingest", response_model=IngestResponse)
async def ingest_satellites(
    group: str = "stations",
    db: AsyncSession = Depends(get_db)
):
    if group not in AVAILABLE_GROUPS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown group '{group}'. Available: {AVAILABLE_GROUPS}"
        )
    satellites = await fetch_tle_group(group)
    count = await upsert_satellites(db, satellites, group)
    return {"message": f"Ingested {count} satellites from group '{group}'"}


@router.get("/", response_model=list[SatelliteSummary])
async def list_satellites(
    group: str = None,
    db: AsyncSession = Depends(get_db)
):
    satellites = await get_all_satellites(db, group)
    return [
        {
            "norad_id": s.norad_id,
            "name": s.name,
            "group": s.group,
        }
        for s in satellites
    ]

@router.get("/positions", response_model=BatchPositionResponse)
async def get_positions(
    group: str = None,
    limit: int = 500,
    db: AsyncSession = Depends(get_db)
):
    satellites = await get_all_satellites(db, group)
    satellites = satellites[:limit]

    sat_dicts = [
        {
            "norad_id": s.norad_id,
            "name": s.name,
            "line1": s.line1,
            "line2": s.line2,
        }
        for s in satellites
    ]

    import asyncio
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    positions = await asyncio.to_thread(get_positions_batch, sat_dicts, now)

    return {
        "timestamp": now.isoformat(),
        "count": len(positions),
        "group": group,
        "positions": positions,
    }
@router.get("/conjunctions", response_model=ConjunctionResponse)
async def get_conjunctions(
    group: str = "stations",
    threshold_km: float = 50.0,
    minutes: int = 30,
    db: AsyncSession = Depends(get_db)
):
    if group not in AVAILABLE_GROUPS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown group. Available: {AVAILABLE_GROUPS}"
        )

    MAX_CONJUNCTION_GROUP_SIZE = 200

    satellites = await get_all_satellites(db, group)

    if len(satellites) > MAX_CONJUNCTION_GROUP_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Group '{group}' has {len(satellites)} satellites. "
                f"Conjunction detection is capped at {MAX_CONJUNCTION_GROUP_SIZE} "
                f"to prevent excessive computation. Try a smaller group like "
                f"'stations' or 'weather'."
            )
        )

    if len(satellites) < 2:
        return {
            "group": group,
            "threshold_km": threshold_km,
            "minutes_checked": minutes,
            "conjunction_count": 0,
            "conjunctions": [],
        }

    sat_dicts = [
        {
            "norad_id": s.norad_id,
            "name": s.name,
            "line1": s.line1,
            "line2": s.line2,
        }
        for s in satellites
    ]

    results = find_conjunctions(
        sat_dicts,
        threshold_km=threshold_km,
        minutes=minutes,
    )

    return {
        "group": group,
        "threshold_km": threshold_km,
        "minutes_checked": minutes,
        "conjunction_count": len(results),
        "conjunctions": results
    }

@router.get("/search", response_model=list[SatelliteSummary])
async def search(
    q: str,
    group: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Search query must be at least 2 characters."
        )

    results = await search_satellites(db, q, group, limit)
    return [
        {
            "norad_id": s.norad_id,
            "name": s.name,
            "group": s.group,
        }
        for s in results
    ]

@router.get("/overhead", response_model=OverheadResponse)
async def satellites_overhead(
    lat: float,
    lon: float,
    radius_km: float = 500.0,
    group: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(
            status_code=400,
            detail="Invalid coordinates. lat must be in [-90, 90], lon in [-180, 180]."
        )
    if radius_km <= 0 or radius_km > 5000:
        raise HTTPException(
            status_code=400,
            detail="radius_km must be between 0 and 5000."
        )

    satellites = await get_all_satellites(db, group)
    satellites = satellites[:500]

    sat_dicts = [
        {
            "norad_id": s.norad_id,
            "name": s.name,
            "line1": s.line1,
            "line2": s.line2,
            "group": s.group,
        }
        for s in satellites
    ]

    import asyncio
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    positions = await asyncio.to_thread(get_positions_batch, sat_dicts, now)

    group_lookup = {s["norad_id"]: s["group"] for s in sat_dicts}

    results = []
    for pos in positions:
        distance = haversine_km(lat, lon, pos["latitude"], pos["longitude"])
        if distance <= radius_km:
            results.append({
                "norad_id": pos["norad_id"],
                "name": pos["name"],
                "group": group_lookup.get(pos["norad_id"], "unknown"),
                "latitude": pos["latitude"],
                "longitude": pos["longitude"],
                "altitude_km": pos["altitude_km"],
                "distance_km": round(distance, 2),
            })

    results.sort(key=lambda r: r["distance_km"])

    return {
        "user_lat": lat,
        "user_lon": lon,
        "radius_km": radius_km,
        "timestamp": now.isoformat(),
        "count": len(results),
        "satellites": results,
    }
@router.get("/featured", response_model=FeaturedResponse)
async def list_featured(db: AsyncSession = Depends(get_db)):
    results = []
    for norad_id, meta in FEATURED_SATELLITES.items():
        sat = await get_satellite_by_norad(db, norad_id)
        results.append({
            "norad_id": norad_id,
            "name": sat.name if sat else meta["tagline"],
            "group": sat.group if sat else "unknown",
            "tagline": meta["tagline"],
            "description": meta["description"],
            "available": sat is not None,
        })

    return {"count": len(results), "satellites": results}
@router.get("/{norad_id}", response_model=SatelliteDetail)
async def get_satellite(norad_id: int, db: AsyncSession = Depends(get_db)):
    satellite = await get_satellite_by_norad(db, norad_id)
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return {
        "norad_id": satellite.norad_id,
        "name": satellite.name,
        "group": satellite.group,
        "line1": satellite.line1,
        "line2": satellite.line2,
    }


@router.get("/{norad_id}/position", response_model=SinglePositionResponse)
async def get_position(norad_id: int, db: AsyncSession = Depends(get_db)):
    satellite = await get_satellite_by_norad(db, norad_id)
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")
    try:
        position = get_satellite_position(satellite.line1, satellite.line2)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"norad_id": satellite.norad_id, "name": satellite.name, **position}


@router.get("/{norad_id}/path", response_model=OrbitalPathResponse)
async def get_orbital_path_endpoint(
    norad_id: int,
    minutes: int = 90,
    db: AsyncSession = Depends(get_db)
):
    satellite = await get_satellite_by_norad(db, norad_id)
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")
    path = get_orbital_path(satellite.line1, satellite.line2, minutes)
    return {
        "norad_id": satellite.norad_id,
        "name": satellite.name,
        "minutes": minutes,
        "point_count": len(path),
        "path": path
    }
