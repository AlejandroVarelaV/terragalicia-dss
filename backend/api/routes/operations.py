from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_current_user, get_operation_store, get_orion, prop, require_roles
from models.auth import UserPublic
from models.operation import OperationCreate, OperationPatch, OperationResponse
from services.orion import OrionClient

router = APIRouter(prefix="/parcels", tags=["operations"])


def _to_response(operation: dict[str, Any]) -> OperationResponse:
    return OperationResponse(
        id=operation["id"],
        operationType=prop(operation, "operationType", "unknown"),
        startedAt=prop(operation, "startedAt"),
        endedAt=prop(operation, "endedAt"),
        quantityApplied=prop(operation, "quantityApplied"),
        unitCode=prop(operation, "unitCode"),
        notes=prop(operation, "notes"),
        refParcel=prop(operation, "refParcel", ""),
        refFertilizer=prop(operation, "refFertilizer"),
    )


@router.get("/{parcel_id}/operations", response_model=list[OperationResponse])
async def list_operations(
    parcel_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    operation_type: str | None = Query(default=None, alias="type"),
    _: UserPublic = Depends(get_current_user),
    operation_store: list[dict[str, Any]] = Depends(get_operation_store),
) -> list[OperationResponse]:
    filtered = [item for item in operation_store if prop(item, "refParcel") == parcel_id]
    if operation_type:
        filtered = [item for item in filtered if prop(item, "operationType") == operation_type]

    filtered.sort(key=lambda item: prop(item, "startedAt") or "", reverse=True)
    start = (page - 1) * page_size
    end = start + page_size
    return [_to_response(item) for item in filtered[start:end]]


@router.post("/{parcel_id}/operations", response_model=OperationResponse, status_code=201)
async def create_operation(
    parcel_id: str,
    body: OperationCreate,
    _: UserPublic = Depends(require_roles(["farmer", "cooperative", "admin"])),
    operation_store: list[dict[str, Any]] = Depends(get_operation_store),
    orion: OrionClient = Depends(get_orion),
) -> OperationResponse:
    op_id = f"urn:ngsi-ld:AgriParcelOperation:{uuid4()}"
    started_at = body.startedAt or datetime.now(UTC).isoformat()

    entity = {
        "id": op_id,
        "type": "AgriParcelOperation",
        "operationType": {"type": "Property", "value": body.operationType},
        "startedAt": {"type": "Property", "value": started_at},
        "endedAt": {"type": "Property", "value": body.endedAt},
        "quantityApplied": {"type": "Property", "value": body.quantityApplied},
        "unitCode": {"type": "Property", "value": body.unitCode},
        "notes": {"type": "Property", "value": body.notes},
        "refParcel": {"type": "Relationship", "object": parcel_id},
    }
    if body.refFertilizer:
        entity["refFertilizer"] = {"type": "Relationship", "object": body.refFertilizer}

    try:
        await orion.create_entity(entity)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to persist operation to Orion CB: {exc}")

    operation_store.append(entity)
    return _to_response(entity)


@router.patch("/operations/{op_id}", response_model=OperationResponse)
async def update_operation(
    op_id: str,
    body: OperationPatch,
    _: UserPublic = Depends(require_roles(["farmer", "cooperative", "admin"])),
    operation_store: list[dict[str, Any]] = Depends(get_operation_store),
) -> OperationResponse:
    target = next((item for item in operation_store if item["id"] == op_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Operation not found")

    if body.startedAt is not None:
        target["startedAt"] = {"type": "Property", "value": body.startedAt}
    if body.endedAt is not None:
        target["endedAt"] = {"type": "Property", "value": body.endedAt}
    if body.quantityApplied is not None:
        target["quantityApplied"] = {"type": "Property", "value": body.quantityApplied}
    if body.notes is not None:
        target["notes"] = {"type": "Property", "value": body.notes}

    return _to_response(target)
