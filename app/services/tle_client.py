import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def parse_tle_file(raw_text: str) -> list[dict]:
    """
    Parse raw TLE file text into a list of satellite dicts.

    A TLE file is a plain text file where every 3 lines represent one satellite:
    Line 0: satellite name
    Line 1: first data line (starts with "1")
    Line 2: second data line (starts with "2")
    """
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
    """
    Fetch a TLE group from Celestrak and return parsed satellites.

    Common groups:
    - "stations"  — ISS and other space stations
    - "visual"    — brightest/most visible satellites
    - "starlink"  — all Starlink satellites
    """
    url = f"{settings.CELESTRAK_BASE_URL}?GROUP={group}&FORMAT=tle"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()

    parsed = parse_tle_file(response.text)
    logger.info(f"Fetched {len(parsed)} satellites from group '{group}'")
    return parsed