from typing import List, Optional

from fastapi import Query
from pydantic import BaseModel


class StartChoice(BaseModel):
    lat: float
    lon: float
    cluster: List[str] = Query(None)


class Marker(BaseModel):
    lat: float
    lon: float
    title: str
    marker_id: float
    url: str
    text_clean: str
    img_src: str
    marker_ents: Optional[List[str]]


class NearbyOptions(BaseModel):
    markers: List[Marker]
    map_center: List[float]


class Route(BaseModel):
    markers: List[Marker]
    map_center: List[float]
    route_polylines: List[List[float]]
    marker_order: List[int]
    route_str: str
    optimal_duration: float


class StepTwo(BaseModel):
    radius: float
    start_marker: int
