from __future__ import annotations

from pydantic import BaseModel


class CropResponse(BaseModel):
    id: str
    species: str
    waterNeedMm: float | None = None
    yieldTnHa: float | None = None
    recommendedSoilPHMin: float | None = None
    recommendedSoilPHMax: float | None = None


class CropDetailResponse(CropResponse):
    plantingDateStart: str | None = None
    plantingDateEnd: str | None = None
    harvestDateStart: str | None = None
    harvestDateEnd: str | None = None
