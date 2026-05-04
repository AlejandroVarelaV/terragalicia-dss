from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import (
    get_current_user,
    get_operation_store,
    get_orion,
    get_parcel_status_overrides,
    load_seed,
    prop,
    require_roles,
)
from config import get_settings
from models.auth import UserPublic
from models.operation import OperationResponse
from models.parcel import LastFertilization, ParcelDetailResponse, ParcelResponse, ParcelStatusPatch, SoilSummary
from services.orion import OrionClient

router = APIRouter(prefix="/parcels", tags=["parcels"])


def _inside_bbox(geometry: dict[str, Any], bbox: tuple[float, float, float, float]) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    coordinates = geometry.get("coordinates", [])
    if not coordinates:
        return False
    rings = coordinates[0] if isinstance(coordinates[0], list) else coordinates
    for point in rings:
        if len(point) != 2:
            continue
        lon, lat = point
        if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
            return True
    return False


def _op_to_response(operation: dict[str, Any]) -> OperationResponse:
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


def _parcel_response(
    parcel: dict[str, Any],
    soils: dict[str, dict[str, Any]],
    crops: dict[str, dict[str, Any]],
    operations: list[dict[str, Any]],
    status_overrides: dict[str, str],
) -> ParcelResponse:
    parcel_id = parcel["id"]
    soil_id = prop(parcel, "hasAgriSoil")
    crop_id = prop(parcel, "hasAgriCrop")

    soil = soils.get(soil_id, {}) if soil_id else {}
    crop = crops.get(crop_id, {}) if crop_id else {}

    parcel_ops = [op for op in operations if prop(op, "refParcel") == parcel_id]
    fert_ops = [op for op in parcel_ops if prop(op, "operationType") == "fertilizing"]
    fert_ops.sort(key=lambda item: prop(item, "startedAt") or "", reverse=True)

    last_fert = None
    if fert_ops:
        last_fert = LastFertilization(
            date=prop(fert_ops[0], "startedAt"),
            product=prop(fert_ops[0], "refFertilizer"),
        )

    status = status_overrides.get(parcel_id, prop(parcel, "parcelStatus", "FALLOW"))

    belongs_to = prop(parcel, "belongsTo", "")
    municipality = belongs_to.split(":")[-1] if isinstance(belongs_to, str) else None

    return ParcelResponse(
        id=parcel_id,
        name=prop(parcel, "name", parcel_id),
        area=float(prop(parcel, "area", 0.0) or 0.0),
        status=status,
        location=prop(parcel, "location", {"type": "Polygon", "coordinates": []}),
        municipality=municipality,
        currentCrop=prop(crop, "cropSpecies"),
        lastFertilization=last_fert,
        soilSummary=SoilSummary(
            pH=prop(soil, "soilPH"),
            texture=prop(soil, "soilTextureType"),
        ),
    )


@router.get("", response_model=list[ParcelResponse])
async def list_parcels(
    bbox: str | None = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    _: UserPublic = Depends(get_current_user),
    orion: OrionClient = Depends(get_orion),
    operation_store: list[dict[str, Any]] = Depends(get_operation_store),
    status_overrides: dict[str, str] = Depends(get_parcel_status_overrides),
) -> list[ParcelResponse]:
    settings_obj = get_settings()

    try:
        parcels = await orion.query_entities("AgriParcel", params={"limit": 500})
        soils = await orion.query_entities("AgriSoil", params={"limit": 200})
        crops = await orion.query_entities("AgriCrop", params={"limit": 200})
    except Exception:
        parcels = load_seed(settings_obj, "seed_parcels.json")
        soils = load_seed(settings_obj, "seed_soils.json")
        crops = load_seed(settings_obj, "seed_crops.json")

    soil_map = {item["id"]: item for item in soils}
    crop_map = {item["id"]: item for item in crops}

    bbox_tuple: tuple[float, float, float, float] | None = None
    if bbox:
        parts = [float(item.strip()) for item in bbox.split(",")]
        if len(parts) == 4:
            bbox_tuple = (parts[0], parts[1], parts[2], parts[3])

    response: list[ParcelResponse] = []
    for parcel in parcels:
        geometry = prop(parcel, "location", {})
        if bbox_tuple and not _inside_bbox(geometry, bbox_tuple):
            continue
        response.append(_parcel_response(parcel, soil_map, crop_map, operation_store, status_overrides))

    return response


@router.get("/{parcel_id}", response_model=ParcelDetailResponse)
async def get_parcel(
    parcel_id: str,
    _: UserPublic = Depends(get_current_user),
    orion: OrionClient = Depends(get_orion),
    operation_store: list[dict[str, Any]] = Depends(get_operation_store),
    status_overrides: dict[str, str] = Depends(get_parcel_status_overrides),
) -> ParcelDetailResponse:
    settings_obj = get_settings()
    try:
        parcel = await orion.get_entity(parcel_id, "AgriParcel")
    except Exception:
        parcel = next((item for item in load_seed(settings_obj, "seed_parcels.json") if item["id"] == parcel_id), None)

    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    soils = {item["id"]: item for item in load_seed(settings_obj, "seed_soils.json")}
    crops = {item["id"]: item for item in load_seed(settings_obj, "seed_crops.json")}
    parcel_resp = _parcel_response(parcel, soils, crops, operation_store, status_overrides)

    parcel_ops = [op for op in operation_store if prop(op, "refParcel") == parcel_id]
    parcel_ops.sort(key=lambda item: prop(item, "startedAt") or "", reverse=True)
    last_ops = [_op_to_response(op) for op in parcel_ops[:5]]

    soil = soils.get(prop(parcel, "hasAgriSoil"), None)

    return ParcelDetailResponse(
        **parcel_resp.model_dump(),
        soil=soil,
        lastOperations=last_ops,
    )


@router.patch("/{parcel_id}", response_model=ParcelResponse)
async def patch_parcel_status(
    parcel_id: str,
    body: ParcelStatusPatch,
    _: UserPublic = Depends(require_roles(["farmer", "cooperative", "admin"])),
    orion: OrionClient = Depends(get_orion),
    operation_store: list[dict[str, Any]] = Depends(get_operation_store),
    status_overrides: dict[str, str] = Depends(get_parcel_status_overrides),
) -> ParcelResponse:
    settings_obj = get_settings()
    parcels = load_seed(settings_obj, "seed_parcels.json")
    soils = {item["id"]: item for item in load_seed(settings_obj, "seed_soils.json")}
    crops = {item["id"]: item for item in load_seed(settings_obj, "seed_crops.json")}

    parcel = next((item for item in parcels if item["id"] == parcel_id), None)
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")

    try:
        await orion.update_entity_attr(parcel_id, "parcelStatus", body.parcelStatus.value)
    except Exception:
        pass

    status_overrides[parcel_id] = body.parcelStatus.value
    return _parcel_response(parcel, soils, crops, operation_store, status_overrides)


@router.get("/{parcel_id}/geojson")
async def get_parcel_geojson(
    parcel_id: str,
    _: UserPublic = Depends(get_current_user),
    orion: OrionClient = Depends(get_orion),
) -> dict[str, Any]:
    settings_obj = get_settings()
    try:
        parcel = await orion.get_entity(parcel_id, "AgriParcel")
    except Exception:
        parcel = next((item for item in load_seed(settings_obj, "seed_parcels.json") if item["id"] == parcel_id), None)

    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    return {
        "type": "Feature",
        "id": parcel["id"],
        "geometry": prop(parcel, "location", {}),
        "properties": {
            "name": prop(parcel, "name"),
            "status": prop(parcel, "parcelStatus", "FALLOW"),
            "area": prop(parcel, "area"),
        },
    }
