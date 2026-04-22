from app.services.orbital import get_satellite_position
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
router = APIRouter()


@router.post("/ingest")
async def ingest_satellites(
    group: str = "stations",
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch TLE data from Celestrak and save to database.
    """
    satellites = await fetch_tle_group(group)
    count = await upsert_satellites(db, satellites)
    return {"message": f"Ingested {count} satellites from group '{group}'"}


@router.get("/")
async def list_satellites(db: AsyncSession = Depends(get_db)):
    """
    Return all satellites in the database.
    """
    satellites = await get_all_satellites(db)
    return [
        {
            "norad_id": s.norad_id,
            "name": s.name,
        }
        for s in satellites
    ]


@router.get("/{norad_id}")
async def get_satellite(norad_id: int, db: AsyncSession = Depends(get_db)):
    """
    Return a single satellite by NORAD ID.
    """
    satellite = await get_satellite_by_norad(db, norad_id)
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return {
        "norad_id": satellite.norad_id,
        "name": satellite.name,
        "line1": satellite.line1,
        "line2": satellite.line2,
    }

@router.get("/{norad_id}/position")
async def get_position(norad_id: int, db: AsyncSession = Depends(get_db)):
    """
    Return the current position of a satellite in lat/lng/altitude.
    """
    satellite = await get_satellite_by_norad(db, norad_id)
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")

    try:
        position = get_satellite_position(satellite.line1, satellite.line2)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "norad_id": satellite.norad_id,
        "name": satellite.name,
        **position
    }

@router.get("/{norad_id}/path")
async def get_orbital_path_endpoint(
    norad_id: int,
    minutes: int = 90,
    db: AsyncSession = Depends(get_db)
):
    """
    Return the projected ground track for a satellite
    over the next N minutes. Defaults to 90 minutes.
    """
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