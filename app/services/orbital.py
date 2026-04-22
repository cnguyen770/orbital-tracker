from sgp4.api import Satrec, WGS84, jday
from sgp4.conveniences import sat_epoch_datetime
from datetime import datetime, timezone
import math
from datetime import timedelta

def get_satellite_position(line1: str, line2: str, dt: datetime = None) -> dict:
    """
    Calculate a satellite's position at a given time.
    Defaults to current time if no datetime provided.

    Returns latitude, longitude, altitude and velocity.
    """
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

    # position is in km in Earth-Centered Inertial (ECI) coordinates
    # convert to latitude, longitude, altitude
    x, y, z = position
    vx, vy, vz = velocity

    # Earth radius in km
    EARTH_RADIUS_KM = 6371.0

    # Distance from Earth center
    r = math.sqrt(x**2 + y**2 + z**2)

    # Latitude (degrees)
    lat = math.degrees(math.asin(z / r))

    # Longitude (degrees) — account for Earth's rotation
    lon = math.degrees(math.atan2(y, x))

    # Altitude above Earth surface (km)
    alt = r - EARTH_RADIUS_KM

    # Speed (km/s)
    speed = math.sqrt(vx**2 + vy**2 + vz**2)

    return {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "altitude_km": round(alt, 2),
        "speed_km_s": round(speed, 4),
        "timestamp": dt.isoformat(),
    }

def get_orbital_path(line1: str, line2: str, minutes: int = 90) -> list[dict]:
    """
    Calculate the ground track of a satellite over a given time window.
    Defaults to 90 minutes — roughly one full orbit for LEO satellites.

    Samples position every 60 seconds.
    """
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