from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.satellite import Satellite


async def upsert_satellites(db: AsyncSession, satellites: list[dict]) -> int:
    """
    Insert new satellites or update existing ones by NORAD ID.
    Returns the count of satellites processed.
    """
    for sat in satellites:
        result = await db.execute(
            select(Satellite).where(Satellite.norad_id == sat["norad_id"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = sat["name"]
            existing.line1 = sat["line1"]
            existing.line2 = sat["line2"]
        else:
            db.add(Satellite(
                norad_id=sat["norad_id"],
                name=sat["name"],
                line1=sat["line1"],
                line2=sat["line2"],
            ))

    await db.commit()
    return len(satellites)


async def get_all_satellites(db: AsyncSession) -> list[Satellite]:
    result = await db.execute(select(Satellite).order_by(Satellite.name))
    return result.scalars().all()


async def get_satellite_by_norad(db: AsyncSession, norad_id: int) -> Satellite | None:
    result = await db.execute(
        select(Satellite).where(Satellite.norad_id == norad_id)
    )
    return result.scalar_one_or_none()