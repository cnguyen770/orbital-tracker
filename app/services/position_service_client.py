import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def compute_positions_remote(
    satellites: list[dict],
    dt: datetime,
    base_url: str,
) -> list[dict] | None:
    payload = {
        "satellites": [
            {
                "tleLine1": sat["line1"],
                "tleLine2": sat["line2"],
            }
            for sat in satellites
        ],
        "timestamp": dt.isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{base_url}/positions/batch",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        norad_lookup = {str(sat["norad_id"]): sat for sat in satellites}

        results = []
        for pos in data.get("positions", []):
            norad_id_str = str(pos.get("noradId", "")).strip()
            sat = norad_lookup.get(norad_id_str)
            if sat is None:
                continue
            results.append({
                "norad_id": sat["norad_id"],
                "name": sat["name"],
                "latitude": round(pos["latitude"], 4),
                "longitude": round(pos["longitude"], 4),
                "altitude_km": round(pos["altitudeKm"], 2),
            })

        return results

    except Exception as exc:
        logger.warning(
            "Position service unavailable, falling back to inline SGP4: %s", exc
        )
        return None