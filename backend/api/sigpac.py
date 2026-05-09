from __future__ import annotations

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query

from api.deps import get_redis_cache
from services.sigpac import fetch_parcels_by_bbox

router = APIRouter(prefix="/sigpac", tags=["sigpac"])
LOGGER = logging.getLogger("sigpac_api")


@router.get("/parcels")
async def get_sigpac_parcels(
    bbox: str | None = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    force_refresh: bool = False,
    redis=Depends(get_redis_cache),
) -> dict[str, Any]:
    """Return parcels in GeoJSON FeatureCollection for given bbox.

    Uses Catastro INSPIRE WFS first, then SIGPAC WFS. Caches in Redis.
    """
    # default bbox for Galicia if not provided
    if bbox:
        parts = [float(p.strip()) for p in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must be minLon,minLat,maxLon,maxLat")
        bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
    else:
        # A Coruña province bbox by default
        bbox_tuple = (-9.3, 42.7, -7.4, 43.8)

    return await fetch_parcels_by_bbox(bbox_tuple, redis_cache=redis)


def _parse_gml_feature_collection(text: str) -> dict[str, Any]:
    if not HAS_LXML or etree is None:
        raise RuntimeError("lxml is required for GML to GeoJSON conversion")

    parser = etree.XMLParser(recover=True, huge_tree=True)
    root = etree.fromstring(text.encode("utf-8"), parser=parser)

    members = root.xpath("//*[local-name()='member' or local-name()='featureMember']")
    features: list[dict[str, Any]] = []

    for member in members:
        feature_nodes = [el for el in member if isinstance(el.tag, str)]
        if not feature_nodes:
            continue

        feature_node = feature_nodes[0]
        geometry = _extract_geometry(feature_node)
        if geometry is None:
            continue

        properties = _extract_properties(feature_node)
        fid = feature_node.attrib.get("{http://www.opengis.net/gml}id") or feature_node.attrib.get("id")

        features.append(
            {
                "type": "Feature",
                "id": fid,
                "geometry": geometry,
                "properties": properties,
            }
        )

    return {"type": "FeatureCollection", "features": features}


async def _fetch_wfs_payload() -> dict[str, Any]:
    requests_to_try = [
        {
            "version": "2.0.0",
            "typeNames": "SIGPAC:recinto",
            "count": "5000",
        },
        {
            "version": "1.1.0",
            "typeName": "SIGPAC:recinto",
            "maxFeatures": "5000",
        },
    ]

    filter_expr = "PROVINCIA='15'"

    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        last_error: Exception | None = None
        for endpoint in SIGPAC_ENDPOINTS:
            for request_shape in requests_to_try:
                params = {
                    "service": "WFS",
                    "request": "GetFeature",
                    "outputFormat": "application/gml+xml; version=3.2",
                    "srsName": "EPSG:4326",
                    "CQL_FILTER": filter_expr,
                }
                params.update(request_shape)

                try:
                    response = await client.get(endpoint, params=params)
                    text = response.text
                    preview = " ".join(text[:220].split())
                    kind = _detect_payload_kind(response.headers.get("content-type", ""), text)

                    LOGGER.info(
                        "SIGPAC WFS endpoint=%s status=%s payload=%s preview=%s",
                        endpoint,
                        response.status_code,
                        kind,
                        preview,
                    )

                    response.raise_for_status()

                    if kind == "geojson":
                        geo = _parse_json_feature_collection(text)
                        if geo is not None and len(geo.get("features", [])) > 0:
                            return geo
                        last_error = ValueError("GeoJSON payload was empty or invalid")
                        continue

                    geo = _parse_gml_feature_collection(text)
                    if len(geo.get("features", [])) > 0:
                        return geo

                    last_error = ValueError("GML conversion produced no features")
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    LOGGER.warning("SIGPAC fetch failed for endpoint=%s shape=%s: %s", endpoint, request_shape, exc)

        if last_error:
            raise last_error
        raise RuntimeError("SIGPAC WFS did not return any usable payload")


@router.get("/parcels")
async def get_sigpac_parcels(force_refresh: bool = False) -> dict[str, Any]:
    cached = _load_cached_feature_collection(CACHE_PATH)

    if not force_refresh and _cache_is_fresh(CACHE_PATH) and cached is not None:
        LOGGER.info("Serving SIGPAC parcels from fresh cache: %s", CACHE_PATH)
        return cached

    try:
        parcels = await _fetch_wfs_payload()
        _save_cache(CACHE_PATH, parcels)
        LOGGER.info("SIGPAC cache refreshed with %s features", len(parcels.get("features", [])))
        return parcels
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("SIGPAC live fetch failed: %s", exc)
        if cached is not None:
            LOGGER.warning("Serving SIGPAC parcels from stale cache")
            return cached

    LOGGER.warning("No SIGPAC cache available; returning empty FeatureCollection")
    return _empty_feature_collection()
