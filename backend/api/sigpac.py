from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query

from api.deps import get_redis_cache
from services.sigpac import fetch_parcels_by_bbox, _fetch_from_postgis, _fetch_from_gpkg

router = APIRouter(prefix="/sigpac", tags=["sigpac"])
LOGGER = logging.getLogger(__name__)


@router.get("/parcels")
async def get_sigpac_parcels(
    bbox: str | None = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    force_refresh: bool = False,
    zoom: int | None = Query(default=None, description="Map zoom level"),
    limit: int = Query(default=5000, ge=1),
    redis=Depends(get_redis_cache),
) -> dict[str, Any]:
    """Return parcels for a bbox using the service fallback chain: WFS -> .gpkg files -> mock data."""
    if zoom is not None and zoom < 14:
        LOGGER.info("Zoom level too low (%d); returning empty features", zoom)
        return {"type": "FeatureCollection", "features": [], "zoom_too_low": True,
                "truncated": False, "total_estimate": 0, "returned": 0}

    if bbox:
        parts = [float(part.strip()) for part in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must be minLon,minLat,maxLon,maxLat")
        bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
    else:
        bbox_tuple = (-8.8, 43.0, -7.9, 43.5)

    if force_refresh:
        LOGGER.info("Force refresh requested for SIGPAC parcels")

    effective_zoom = zoom if zoom is not None else 18
    result = await fetch_parcels_by_bbox(bbox_tuple, zoom=effective_zoom, limit=limit, redis_cache=redis)

    features = result.get("features", [])
    return {
        "type": "FeatureCollection",
        "features": features,
        "truncated": result.get("truncated", False),
        "total_estimate": result.get("total_estimate", len(features)),
        "returned": result.get("returned", len(features)),
    }


@router.get("/nearby")
async def get_sigpac_nearby(
    lat: float = Query(..., description="Latitude of cursor"),
    lon: float = Query(..., description="Longitude of cursor"),
    zoom: int = Query(default=18, description="Map zoom level"),
    limit: int = Query(default=50, description="Maximum number of features to return"),
) -> dict[str, Any]:
    """Return parcels near the cursor coordinates at the given zoom level."""
    # Zoom validation: return empty features if zoom is too low
    if zoom < 14:
        LOGGER.info("Zoom level too low (%d); returning empty features", zoom)
        return {"type": "FeatureCollection", "features": []}
    
    # Determine delta based on zoom level (expanded areas)
    if zoom >= 18:
        delta = 0.015
    elif zoom >= 16:
        delta = 0.025
    else:  # zoom >= 14
        delta = 0.04
    
    # Build bbox around cursor
    bbox = (lon - delta, lat - delta, lon + delta, lat + delta)
    
    # Try PostGIS first
    result = await _fetch_from_postgis(bbox, limit=limit)
    if result and result.get("features"):
        features = result.get("features", [])[:limit]
        return {"type": "FeatureCollection", "features": features}
    
    # Fall back to .gpkg files
    result = await _fetch_from_gpkg(bbox, zoom=zoom)
    
    # Handle empty or missing result
    if result is None or not result.get("features"):
        return {"type": "FeatureCollection", "features": []}
    
    # Limit features to requested count
    features = result.get("features", [])[:limit]
    
    return {"type": "FeatureCollection", "features": features}
