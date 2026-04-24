from pydantic import BaseModel, Field
from typing import Optional


class PositionResponse(BaseModel):
    norad_id: int
    name: str
    latitude: float
    longitude: float
    altitude_km: float
    speed_km_s: float


class SinglePositionResponse(PositionResponse):
    timestamp: str


class PathPoint(BaseModel):
    latitude: float
    longitude: float
    altitude_km: float
    timestamp: str


class OrbitalPathResponse(BaseModel):
    norad_id: int
    name: str
    minutes: int
    point_count: int
    path: list[PathPoint]


class BatchPositionResponse(BaseModel):
    timestamp: str
    count: int
    group: Optional[str] = None
    positions: list[PositionResponse]


class SatelliteSummary(BaseModel):
    norad_id: int
    name: str
    group: str


class SatelliteDetail(SatelliteSummary):
    line1: str
    line2: str


class ConjunctionEvent(BaseModel):
    satellite_a: str
    norad_id_a: int
    satellite_b: str
    norad_id_b: int
    closest_approach_km: float
    time_of_closest_approach: str


class ConjunctionResponse(BaseModel):
    group: str
    threshold_km: float
    minutes_checked: int
    conjunction_count: int
    conjunctions: list[ConjunctionEvent]


class IngestResponse(BaseModel):
    message: str


class GroupsResponse(BaseModel):
    groups: list[str]


class SchedulerJob(BaseModel):
    id: str
    next_run: str


class SchedulerStatus(BaseModel):
    running: bool
    jobs: list[SchedulerJob]

class OverheadSatellite(BaseModel):
    norad_id: int
    name: str
    group: str
    latitude: float
    longitude: float
    altitude_km: float
    distance_km: float

class OverheadResponse(BaseModel):
    user_lat: float
    user_lon: float
    radius_km: float
    timestamp: str
    count: int
    satellites: list[OverheadSatellite]

class FeaturedSatellite(BaseModel):
    norad_id: int
    name: str
    group: str
    tagline: str
    description: str
    available: bool


class FeaturedResponse(BaseModel):
    count: int
    satellites: list[FeaturedSatellite]
