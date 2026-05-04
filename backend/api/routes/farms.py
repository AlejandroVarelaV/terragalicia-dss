from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user, get_orion, load_seed, prop
from config import get_settings
from models.auth import UserPublic
from models.farm import FarmCreate, FarmDetailResponse, FarmResponse
from services.orion import OrionClient

router = APIRouter(prefix="/farms", tags=["farms"])


def _to_farm_response(entity: dict[str, Any]) -> FarmResponse:
    return FarmResponse(
        id=entity["id"],
        name=prop(entity, "name", ""),
        farmType=prop(entity, "farmType", "unknown"),
        ownerName=prop(entity, "ownerName", "unknown"),
        municipality=(prop(entity, "refMunicipality", "") or "").split(":")[-1] or None,
    )


@router.get("", response_model=list[FarmResponse])
async def list_farms(
    _: UserPublic = Depends(get_current_user),
    orion: OrionClient = Depends(get_orion),
) -> list[FarmResponse]:
    try:
        entities = await orion.query_entities("AgriFarm", params={"limit": 100})
    except Exception:
        settings_obj = get_settings()
        entities = load_seed(settings_obj, "seed_farms.json")

    return [_to_farm_response(entity) for entity in entities]


@router.get("/{farm_id}", response_model=FarmDetailResponse)
async def get_farm(
    farm_id: str,
    _: UserPublic = Depends(get_current_user),
    orion: OrionClient = Depends(get_orion),
) -> FarmDetailResponse:
    try:
        entity = await orion.get_entity(farm_id, "AgriFarm")
    except Exception:
        settings_obj = get_settings()
        entity = next((item for item in load_seed(settings_obj, "seed_farms.json") if item["id"] == farm_id), None)

    if not entity:
        raise HTTPException(status_code=404, detail="Farm not found")

    farm = _to_farm_response(entity)
    parcels = prop(entity, "hasAgriParcel", []) or []
    if isinstance(parcels, str):
        parcels = [parcels]
    return FarmDetailResponse(**farm.model_dump(), parcels=parcels)


@router.post("", response_model=FarmResponse, status_code=201)
async def create_farm(
    payload: FarmCreate,
    _: UserPublic = Depends(get_current_user),
    orion: OrionClient = Depends(get_orion),
) -> FarmResponse:
    entity = {
        "id": payload.id,
        "type": "AgriFarm",
        "name": {"type": "Property", "value": payload.name},
        "farmType": {"type": "Property", "value": payload.farmType},
        "ownerName": {"type": "Property", "value": payload.ownerName},
        "refMunicipality": {
            "type": "Relationship",
            "object": f"urn:ngsi-ld:AdministrativeArea:municipality:{payload.municipality or 'unknown'}",
        },
    }
    if payload.location:
        entity["location"] = {"type": "GeoProperty", "value": payload.location}

    await orion.create_entity(entity)
    return _to_farm_response(entity)
