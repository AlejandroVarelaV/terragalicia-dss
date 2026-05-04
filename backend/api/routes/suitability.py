from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from api.deps import (
    get_current_user,
    get_ml_client,
    get_orion,
    get_quantumleap,
    get_redis_cache,
    load_seed,
    prop,
)
from config import get_settings
from db.redis_cache import RedisCache
from models.auth import UserPublic
from models.parcel import SuitabilityResponse
from services.ml_client import MLClient
from services.orion import OrionClient
from services.quantumleap import QuantumLeapClient

router = APIRouter(prefix="/parcels", tags=["suitability"])


@router.get("/{parcel_id}/suitability", response_model=SuitabilityResponse)
async def get_suitability(
    parcel_id: str,
    _: UserPublic = Depends(get_current_user),
    orion: OrionClient = Depends(get_orion),
    ql: QuantumLeapClient = Depends(get_quantumleap),
    cache: RedisCache = Depends(get_redis_cache),
    ml_client: MLClient = Depends(get_ml_client),
) -> SuitabilityResponse:
    settings_obj = get_settings()
    cache_key = f"suitability:{parcel_id}"
    cached = await cache.get_json(cache_key)
    if cached:
        return SuitabilityResponse(**cached)

    try:
        parcel = await orion.get_entity(parcel_id, "AgriParcel")
    except Exception:
        parcel = next((item for item in load_seed(settings_obj, "seed_parcels.json") if item["id"] == parcel_id), None)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    soil_id = prop(parcel, "hasAgriSoil")
    try:
        soil = await orion.get_entity(soil_id, "AgriSoil") if soil_id else {}
    except Exception:
        soil = next((item for item in load_seed(settings_obj, "seed_soils.json") if item["id"] == soil_id), {})

    weather_cache_key = f"suitability-weather:{parcel_id}"
    weather = await cache.get_json(weather_cache_key)
    if weather is None:
        try:
            weather = await ql.get_last_n(
                entity_id="urn:ngsi-ld:WeatherObserved:station:acoruna:15030:current",
                attr="temperature",
                n=24,
            )
        except Exception:
            weather = [{"date": prop(item, "dateObserved"), "value": prop(item, "temperature")} for item in load_seed(settings_obj, "seed_weather_observed.json")[-24:]]
        await cache.set_json(weather_cache_key, weather, settings_obj.weather_cache_ttl_seconds)

    crops = load_seed(settings_obj, "seed_crops.json")
    crop_ids = [item["id"] for item in crops][:8]
    ml_payload = {
        "parcel": {
            "id": parcel_id,
            "status": prop(parcel, "parcelStatus"),
            "area": prop(parcel, "area"),
        },
        "soil": {
            "pH": prop(soil, "soilPH"),
            "texture": prop(soil, "soilTextureType"),
        },
        "weather": weather,
    }

    ranking = await ml_client.rank_crops(payload=ml_payload, crop_ids=crop_ids)
    result = SuitabilityResponse(
        parcelId=parcel_id,
        generatedAt=datetime.now(UTC).isoformat(),
        ranking=ranking,
    )
    await cache.set_json(cache_key, result.model_dump(), settings_obj.suitability_cache_ttl_seconds)
    return result
