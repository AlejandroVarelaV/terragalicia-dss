from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query

from api.deps import get_redis_cache
from services.sigpac import fetch_parcels_by_bbox

router = APIRouter(prefix="/sigpac", tags=["sigpac"])
LOGGER = logging.getLogger(__name__)


@router.get("/parcels")
async def get_sigpac_parcels(
    bbox: str | None = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    force_refresh: bool = False,
    zoom: int | None = Query(default=None, description="Map zoom level"),
    redis=Depends(get_redis_cache),
) -> dict[str, Any]:
    """Return parcels for a bbox using the service fallback chain: WFS -> .gpkg files -> mock data."""
    # Zoom validation: do not fetch parcels if zoom is too low
    if zoom is not None and zoom < 14:
        LOGGER.info("Zoom level too low (%d); returning empty features", zoom)
        return {"type": "FeatureCollection", "features": [], "zoom_too_low": True}
    
    if bbox:
        parts = [float(part.strip()) for part in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must be minLon,minLat,maxLon,maxLat")
        bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
    else:
        bbox_tuple = (-8.8, 43.0, -7.9, 43.5)

    if force_refresh:
        LOGGER.info("Force refresh requested for SIGPAC parcels")

    return await fetch_parcels_by_bbox(bbox_tuple, redis_cache=redis)
