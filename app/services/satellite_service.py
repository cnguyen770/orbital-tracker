from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.satellite import Satellite
from sqlalchemy import or_


async def upsert_satellites(db: AsyncSession, satellites: list[dict], group: str) -> int:
    for sat in satellites:
        result = await db.execute(
            select(Satellite).where(Satellite.norad_id == sat["norad_id"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = sat["name"]
            existing.line1 = sat["line1"]
            existing.line2 = sat["line2"]
            existing.group = group
        else:
            db.add(Satellite(
                norad_id=sat["norad_id"],
                name=sat["name"],
                line1=sat["line1"],
                line2=sat["line2"],
                group=group,
            ))

    await db.commit()
    return len(satellites)


async def get_all_satellites(db: AsyncSession, group: str = None) -> list[Satellite]:
    query = select(Satellite).order_by(Satellite.name)
    if group:
        query = query.where(Satellite.group == group)
    result = await db.execute(query)
    return result.scalars().all()


async def get_satellite_by_norad(db: AsyncSession, norad_id: int) -> Satellite | None:
    result = await db.execute(
        select(Satellite).where(Satellite.norad_id == norad_id)
    )
    return result.scalar_one_or_none()

async def search_satellites(
    db: AsyncSession,
    query: str,
    group: str | None = None,
    limit: int = 50,
) -> list[Satellite]:
    stmt = select(Satellite).where(
        Satellite.name.ilike(f"%{query}%")
    )

    if group:
        stmt = stmt.where(Satellite.group == group)

    stmt = stmt.order_by(Satellite.name).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()