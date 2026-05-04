from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter

try:
    from lxml import etree

    HAS_LXML = True
except Exception:  # noqa: BLE001
    etree = None
    HAS_LXML = False

router = APIRouter(prefix="/sigpac", tags=["sigpac"])
LOGGER = logging.getLogger("sigpac_api")

SIGPAC_ENDPOINTS = [
    "https://www.fega.gob.es/PwfGeoPortal/",
    "https://mapas.xunta.gal/",
]

CACHE_TTL_SECONDS = 24 * 60 * 60
CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "cache" / "sigpac_parcels.json"

GEOMETRY_NAMES = {
    "polygon",
    "multipolygon",
    "surface",
    "multisurface",
    "curvepolygon",
    "multicurve",
    "point",
    "multipoint",
    "linestring",
    "multilinestring",
}


def _empty_feature_collection() -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": []}


def _now_epoch() -> int:
    return int(time.time())


def _cache_is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = _now_epoch() - int(path.stat().st_mtime)
    return age <= CACHE_TTL_SECONDS


def _load_cached_feature_collection(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("type") == "FeatureCollection" and isinstance(payload.get("features"), list):
            return payload
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed reading SIGPAC cache %s: %s", path, exc)
    return None


def _save_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _detect_payload_kind(content_type: str, text: str) -> str:
    ctype = (content_type or "").lower()
    preview = (text or "").strip().lower()
    if "json" in ctype or preview.startswith("{") or preview.startswith("["):
        return "geojson"
    if "xml" in ctype or preview.startswith("<"):
        if "featurecollection" in preview or "wfs:" in preview or "gml:" in preview:
            return "gml"
        return "xml"
    return "unknown"


def _parse_json_feature_collection(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None

    if isinstance(payload, dict) and payload.get("type") == "FeatureCollection" and isinstance(payload.get("features"), list):
        return payload
    return None


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_pairwise(values: list[float], dimension: int = 2) -> list[list[float]]:
    if dimension < 2:
        dimension = 2
    pairs: list[list[float]] = []
    for idx in range(0, len(values), dimension):
        block = values[idx : idx + dimension]
        if len(block) < 2:
            continue
        pairs.append([block[0], block[1]])
    return pairs


def _parse_ring_from_poslist(ring: Any) -> list[list[float]]:
    pos_list = ring.xpath(".//*[local-name()='posList']")
    if not pos_list:
        return []

    raw = " ".join((pos_list[0].text or "").split())
    if not raw:
        return []

    dim_attr = pos_list[0].attrib.get("srsDimension") or ring.attrib.get("srsDimension")
    dim = int(dim_attr) if dim_attr and dim_attr.isdigit() else 2

    values = [_to_float(x) for x in raw.split(" ")]
    clean = [x for x in values if x is not None]
    return _parse_pairwise(clean, dim)


def _parse_ring_from_pos_nodes(ring: Any) -> list[list[float]]:
    pos_nodes = ring.xpath(".//*[local-name()='pos']/text()")
    coords: list[list[float]] = []
    for text in pos_nodes:
        nums = [_to_float(x) for x in text.replace(",", " ").split()]
        clean = [x for x in nums if x is not None]
        if len(clean) >= 2:
            coords.append([clean[0], clean[1]])
    return coords


def _parse_ring_from_coordinates(ring: Any) -> list[list[float]]:
    coordinate_nodes = ring.xpath(".//*[local-name()='coordinates']/text()")
    if not coordinate_nodes:
        return []

    coords: list[list[float]] = []
    for node_text in coordinate_nodes:
        pairs = node_text.strip().split()
        for pair in pairs:
            pair = pair.replace(",", " ")
            nums = [_to_float(x) for x in pair.split()]
            clean = [x for x in nums if x is not None]
            if len(clean) >= 2:
                coords.append([clean[0], clean[1]])
    return coords


def _ensure_closed_ring(coords: list[list[float]]) -> list[list[float]]:
    if len(coords) < 3:
        return coords
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return coords


def _parse_linear_ring(ring: Any) -> list[list[float]]:
    coords = _parse_ring_from_poslist(ring)
    if not coords:
        coords = _parse_ring_from_pos_nodes(ring)
    if not coords:
        coords = _parse_ring_from_coordinates(ring)
    return _ensure_closed_ring(coords)


def _parse_polygon(polygon: Any) -> list[list[list[float]]] | None:
    exterior_rings = polygon.xpath(
        ".//*[local-name()='exterior' or local-name()='outerBoundaryIs']//*[local-name()='LinearRing']"
    )
    if not exterior_rings:
        fallback_rings = polygon.xpath(".//*[local-name()='LinearRing']")
        exterior_rings = fallback_rings[:1]

    if not exterior_rings:
        return None

    exterior = _parse_linear_ring(exterior_rings[0])
    if len(exterior) < 4:
        return None

    interiors: list[list[list[float]]] = []
    inner_rings = polygon.xpath(
        ".//*[local-name()='interior' or local-name()='innerBoundaryIs']//*[local-name()='LinearRing']"
    )
    for ring in inner_rings:
        parsed = _parse_linear_ring(ring)
        if len(parsed) >= 4:
            interiors.append(parsed)

    return [exterior, *interiors]


def _extract_geometry(feature: Any) -> dict[str, Any] | None:
    multi_polygons = feature.xpath(".//*[local-name()='MultiPolygon' or local-name()='MultiSurface']")
    if multi_polygons:
        polygons = multi_polygons[0].xpath(".//*[local-name()='Polygon' or local-name()='Surface']")
        parts: list[list[list[list[float]]]] = []
        for poly in polygons:
            parsed = _parse_polygon(poly)
            if parsed:
                parts.append(parsed)
        if parts:
            if len(parts) == 1:
                return {"type": "Polygon", "coordinates": parts[0]}
            return {"type": "MultiPolygon", "coordinates": parts}

    polygons = feature.xpath(".//*[local-name()='Polygon' or local-name()='Surface']")
    for poly in polygons:
        parsed = _parse_polygon(poly)
        if parsed:
            return {"type": "Polygon", "coordinates": parsed}

    return None


def _is_geometry_property(node: Any) -> bool:
    local = etree.QName(node).localname.lower()
    if local in GEOMETRY_NAMES:
        return True
    descendants = node.xpath(".//*[local-name()='Polygon' or local-name()='MultiPolygon' or local-name()='Surface' or local-name()='MultiSurface']")
    return len(descendants) > 0


def _extract_properties(feature: Any) -> dict[str, Any]:
    properties: dict[str, Any] = {}

    for child in feature:
        if not isinstance(child.tag, str):
            continue
        if _is_geometry_property(child):
            continue

        key = etree.QName(child).localname
        if len(child) == 0:
            value = (child.text or "").strip()
        else:
            value = " ".join(" ".join(child.itertext()).split())

        if not value:
            continue
        properties[key] = value

    return properties


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
