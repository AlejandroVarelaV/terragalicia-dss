from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user, load_seed, prop
from config import get_settings
from models.auth import UserPublic
from models.crop import CropDetailResponse, CropResponse

router = APIRouter(prefix="/crops", tags=["crops"])


@router.get("", response_model=list[CropResponse])
async def list_crops(_: UserPublic = Depends(get_current_user)) -> list[CropResponse]:
    settings_obj = get_settings()
    crops = load_seed(settings_obj, "seed_crops.json")
    return [
        CropResponse(
            id=item["id"],
            species=prop(item, "cropSpecies", "unknown"),
            waterNeedMm=prop(item, "waterNeed"),
            yieldTnHa=prop(item, "modelledYield"),
            recommendedSoilPHMin=prop(item, "recommendedSoilPHMin"),
            recommendedSoilPHMax=prop(item, "recommendedSoilPHMax"),
        )
        for item in crops
    ]


@router.get("/{crop_id}", response_model=CropDetailResponse)
async def get_crop(crop_id: str, _: UserPublic = Depends(get_current_user)) -> CropDetailResponse:
    settings_obj = get_settings()
    crop = next((item for item in load_seed(settings_obj, "seed_crops.json") if item["id"] == crop_id), None)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    planting = prop(crop, "plantingDateRange", {}) or {}
    harvest = prop(crop, "expectedHarvestDateRange", {}) or {}

    return CropDetailResponse(
        id=crop["id"],
        species=prop(crop, "cropSpecies", "unknown"),
        waterNeedMm=prop(crop, "waterNeed"),
        yieldTnHa=prop(crop, "modelledYield"),
        recommendedSoilPHMin=prop(crop, "recommendedSoilPHMin"),
        recommendedSoilPHMax=prop(crop, "recommendedSoilPHMax"),
        plantingDateStart=planting.get("start"),
        plantingDateEnd=planting.get("end"),
        harvestDateStart=harvest.get("start"),
        harvestDateEnd=harvest.get("end"),
    )
