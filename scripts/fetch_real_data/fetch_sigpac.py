from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from . import append_json_array, configure_logging, dump_json, fallback_seed_parcels, get_cache_dir

LOGGER = logging.getLogger("fetch_sigpac")
SIGPAC_ENDPOINTS = [
    "https://www.fega.gob.es/PwfGeoPortal/",
    "https://mapas.xunta.gal/",
]


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
    if isinstance(payload, dict):
        return payload
    return {"type": "FeatureCollection", "features": []}


def _seed_feature_collection(municipio_code: str) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for parcel in fallback_seed_parcels():
        location = parcel.get("location", {}).get("value", {})
        if not isinstance(location, dict):
            continue
        if location.get("type") != "Polygon":
            continue

        features.append(
            {
                "type": "Feature",
                "geometry": location,
                "properties": {
                    "id": parcel.get("id"),
                    "name": parcel.get("name", {}).get("value"),
                    "category": parcel.get("category", {}).get("value"),
                    "provincia": "15",
                    "municipio": municipio_code,
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


async def _fetch_sigpac_remote(municipio_code: str) -> dict[str, Any]:
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "SIGPAC:recinto",
        "outputFormat": "application/json",
        "CQL_FILTER": f"PROVINCIA='15' AND MUNICIPIO='{municipio_code}'",
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        for endpoint in SIGPAC_ENDPOINTS:
            try:
                payload = await _get_json(client, endpoint, params)
                if payload.get("type") == "FeatureCollection":
                    return payload
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("SIGPAC endpoint failed (%s): %s", endpoint, exc)

    raise httpx.RequestError("No SIGPAC endpoint returned valid GeoJSON")


def fetch_sigpac_parcels(municipio_code: str) -> dict[str, Any]:
    """Fetch SIGPAC parcel polygons for A Coruña province (PROVINCIA:15)."""
    try:
        payload = asyncio.run(_fetch_sigpac_remote(municipio_code))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("SIGPAC fetch failed (%s). Falling back to seed parcels.", exc)
        payload = _seed_feature_collection(municipio_code)

    cache_file = get_cache_dir() / f"sigpac_{municipio_code}_{datetime.now(UTC).strftime('%Y%m%d')}.json"
    append_json_array(cache_file, payload)
    return payload


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Fetch SIGPAC WFS parcels as GeoJSON FeatureCollection")
    parser.add_argument("--municipio-code", type=str, required=True)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    result = fetch_sigpac_parcels(args.municipio_code)

    if args.output:
        out = Path(args.output)
        dump_json(out, result)
        LOGGER.info("Wrote SIGPAC FeatureCollection to %s", out)
    else:
        LOGGER.info("Fetched %d SIGPAC features", len(result.get("features", [])))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
