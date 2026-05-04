from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel

from models.operation import OperationResponse


class ParcelStatus(str, Enum):
    PLANTED = "PLANTED"
    FALLOW = "FALLOW"
    PREPARED = "PREPARED"
    HARVESTED = "HARVESTED"


class SoilSummary(BaseModel):
    pH: float | None = None
    texture: str | None = None


class LastFertilization(BaseModel):
    date: str | None = None
    product: str | None = None


class ParcelResponse(BaseModel):
    id: str
    name: str
    area: float
    status: ParcelStatus
    location: dict[str, Any]
    municipality: str | None = None
    currentCrop: str | None = None
    lastFertilization: LastFertilization | None = None
    soilSummary: SoilSummary


class ParcelDetailResponse(ParcelResponse):
    soil: dict[str, Any] | None = None
    lastOperations: list[OperationResponse]


class ParcelStatusPatch(BaseModel):
    parcelStatus: ParcelStatus


class SuitabilityItem(BaseModel):
    cropId: str
    score: float
    band: str


class SuitabilityResponse(BaseModel):
    parcelId: str
    generatedAt: str
    ranking: list[SuitabilityItem]
