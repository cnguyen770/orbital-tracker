import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def parse_tle_file(raw_text: str) -> list[dict]:
    satellites = []
    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]

    for i in range(0, len(lines) - 2, 3):
        name = lines[i]
        line1 = lines[i + 1]
        line2 = lines[i + 2]

        if not line1.startswith("1") or not line2.startswith("2"):
            logger.warning(f"Skipping malformed TLE block at line {i}: {name}")
            continue

        satellites.append({
            "name": name,
            "line1": line1,
            "line2": line2,
            "norad_id": int(line1[2:7].strip()),
        })

    return satellites


async def fetch_tle_group(group: str = "stations") -> list[dict]:
    url = f"{settings.CELESTRAK_BASE_URL}?GROUP={group}&FORMAT=tle"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()

    parsed = parse_tle_file(response.text)
    logger.info(f"Fetched {len(parsed)} satellites from group '{group}'")
    return parsed