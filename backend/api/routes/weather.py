from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_current_user, get_quantumleap, get_redis_cache, get_weather_fetcher, load_seed, prop
from config import get_settings
from db.redis_cache import RedisCache
from models.auth import UserPublic
from models.weather import WeatherBundleResponse, WeatherForecastItem, WeatherObservedResponse
from services.quantumleap import QuantumLeapClient
from services.weather_fetcher import WeatherFetcher

router = APIRouter(prefix="/weather", tags=["weather"])


def _parcel_location(parcel_id: str) -> tuple[float, float]:
    settings_obj = get_settings()
    parcel = next((item for item in load_seed(settings_obj, "seed_parcels.json") if item["id"] == parcel_id), None)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    geometry = prop(parcel, "location", {})
    coordinates = geometry.get("coordinates", [[[-8.4, 43.36]]])
    lon, lat = coordinates[0][0]
    return lat, lon


@router.get("", response_model=WeatherBundleResponse)
async def get_weather(
    parcelId: str | None = Query(None),
    lat: float | None = Query(None),
    lon: float | None = Query(None),
    _: UserPublic = Depends(get_current_user),
    cache: RedisCache = Depends(get_redis_cache),
    fetcher: WeatherFetcher = Depends(get_weather_fetcher),
) -> WeatherBundleResponse:
    settings_obj = get_settings()
    
    # Use lat/lon directly if provided, otherwise get from parcelId
    if lat is not None and lon is not None:
        cache_key = f"weather:{lat}:{lon}"
    elif parcelId:
        cache_key = f"weather:{parcelId}"
        lat, lon = _parcel_location(parcelId)
    else:
        raise HTTPException(status_code=400, detail="Either parcelId or both lat and lon must be provided")
    
    cached = await cache.get_json(cache_key)
    if cached:
        return WeatherBundleResponse(**cached)

    current_raw = await fetcher.fetch_current(lat=lat, lon=lon)
    forecast_raw = await fetcher.fetch_forecast(lat=lat, lon=lon)

    if not forecast_raw:
        forecast_raw = load_seed(settings_obj, "seed_weather_forecast.json")[:7]
    if not current_raw:
        observed = load_seed(settings_obj, "seed_weather_observed.json")
        current_raw = observed[-1] if observed else {}

    current = WeatherObservedResponse(
        dateObserved=prop(current_raw, "dateObserved", current_raw.get("dateObserved")),
        temperature=prop(current_raw, "temperature", current_raw.get("temperature")),
        relativeHumidity=prop(current_raw, "relativeHumidity", current_raw.get("relativeHumidity")),
        precipitation=prop(current_raw, "precipitation", current_raw.get("precipitation")),
        windSpeed=prop(current_raw, "windSpeed", current_raw.get("windSpeed")),
    )

    forecast = [
        WeatherForecastItem(
            validFrom=prop(item, "validFrom", item.get("date")),
            validTo=prop(item, "validTo"),
            temperatureMin=prop(item, "temperatureMin", item.get("temperature")),
            temperatureMax=prop(item, "temperatureMax", item.get("temperature")),
            precipitation=prop(item, "precipitation"),
            frostRisk=prop(item, "frostRisk"),
        )
        for item in forecast_raw[:7]
    ]

    bundle = WeatherBundleResponse(current=current, forecast=forecast)
    await cache.set_json(cache_key, bundle.model_dump(), settings_obj.weather_cache_ttl_seconds)
    return bundle


@router.get("/history")
async def get_weather_history(
    parcelId: str,
    from_date: datetime = Query(alias="from"),
    to_date: datetime = Query(alias="to"),
    _: UserPublic = Depends(get_current_user),
    ql: QuantumLeapClient = Depends(get_quantumleap),
) -> dict[str, Any]:
    settings_obj = get_settings()
    parcel = next((item for item in load_seed(settings_obj, "seed_parcels.json") if item["id"] == parcelId), None)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    weather_entity = "urn:ngsi-ld:WeatherObserved:station:acoruna:15030:current"

    try:
        history = await ql.get_entity_history(
            entity_id=weather_entity,
            attr="temperature",
            from_date=from_date,
            to_date=to_date,
        )
        if history:
            return {"parcelId": parcelId, "series": history}
    except Exception:
        pass

    observed = load_seed(settings_obj, "seed_weather_observed.json")
    series = []
    for item in observed:
        ts = prop(item, "dateObserved")
        if not ts:
            continue
        ts_dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if from_date <= ts_dt <= to_date + timedelta(days=1):
            series.append({"date": ts, "value": prop(item, "temperature")})

    return {"parcelId": parcelId, "series": series}
