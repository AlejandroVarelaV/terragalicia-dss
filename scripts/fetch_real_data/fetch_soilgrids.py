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
    fallback_seed_soils,
    get_cache_dir,
)

LOGGER = logging.getLogger("fetch_soilgrids")
SOILGRIDS_BASE_URL = "https://rest.soilgrids.org/soilgrids/v2.0"


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


def _collect_layer_values(layer: dict[str, Any], max_depth_cm: int = 30) -> list[float]:
    values: list[float] = []
    depths = layer.get("depths", [])
    if not isinstance(depths, list):
        return values

    for depth in depths:
        if not isinstance(depth, dict):
            continue
        range_obj = depth.get("range", {})
        top = int(range_obj.get("top_depth", 0))
        bottom = int(range_obj.get("bottom_depth", 0))
        if top >= max_depth_cm:
            continue
        if bottom <= 0:
            continue

        entry = depth.get("values", {})
        if not isinstance(entry, dict):
            continue
        val = entry.get("mean")
        if val is None:
            val = entry.get("Q0.5")
        values.append(_safe_float(val, 0.0))

    return values[:3]


def _avg(values: list[float], default: float = 0.0) -> float:
    return round(sum(values) / len(values), 4) if values else default


def _extract_layer_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    layers = payload.get("properties", {}).get("layers", [])
    layer_map: dict[str, dict[str, Any]] = {}
    if isinstance(layers, list):
        for layer in layers:
            if isinstance(layer, dict) and isinstance(layer.get("name"), str):
                layer_map[layer["name"]] = layer
    return layer_map


def _texture_class(clay: float, sand: float, silt: float) -> str:
    dominant = max({"clay": clay, "sand": sand, "silt": silt}, key=lambda key: {"clay": clay, "sand": sand, "silt": silt}[key])
    if dominant == "clay":
        return "clay"
    if dominant == "silt":
        return "silt-loam"
    return "sandy-loam"


async def _fetch_remote(lat: float, lon: float) -> dict[str, Any]:
    endpoint = f"{SOILGRIDS_BASE_URL}/properties/query"
    params = {
        "lon": lon,
        "lat": lat,
        "property": ["phh2o", "clay", "sand", "silt", "nitrogen", "soc"],
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        return await _get_json(client, endpoint, params)


def _fallback(lat: float, lon: float, parcel_id: str | None) -> dict[str, Any]:
    LOGGER.warning("Using seed soil fallback for SoilGrids")
    seed = fallback_seed_soils()[0] if fallback_seed_soils() else {}
    parcel_suffix = (parcel_id or "fallback").split(":")[-1]

    fallback_entity = {
        "id": f"urn:ngsi-ld:AgriSoil:soilgrids:{parcel_suffix}",
        "type": "AgriSoil",
        "soilTextureType": seed.get("soilTextureType", {"type": "Property", "value": "unknown"}),
        "soilPH": seed.get("soilPH", {"type": "Property", "value": 6.0, "unitCode": "pH"}),
        "organicMatter": seed.get("organicMatter", {"type": "Property", "value": 3.0, "unitCode": "P1"}),
        "clay": {"type": "Property", "value": 30.0, "unitCode": "P1"},
        "sand": {"type": "Property", "value": 30.0, "unitCode": "P1"},
        "silt": {"type": "Property", "value": 40.0, "unitCode": "P1"},
        "nitrogen": {"type": "Property", "value": 0.3, "unitCode": "P1"},
        "soc": {"type": "Property", "value": 2.5, "unitCode": "P1"},
        "location": {"type": "GeoProperty", "value": {"type": "Point", "coordinates": [lon, lat]}},
        "source": {"type": "Property", "value": "ISRIC SoilGrids (seed-fallback)"},
        "@context": NGSI_CONTEXT,
    }
    if parcel_id:
        fallback_entity["refParcel"] = {"type": "Relationship", "object": parcel_id}
    return fallback_entity


def fetch_soil_data(lat: float, lon: float, parcel_id: str | None = None) -> dict[str, Any]:
    """Fetch SoilGrids properties and map to an AgriSoil entity."""
    try:
        payload = asyncio.run(_fetch_remote(lat, lon))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("SoilGrids fetch failed (%s). Falling back to seed data.", exc)
        return _fallback(lat, lon, parcel_id)

    raw_cache_file = get_cache_dir() / f"soilgrids_{datetime.now(UTC).strftime('%Y%m%d')}.json"
    append_json_array(raw_cache_file, payload)

    layer_map = _extract_layer_map(payload)
    if not layer_map:
        return _fallback(lat, lon, parcel_id)

    ph_values = _collect_layer_values(layer_map.get("phh2o", {}))
    clay_values = _collect_layer_values(layer_map.get("clay", {}))
    sand_values = _collect_layer_values(layer_map.get("sand", {}))
    silt_values = _collect_layer_values(layer_map.get("silt", {}))
    nitrogen_values = _collect_layer_values(layer_map.get("nitrogen", {}))
    soc_values = _collect_layer_values(layer_map.get("soc", {}))

    ph_raw = _avg(ph_values, 55.0)
    ph = round(ph_raw / 10.0, 2) if ph_raw > 20 else round(ph_raw, 2)

    clay = _avg(clay_values, 300.0)
    sand = _avg(sand_values, 300.0)
    silt = _avg(silt_values, 400.0)
    nitrogen = _avg(nitrogen_values, 3.0)
    soc = _avg(soc_values, 20.0)

    clay_pct = round(clay / 10.0, 2)
    sand_pct = round(sand / 10.0, 2)
    silt_pct = round(silt / 10.0, 2)
    nitrogen_pct = round(nitrogen / 10.0, 4)
    soc_pct = round(soc / 10.0, 4)

    parcel_suffix = (parcel_id or f"{lat:.4f}_{lon:.4f}").replace(".", "p").replace("-", "m").replace(":", "_")
    entity: dict[str, Any] = {
        "id": f"urn:ngsi-ld:AgriSoil:soilgrids:{parcel_suffix}",
        "type": "AgriSoil",
        "soilTextureType": {
            "type": "Property",
            "value": _texture_class(clay_pct, sand_pct, silt_pct),
        },
        "soilPH": {"type": "Property", "value": ph, "unitCode": "pH"},
        "organicMatter": {"type": "Property", "value": soc_pct, "unitCode": "P1"},
        "clay": {"type": "Property", "value": clay_pct, "unitCode": "P1"},
        "sand": {"type": "Property", "value": sand_pct, "unitCode": "P1"},
        "silt": {"type": "Property", "value": silt_pct, "unitCode": "P1"},
        "nitrogen": {"type": "Property", "value": nitrogen_pct, "unitCode": "P1"},
        "soc": {"type": "Property", "value": soc_pct, "unitCode": "P1"},
        "location": {
            "type": "GeoProperty",
            "value": {"type": "Point", "coordinates": [lon, lat]},
        },
        "source": {"type": "Property", "value": "ISRIC SoilGrids v2"},
        "@context": NGSI_CONTEXT,
    }

    if parcel_id:
        entity["refParcel"] = {"type": "Relationship", "object": parcel_id}

    return entity


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Fetch SoilGrids data and map to AgriSoil NGSI-LD")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--parcel-id", type=str, default=None)
    parser.add_argument("--output", type=str, default="")
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    entity = fetch_soil_data(args.lat, args.lon, args.parcel_id)

    if args.output:
        out_path = Path(args.output)
        if args.append:
            append_json_array(out_path, entity)
        else:
            dump_json(out_path, entity)
        LOGGER.info("Wrote SoilGrids AgriSoil entity to %s", out_path)
    else:
        LOGGER.info("Fetched SoilGrids AgriSoil entity: %s", entity.get("id"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
