from __future__ import annotations

import logging
from typing import Any, Tuple

import httpx
from fastapi import HTTPException

from config import get_settings

LOGGER = logging.getLogger(__name__)


def _bbox_to_key(bbox: Tuple[float, float, float, float]) -> str:
    return f"sigpac:bbox:{bbox[0]}:{bbox[1]}:{bbox[2]}:{bbox[3]}"


async def fetch_parcels_by_bbox(bbox: Tuple[float, float, float, float], redis_cache=None) -> dict[str, Any]:
    """Fetch parcel FeatureCollection for given bbox.

    Tries Catastro INSPIRE WFS first, then SIGPAC WFS.
    Caches results in Redis for 24h when redis_cache is provided.
    Raises HTTPException(503) if both sources fail.
    """
    settings = get_settings()
    key = _bbox_to_key(bbox)
    if redis_cache is not None:
        cached = await redis_cache.get_json(key)
        if cached:
            LOGGER.info("Serving parcels from Redis cache key=%s", key)
            return cached

    minx, miny, maxx, maxy = bbox
    # Try Catastro INSPIRE WFS
    try:
        params = {
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAME": "CP:CadastralParcel",
            "OUTPUTFORMAT": "application/json",
            "BBOX": f"{minx},{miny},{maxx},{maxy},EPSG:4326",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(settings.catastro_wfs_url.rstrip('/'), params=params)
            resp.raise_for_status()
            payload = resp.json()
            if isinstance(payload, dict) and payload.get("features"):
                # normalize properties
                for f in payload.get("features", []):
                    props = f.setdefault("properties", {})
                    props.setdefault("source", "catastro")
                if redis_cache is not None:
                    await redis_cache.set_json(key, payload, 86400)
                LOGGER.info("Using catastro source for bbox=%s", bbox)
                return payload
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Catastro WFS failed: %s", exc)

    # Try SIGPAC WFS
    try:
        sigpac_url = settings.sigpac_wfs_url
        params = {
            "SERVICE": "WFS",
            "VERSION": "1.1.0",
            "REQUEST": "GetFeature",
            "TYPENAME": "sigpac:parcela",
            "BBOX": f"{minx},{miny},{maxx},{maxy}",
            "SRSNAME": "EPSG:4326",
            "MAXFEATURES": "500",
            "outputFormat": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(sigpac_url, params=params)
            resp.raise_for_status()
            payload = resp.json()
            if isinstance(payload, dict) and payload.get("features"):
                for f in payload.get("features", []):
                    props = f.setdefault("properties", {})
                    props.setdefault("source", "sigpac")
                if redis_cache is not None:
                    await redis_cache.set_json(key, payload, 86400)
                LOGGER.info("Using sigpac source for bbox=%s", bbox)
                return payload
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("SIGPAC WFS failed: %s", exc)

    raise HTTPException(status_code=503, detail="Parcel geometry service unavailable. No fallback to synthetic data.")


async def fetch_parcel_by_reference(provincia: str, municipio: str, poligono: str, parcela: str, redis_cache=None) -> dict[str, Any] | None:
    """Attempt to fetch single parcel by cadastral reference or by SIGPAC identifiers.

    Returns GeoJSON Feature or None.
    """
    settings = get_settings()
    ref_key = f"sigpac:ref:{provincia}:{municipio}:{poligono}:{parcela}"
    if redis_cache is not None:
        cached = await redis_cache.get_json(ref_key)
        if cached:
            LOGGER.info("Serving parcel from Redis cache key=%s", ref_key)
            return cached

    # Try Catastro by filtering using a bbox around the parcel if possible
    try:
        # best-effort: query Catastro for the municipio bbox
        # This is a lightweight attempt; if not found, return None
        params = {
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAME": "CP:CadastralParcel",
            "OUTPUTFORMAT": "application/json",
            # No standardized query by reference across providers; try to fetch municipality
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(settings.catastro_wfs_url.rstrip('/'), params=params)
            resp.raise_for_status()
            payload = resp.json()
            for f in payload.get("features", []):
                props = f.get("properties", {})
                ref = props.get("REFERENCE") or props.get("referenciaCatastral") or props.get("REF")
                if ref and parcela in str(ref):
                    props.setdefault("source", "catastro")
                    if redis_cache is not None:
                        await redis_cache.set_json(ref_key, f, 86400)
                    LOGGER.info("Found parcel by reference in Catastro: %s", ref_key)
                    return f
    except Exception:
        LOGGER.debug("Catastro lookup by reference failed")

    # Try SIGPAC by municipio/poligono/parcela via WFS filtering (best-effort)
    try:
        params = {
            "SERVICE": "WFS",
            "VERSION": "1.1.0",
            "REQUEST": "GetFeature",
            "TYPENAME": "sigpac:parcela",
            "CQL_FILTER": f"PROVINCIA='{provincia}' AND MUNICIPIO='{municipio}' AND POLIGONO='{poligono}' AND PARCELA='{parcela}'",
            "outputFormat": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(settings.sigpac_wfs_url, params=params)
            resp.raise_for_status()
            payload = resp.json()
            features = payload.get("features", [])
            if features:
                f = features[0]
                f.setdefault("properties", {}).setdefault("source", "sigpac")
                if redis_cache is not None:
                    await redis_cache.set_json(ref_key, f, 86400)
                LOGGER.info("Found parcel by reference in SIGPAC: %s", ref_key)
                return f
    except Exception:
        LOGGER.debug("SIGPAC lookup by reference failed")

    return None
