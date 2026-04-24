from sgp4.api import Satrec, WGS84, jday
from sgp4.conveniences import sat_epoch_datetime
from datetime import datetime, timezone
import math
from datetime import timedelta

def get_satellite_position(line1: str, line2: str, dt: datetime = None) -> dict:
    if dt is None:
        dt = datetime.now(timezone.utc)

    satellite = Satrec.twoline2rv(line1, line2, WGS84)

    jd, fr = jday(
        dt.year, dt.month, dt.day,
        dt.hour, dt.minute, dt.second + dt.microsecond / 1e6
    )
    error, position, velocity = satellite.sgp4(jd, fr)

    if error != 0:
        raise ValueError(f"SGP4 error code {error} — TLE may be too old")

    x, y, z = position
    vx, vy, vz = velocity

    EARTH_RADIUS_KM = 6371.0

    r = math.sqrt(x**2 + y**2 + z**2)

    lat = math.degrees(math.asin(z / r))

    lon = math.degrees(math.atan2(y, x))

    alt = r - EARTH_RADIUS_KM

    speed = math.sqrt(vx**2 + vy**2 + vz**2)

    return {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "altitude_km": round(alt, 2),
        "speed_km_s": round(speed, 4),
        "timestamp": dt.isoformat(),
    }

def get_orbital_path(line1: str, line2: str, minutes: int = 90) -> list[dict]:
    now = datetime.now(timezone.utc)
    path = []

    for i in range(0, minutes * 60, 60):
        dt = now + timedelta(seconds=i)
        try:
            position = get_satellite_position(line1, line2, dt)
            path.append({
                "latitude": position["latitude"],
                "longitude": position["longitude"],
                "altitude_km": position["altitude_km"],
                "timestamp": position["timestamp"],
            })
        except ValueError:
            continue

    return path

def get_positions_batch(satellites: list[dict], dt: datetime = None) -> list[dict]:
    if dt is None:
        dt = datetime.now(timezone.utc)

    jd, fr = jday(
        dt.year, dt.month, dt.day,
        dt.hour, dt.minute, dt.second + dt.microsecond / 1e6
    )

    EARTH_RADIUS_KM = 6371.0
    results = []

    for sat in satellites:
        try:
            satellite = Satrec.twoline2rv(sat["line1"], sat["line2"], WGS84)
            error, position, velocity = satellite.sgp4(jd, fr)

            if error != 0:
                continue

            x, y, z = position
            vx, vy, vz = velocity
            r = math.sqrt(x**2 + y**2 + z**2)

            results.append({
                "norad_id": sat["norad_id"],
                "name": sat["name"],
                "latitude": round(math.degrees(math.asin(z / r)), 4),
                "longitude": round(math.degrees(math.atan2(y, x)), 4),
                "altitude_km": round(r - EARTH_RADIUS_KM, 2),
                "speed_km_s": round(math.sqrt(vx**2 + vy**2 + vz**2), 4),
            })
        except Exception:
            continue

    return results

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    EARTH_RADIUS_KM = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))