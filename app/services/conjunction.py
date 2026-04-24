from datetime import datetime, timezone, timedelta
from sgp4.api import Satrec, WGS84, jday
import math


def compute_position_eci(line1: str, line2: str, dt: datetime) -> tuple[float, float, float] | None:
    satellite = Satrec.twoline2rv(line1, line2, WGS84)
    jd, fr = jday(
        dt.year, dt.month, dt.day,
        dt.hour, dt.minute, dt.second + dt.microsecond / 1e6
    )
    error, position, _ = satellite.sgp4(jd, fr)
    if error != 0:
        return None
    return tuple(position)


def distance_km(pos1: tuple, pos2: tuple) -> float:
    return math.sqrt(
        (pos1[0] - pos2[0])**2 +
        (pos1[1] - pos2[1])**2 +
        (pos1[2] - pos2[2])**2
    )


def find_conjunctions(
    satellites: list[dict],
    threshold_km: float = 10.0,
    minutes: int = 30,
    step_seconds: int = 60,
) -> list[dict]:
    now = datetime.now(timezone.utc)
    time_steps = [
        now + timedelta(seconds=i)
        for i in range(0, minutes * 60, step_seconds)
    ]

    conjunctions = []

    for i in range(len(satellites)):
        for j in range(i + 1, len(satellites)):
            sat_a = satellites[i]
            sat_b = satellites[j]

            closest_distance = float("inf")
            closest_time = None

            for dt in time_steps:
                pos_a = compute_position_eci(sat_a["line1"], sat_a["line2"], dt)
                pos_b = compute_position_eci(sat_b["line1"], sat_b["line2"], dt)

                if pos_a is None or pos_b is None:
                    continue

                dist = distance_km(pos_a, pos_b)
                if dist < closest_distance:
                    closest_distance = dist
                    closest_time = dt

            if 0.1 <= closest_distance <= threshold_km:
                conjunctions.append({
                    "satellite_a": sat_a["name"],
                    "norad_id_a": sat_a["norad_id"],
                    "satellite_b": sat_b["name"],
                    "norad_id_b": sat_b["norad_id"],
                    "closest_approach_km": round(closest_distance, 3),
                    "time_of_closest_approach": closest_time.isoformat(),
                })

    return sorted(conjunctions, key=lambda x: x["closest_approach_km"])