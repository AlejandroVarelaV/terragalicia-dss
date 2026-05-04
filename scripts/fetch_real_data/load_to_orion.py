from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from . import configure_logging, load_json

LOGGER = logging.getLogger("load_to_orion")
ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
LOCAL_CONTEXT = {
    "@vocab": "https://uri.fiware.org/ns/data-models/",
    "schema": "https://schema.org/",
    "id": "@id",
    "type": "@type",
    "Property": "https://uri.etsi.org/ngsi-ld/Property",
    "Relationship": "https://uri.etsi.org/ngsi-ld/Relationship",
    "GeoProperty": "https://uri.etsi.org/ngsi-ld/GeoProperty",
}


def _normalize_entity(entity: dict[str, Any]) -> dict[str, Any]:
    normalized = {k: v for k, v in entity.items() if k != "@context"}
    normalized["@context"] = LOCAL_CONTEXT
    return normalized


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True,
)
async def _post_entity(client: httpx.AsyncClient, entity: dict[str, Any]) -> httpx.Response:
    payload = _normalize_entity(entity)
    response = await client.post(
        f"{ORION_URL}/ngsi-ld/v1/entities",
        headers={"Content-Type": "application/ld+json"},
        json=payload,
    )
    return response


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True,
)
async def _patch_attrs(client: httpx.AsyncClient, entity_id: str, attrs: dict[str, Any]) -> httpx.Response:
    response = await client.patch(
        f"{ORION_URL}/ngsi-ld/v1/entities/{entity_id}/attrs",
        headers={"Content-Type": "application/ld+json"},
        json=attrs,
    )
    return response


async def _upsert_async(entity: dict[str, Any]) -> bool:
    entity_id = entity.get("id")
    if not isinstance(entity_id, str):
        LOGGER.error("Entity missing valid id: %s", entity)
        return False

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            create_response = await _post_entity(client, entity)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Failed to POST entity %s: %s", entity_id, exc)
            return False

        if create_response.status_code in (201, 204):
            LOGGER.info("Created entity: %s", entity_id)
            return True

        if create_response.status_code == 409:
            normalized = _normalize_entity(entity)
            attrs = {k: v for k, v in normalized.items() if k not in {"id", "type"}}
            try:
                patch_response = await _patch_attrs(client, entity_id, attrs)
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Failed to PATCH entity %s: %s", entity_id, exc)
                return False

            if patch_response.status_code in (204, 207):
                LOGGER.info("Updated entity: %s", entity_id)
                return True

            LOGGER.error(
                "PATCH failed for %s with HTTP %s: %s",
                entity_id,
                patch_response.status_code,
                patch_response.text,
            )
            return False

        LOGGER.error(
            "POST failed for %s with HTTP %s: %s",
            entity_id,
            create_response.status_code,
            create_response.text,
        )
        return False


def upsert_to_orion(entity: dict[str, Any]) -> bool:
    """Upsert one NGSI-LD entity in Orion Context Broker."""
    return asyncio.run(_upsert_async(entity))


def _read_entities_from_file(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, list):
        return [e for e in payload if isinstance(e, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def load_entities(paths: list[Path]) -> tuple[int, int]:
    updated = 0
    errors = 0

    for path in paths:
        if not path.exists():
            LOGGER.warning("Skipping missing file: %s", path)
            continue

        entities = _read_entities_from_file(path)
        LOGGER.info("Loading %d entities from %s", len(entities), path)

        for entity in entities:
            if upsert_to_orion(entity):
                updated += 1
            else:
                errors += 1

    return updated, errors


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Upsert NGSI-LD entities to Orion")
    parser.add_argument("--files", nargs="+", required=True, help="JSON files containing entities (object or array)")
    args = parser.parse_args()

    files = [Path(p) for p in args.files]
    updated, errors = load_entities(files)
    LOGGER.info("RESULT updated=%d errors=%d", updated, errors)

    if errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
