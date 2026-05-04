from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from . import (
    NGSI_CONTEXT,
    append_json_array,
    configure_logging,
    dump_json,
    fallback_seed_weather_forecast,
    get_cache_dir,
    utc_now_iso,
)

LOGGER = logging.getLogger("fetch_meteogalicia")
METEOGALICIA_BASE_URL = "https://servizos.meteogalicia.gal/apiv4"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True,
)
async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = await client.get(url, params=params)
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {"data": payload}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _forecast_to_entity(
    item: dict[str, Any],
    lat: float,
    lon: float,
    parcel_id: str | None,
    source: str,
) -> dict[str, Any]:
    date_key = str(item.get("data") or item.get("date") or utc_now_iso())
    valid_from = f"{date_key[:10]}T00:00:00Z"
    valid_to = f"{date_key[:10]}T23:59:59Z"

    tmax = _safe_float(item.get("tMax"), 0.0)
    tmin = _safe_float(item.get("tMin"), 0.0)
    tavg = (tmax + tmin) / 2.0

    precip = _safe_float(item.get("precipitacion"), 0.0)
    wind = _safe_float(item.get("velvento"), 0.0)

    point_tag = f"{lat:.4f}_{lon:.4f}".replace("-", "m").replace(".", "p")
    entity_id = f"urn:ngsi-ld:WeatherForecast:meteogalicia:{point_tag}:{valid_from}"
    entity: dict[str, Any] = {
        "id": entity_id,
        "type": "WeatherForecast",
        "issuedAt": {"type": "Property", "value": utc_now_iso()},
        "validFrom": {"type": "Property", "value": valid_from},
        "validTo": {"type": "Property", "value": valid_to},
        "location": {
            "type": "GeoProperty",
            "value": {"type": "Point", "coordinates": [lon, lat]},
        },
        "temperature": {"type": "Property", "value": round(tavg, 2), "unitCode": "DEG_C"},
        "temperatureMin": {"type": "Property", "value": tmin, "unitCode": "DEG_C"},
        "temperatureMax": {"type": "Property", "value": tmax, "unitCode": "DEG_C"},
        "precipitation": {"type": "Property", "value": precip, "unitCode": "MM"},
        "windSpeed": {"type": "Property", "value": wind, "unitCode": "MTS"},
        "source": {"type": "Property", "value": source},
        "@context": NGSI_CONTEXT,
    }
    if parcel_id:
        entity["refParcel"] = {"type": "Relationship", "object": parcel_id}
    return entity


def _extract_forecast_days(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_keys = [
        "predicion",
        "prediccion",
        "forecast",
        "dailyForecast",
        "days",
        "data",
    ]

    for key in candidate_keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [v for v in value if isinstance(v, dict)]
        if isinstance(value, dict):
            nested = value.get("dias") or value.get("days") or value.get("data")
            if isinstance(nested, list):
                return [v for v in nested if isinstance(v, dict)]

    return []


async def _fetch_remote(lat: float, lon: float) -> dict[str, Any]:
    endpoint = f"{METEOGALICIA_BASE_URL}/predicion/point"
    params = {"lat": lat, "lon": lon, "days": 7}
    async with httpx.AsyncClient(timeout=30.0) as client:
        return await _get_json(client, endpoint, params)


def _fallback(lat: float, lon: float, parcel_id: str | None) -> list[dict[str, Any]]:
    LOGGER.warning("Using seed weather forecast fallback for MeteoGalicia")
    out: list[dict[str, Any]] = []
    for seed in fallback_seed_weather_forecast():
        valid_from = seed.get("validFrom", {}).get("value", utc_now_iso())
        entity = {
            "id": f"urn:ngsi-ld:WeatherForecast:meteogalicia:fallback:{valid_from}",
            "type": "WeatherForecast",
            "issuedAt": seed.get("issuedAt", {"type": "Property", "value": utc_now_iso()}),
            "validFrom": {"type": "Property", "value": valid_from},
            "validTo": seed.get("validTo", {"type": "Property", "value": valid_from}),
            "location": {
                "type": "GeoProperty",
                "value": {"type": "Point", "coordinates": [lon, lat]},
            },
            "temperature": {
                "type": "Property",
                "value": round(
                    (_safe_float(seed.get("temperatureMax", {}).get("value")) + _safe_float(seed.get("temperatureMin", {}).get("value")))
                    / 2.0,
                    2,
                ),
                "unitCode": "DEG_C",
            },
            "temperatureMin": seed.get("temperatureMin", {"type": "Property", "value": 0.0, "unitCode": "DEG_C"}),
            "temperatureMax": seed.get("temperatureMax", {"type": "Property", "value": 0.0, "unitCode": "DEG_C"}),
            "precipitation": seed.get("precipitation", {"type": "Property", "value": 0.0, "unitCode": "MM"}),
            "windSpeed": seed.get("windSpeed", {"type": "Property", "value": 0.0, "unitCode": "MTS"}),
            "source": {"type": "Property", "value": "MeteoGalicia (seed-fallback)"},
            "@context": NGSI_CONTEXT,
        }
        if parcel_id:
            entity["refParcel"] = {"type": "Relationship", "object": parcel_id}
        out.append(entity)
    return out


def fetch_meteogalicia_forecast(lat: float, lon: float, parcel_id: str | None = None) -> list[dict[str, Any]]:
    """Fetch 7-day forecast from MeteoGalicia and map to WeatherForecast entities."""
    try:
        payload = asyncio.run(_fetch_remote(lat, lon))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("MeteoGalicia fetch failed (%s). Falling back to seed data.", exc)
        return _fallback(lat, lon, parcel_id)

    raw_cache_file = get_cache_dir() / f"meteogalicia_{datetime.now(UTC).strftime('%Y%m%d')}.json"
    append_json_array(raw_cache_file, payload)

    days = _extract_forecast_days(payload)
    mapped = [_forecast_to_entity(day, lat, lon, parcel_id, "MeteoGalicia") for day in days]
    if not mapped:
        LOGGER.warning("MeteoGalicia payload could not be mapped, using fallback")
        return _fallback(lat, lon, parcel_id)

    return mapped


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Fetch MeteoGalicia forecast and map to NGSI-LD")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--parcel-id", type=str, default=None)
    parser.add_argument("--output", type=str, default="")
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    entities = fetch_meteogalicia_forecast(args.lat, args.lon, args.parcel_id)

    if args.output:
        output = Path(args.output)
        if args.append:
            append_json_array(output, entities)
        else:
            dump_json(output, entities)
        LOGGER.info("Wrote %d MeteoGalicia entities to %s", len(entities), output)
    else:
        LOGGER.info("Fetched %d MeteoGalicia entities", len(entities))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
