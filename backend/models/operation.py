from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class OperationResponse(BaseModel):
    id: str
    operationType: str
    startedAt: str | None = None
    endedAt: str | None = None
    quantityApplied: float | None = None
    unitCode: str | None = None
    notes: str | None = None
    refParcel: str
    refFertilizer: str | None = None
    metadata: dict[str, Any] | None = None


class OperationCreate(BaseModel):
    operationType: str
    startedAt: str | None = None
    endedAt: str | None = None
    quantityApplied: float | None = None
    unitCode: str | None = None
    notes: str | None = None
    refFertilizer: str | None = None


class OperationPatch(BaseModel):
    startedAt: str | None = None
    endedAt: str | None = None
    quantityApplied: float | None = None
    notes: str | None = None
