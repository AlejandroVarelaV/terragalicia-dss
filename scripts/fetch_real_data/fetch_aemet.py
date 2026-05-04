from __future__ import annotations

import argparse
import asyncio
import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from . import (
    NGSI_CONTEXT,
    append_json_array,
    configure_logging,
    fallback_seed_weather_forecast,
    get_cache_dir,
    utc_now_iso,
)

LOGGER = logging.getLogger("fetch_aemet")
AEMET_BASE_URL = "https://opendata.aemet.es/opendata/api"
AEMET_STATIONS = ("1387", "1387E")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True,
)
async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await client.get(url, params=params)
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {"data": payload}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _map_aemet_day(day: dict[str, Any], lat: float, lon: float, issued_at: str, source_station: str) -> dict[str, Any]:
    date_text = day.get("fecha") or utc_now_iso()
    valid_from = f"{date_text[:10]}T00:00:00Z"
    valid_to = f"{date_text[:10]}T23:59:59Z"

    temp = day.get("temperatura", {}) if isinstance(day.get("temperatura"), dict) else {}
    rain_prob = day.get("probPrecipitacion", [])

    pop_values = []
    if isinstance(rain_prob, list):
        for item in rain_prob:
            if isinstance(item, dict):
                pop_values.append(_as_float(item.get("value"), 0.0))
            else:
                pop_values.append(_as_float(item, 0.0))

    precip_probability = max(pop_values) if pop_values else 0.0
    tmin = _as_float(temp.get("minima"), 0.0)
    tmax = _as_float(temp.get("maxima"), 0.0)
    wind = _as_float(day.get("viento", [{}])[0].get("velocidad") if isinstance(day.get("viento"), list) and day.get("viento") else 0.0)
    rain = _as_float(day.get("precipitacion"), 0.0)

    entity_id = f"urn:ngsi-ld:WeatherForecast:aemet:{source_station}:{valid_from}"

    return {
        "id": entity_id,
        "type": "WeatherForecast",
        "issuedAt": {"type": "Property", "value": issued_at},
        "validFrom": {"type": "Property", "value": valid_from},
        "validTo": {"type": "Property", "value": valid_to},
        "location": {
            "type": "GeoProperty",
            "value": {"type": "Point", "coordinates": [lon, lat]},
        },
        "temperatureMin": {"type": "Property", "value": tmin, "unitCode": "DEG_C"},
        "temperatureMax": {"type": "Property", "value": tmax, "unitCode": "DEG_C"},
        "precipitationProbability": {
            "type": "Property",
            "value": min(100.0, max(0.0, precip_probability)),
            "unitCode": "P1",
        },
        "precipitation": {"type": "Property", "value": rain, "unitCode": "MM"},
        "windSpeed": {"type": "Property", "value": wind, "unitCode": "MTS"},
        "sourceStation": {"type": "Property", "value": source_station},
        "@context": NGSI_CONTEXT,
    }


async def _fetch_aemet_raw(lat: float, lon: float, api_key: str) -> list[dict[str, Any]]:
    params = {"api_key": api_key}
    endpoint = f"{AEMET_BASE_URL}/prediccion/especifica/punto/{lat},{lon}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        metadata = await _get_json(client, endpoint, params=params)
        data_url = metadata.get("datos")
        if not data_url:
            raise RuntimeError("AEMET metadata missing 'datos' URL")

        response = await client.get(str(data_url))
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            return [payload]
        return []


def _fallback_forecast(lat: float, lon: float) -> list[dict[str, Any]]:
    LOGGER.warning("Using seed weather forecast fallback for AEMET")
    fallback = fallback_seed_weather_forecast()
    out: list[dict[str, Any]] = []
    for item in fallback:
        entity = dict(item)
        entity["id"] = str(entity.get("id", "urn:ngsi-ld:WeatherForecast:aemet:fallback")).replace(
            "urn:ngsi-ld:WeatherForecast:", "urn:ngsi-ld:WeatherForecast:aemet:fallback:"
        )
        entity["location"] = {
            "type": "GeoProperty",
            "value": {"type": "Point", "coordinates": [lon, lat]},
        }
        out.append(entity)
    return out


def fetch_aemet_forecast(lat: float, lon: float) -> list[dict[str, Any]]:
    """Fetch AEMET forecast and map it to WeatherForecast NGSI-LD entities."""
    api_key = os.getenv("AEMET_API_KEY")
    if not api_key:
        LOGGER.warning("AEMET_API_KEY not set, falling back to seed data")
        return _fallback_forecast(lat, lon)

    cache_file = get_cache_dir() / f"aemet_{datetime.now(UTC).strftime('%Y%m%d')}.json"

    try:
        payload = asyncio.run(_fetch_aemet_raw(lat, lon, api_key))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("AEMET fetch failed (%s). Falling back to seed data.", exc)
        return _fallback_forecast(lat, lon)

    append_json_array(cache_file, payload)

    issued_at = utc_now_iso()
    mapped: list[dict[str, Any]] = []
    station = AEMET_STATIONS[0]
    for chunk in payload:
        prediction = chunk.get("prediccion", {}) if isinstance(chunk, dict) else {}
        daily = prediction.get("dia", []) if isinstance(prediction, dict) else []
        for day in daily:
            if isinstance(day, dict):
                mapped.append(_map_aemet_day(day, lat, lon, issued_at, station))

    if not mapped:
        LOGGER.warning("AEMET payload had no daily forecast entries, using fallback")
        return _fallback_forecast(lat, lon)

    return mapped


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Fetch AEMET daily forecast and map to NGSI-LD")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--output", type=str, default="")
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    entities = fetch_aemet_forecast(args.lat, args.lon)

    if args.output:
        from pathlib import Path

        out_path = Path(args.output)
        if args.append:
            append_json_array(out_path, entities)
        else:
            from . import dump_json

            dump_json(out_path, entities)
        LOGGER.info("Wrote %d AEMET entities to %s", len(entities), out_path)
    else:
        LOGGER.info("Fetched %d AEMET entities", len(entities))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
