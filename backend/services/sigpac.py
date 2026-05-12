from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Tuple

import httpx

from config import get_settings

try:
    import fiona

    HAS_FIONA = True
except ImportError:
    HAS_FIONA = False

LOGGER = logging.getLogger(__name__)


def _bbox_to_key(bbox: Tuple[float, float, float, float]) -> str:
    return f"sigpac:bbox:{bbox[0]}:{bbox[1]}:{bbox[2]}:{bbox[3]}"


async def _fetch_from_gpkg(bbox: Tuple[float, float, float, float]) -> dict[str, Any] | None:
    """Fetch parcels from local .gpkg files in Recintos_Corunha directory.
    
    Only opens .gpkg files whose spatial extent intersects with the query bbox.
    Filters by extent first, then sorts by proximity to bbox center.
    Limits results to 500 features per request and sets truncated flag if exceeded.
    """
    if not HAS_FIONA:
        LOGGER.warning("fiona not installed; skipping .gpkg fallback")
        return None

    gpkg_dir = Path(__file__).parent.parent / "Recintos_Corunha"
    if not gpkg_dir.exists():
        LOGGER.warning("GPKG directory not found: %s", gpkg_dir)
        return None

    gpkg_files = list(gpkg_dir.glob("*.gpkg"))
    if not gpkg_files:
        LOGGER.warning("No .gpkg files found in %s", gpkg_dir)
        return None

    minx, miny, maxx, maxy = bbox
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2
    max_features = 500
    truncated = False

    try:
        # First pass: filter by extent and calculate proximity to center
        matching_files = []
        
        for gpkg_path in gpkg_files:
            try:
                with fiona.open(gpkg_path, layer="recinto") as src:
                    file_minx, file_miny, file_maxx, file_maxy = src.bounds
                    
                    # Check intersection with query bbox
                    intersects = (file_maxx >= minx and file_minx <= maxx and
                                  file_maxy >= miny and file_miny <= maxy)
                    
                    if intersects:
                        # Calculate distance from file center to bbox center
                        fc_x = (file_minx + file_maxx) / 2
                        fc_y = (file_miny + file_maxy) / 2
                        dist = ((fc_x - cx) ** 2 + (fc_y - cy) ** 2) ** 0.5
                        matching_files.append((gpkg_path, dist))
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Failed to read bounds from .gpkg file %s: %s", gpkg_path, exc)
                continue
        
        LOGGER.info("gpkg: %d archivos intersectan con bbox=%s", len(matching_files), bbox)
        
        # Sort by distance (closest first)
        matching_files.sort(key=lambda x: x[1])
        
        # Second pass: fetch features from matching files in proximity order
        features = []
        
        for gpkg_path, _ in matching_files:
            if len(features) >= max_features:
                truncated = True
                break

            try:
                # fiona.open with bbox parameter filters features spatially
                with fiona.open(gpkg_path, layer="recinto", bbox=(minx, miny, maxx, maxy)) as src:
                    for feature in src:
                        if len(features) >= max_features:
                            truncated = True
                            break

                        geom = dict(feature.geometry)
                        props = feature.properties or {}
                        geojson_feature = {
                            "type": "Feature",
                            "geometry": geom,
                            "properties": {
                                "id": props.get("dn_oid"),
                                "provincia": props.get("provincia"),
                                "municipio": props.get("municipio"),
                                "poligono": props.get("poligono"),
                                "parcela": props.get("parcela"),
                                "recinto": props.get("recinto"),
                                "area": props.get("dn_surface"),
                                "landUse": props.get("uso_sigpac"),
                                "slope": props.get("pendiente_media"),
                                "source": "gpkg-local",
                            },
                        }
                        features.append(geojson_feature)
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Failed to read .gpkg file %s: %s", gpkg_path, exc)
                continue

        if not features:
            return None

        result = {"type": "FeatureCollection", "features": features}
        if truncated:
            result["truncated"] = True
        return result
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Error during .gpkg fetch: %s", exc)
        return None


def _get_mock_parcels(bbox: Tuple[float, float, float, float]) -> dict[str, Any]:
    """Generate 5 mock parcel features for fallback when no real data is available."""
    minx, miny, maxx, maxy = bbox
    width = maxx - minx
    features = []

    for i in range(5):
        # Divide bbox into 5 horizontal strips, place one polygon per strip
        x_center = minx + (width / 5) * (i + 0.5)
        y_center = (miny + maxy) / 2

        # 0.001 degree square polygon around center
        offset = 0.0005
        coords = [
            [
                [x_center - offset, y_center - offset],
                [x_center + offset, y_center - offset],
                [x_center + offset, y_center + offset],
                [x_center - offset, y_center + offset],
                [x_center - offset, y_center - offset],
            ]
        ]

        feature = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": coords},
            "properties": {
                "id": f"mock-{i}",
                "area": 0.5,
                "landUse": "arable",
                "source": "mock",
                "status": "FALLOW",
                "provincia": "15",
            },
        }
        features.append(feature)

    return {"type": "FeatureCollection", "features": features}


async def fetch_parcels_by_bbox(bbox: Tuple[float, float, float, float], redis_cache=None) -> dict[str, Any]:
    """Fetch parcel FeatureCollection for given bbox.

    Tries local .gpkg files first, then fallback to mock data.
    Caches results in Redis for 24h when redis_cache is provided.
    """
    settings = get_settings()
    key = _bbox_to_key(bbox)
    if redis_cache is not None:
        cached = await redis_cache.get_json(key)
        if cached:
            LOGGER.info("Serving parcels from Redis cache key=%s", key)
            return cached

    minx, miny, maxx, maxy = bbox
    
    # WFS_DISABLED: Try Catastro INSPIRE WFS
    # try:
    #     params = {
    #         "SERVICE": "WFS",
    #         "VERSION": "2.0.0",
    #         "REQUEST": "GetFeature",
    #         "TYPENAME": "CP:CadastralParcel",
    #         "OUTPUTFORMAT": "application/json",
    #         "BBOX": f"{minx},{miny},{maxx},{maxy},EPSG:4326",
    #     }
    #     async with httpx.AsyncClient(timeout=60.0) as client:
    #         resp = await client.get(settings.catastro_wfs_url.rstrip('/'), params=params)
    #         resp.raise_for_status()
    #         payload = resp.json()
    #         if isinstance(payload, dict) and payload.get("features"):
    #             # normalize properties
    #             for f in payload.get("features", []):
    #                 props = f.setdefault("properties", {})
    #                 props.setdefault("source", "catastro")
    #             if redis_cache is not None:
    #                 await redis_cache.set_json(key, payload, 86400)
    #             LOGGER.info("Using catastro source for bbox=%s", bbox)
    #             return payload
    # except Exception as exc:  # noqa: BLE001
    #     LOGGER.warning("Catastro WFS failed: %s", exc)

    # WFS_DISABLED: Try SIGPAC WFS
    # try:
    #     sigpac_url = settings.sigpac_wfs_url
    #     params = {
    #         "SERVICE": "WFS",
    #         "VERSION": "1.1.0",
    #         "REQUEST": "GetFeature",
    #         "TYPENAME": "sigpac:parcela",
    #         "BBOX": f"{minx},{miny},{maxx},{maxy}",
    #         "SRSNAME": "EPSG:4326",
    #         "MAXFEATURES": "500",
    #         "outputFormat": "application/json",
    #     }
    #     async with httpx.AsyncClient(timeout=60.0) as client:
    #         resp = await client.get(sigpac_url, params=params)
    #         resp.raise_for_status()
    #         payload = resp.json()
    #         if isinstance(payload, dict) and payload.get("features"):
    #             for f in payload.get("features", []):
    #                 props = f.setdefault("properties", {})
    #                 props.setdefault("source", "sigpac")
    #             if redis_cache is not None:
    #                 await redis_cache.set_json(key, payload, 86400)
    #             LOGGER.info("Using sigpac source for bbox=%s", bbox)
    #             return payload
    # except Exception as exc:  # noqa: BLE001
    #     LOGGER.warning("SIGPAC WFS failed: %s", exc)

    # Try .gpkg local files (FIRST)
    gpkg_result = await _fetch_from_gpkg(bbox)
    if gpkg_result and gpkg_result.get("features"):
        LOGGER.info("Using gpkg-local source for bbox=%s", bbox)
        if redis_cache is not None:
            await redis_cache.set_json(key, gpkg_result, 86400)
        return gpkg_result

    # Fall back to mock data (LAST)
    mock_result = _get_mock_parcels(bbox)
    LOGGER.warning("Using mock data for bbox=%s", bbox)
    if redis_cache is not None:
        await redis_cache.set_json(key, mock_result, 3600)
    return mock_result


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
