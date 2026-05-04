from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FarmCreate(BaseModel):
    id: str
    name: str
    farmType: str
    ownerName: str
    municipality: str | None = None
    location: dict[str, Any] | None = None


class FarmResponse(BaseModel):
    id: str
    name: str
    farmType: str
    ownerName: str
    municipality: str | None = None


class FarmDetailResponse(FarmResponse):
    parcels: list[str]
