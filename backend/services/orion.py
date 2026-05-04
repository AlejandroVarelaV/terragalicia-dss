from __future__ import annotations

import logging
from typing import Any

import httpx

from config import Settings

logger = logging.getLogger(__name__)


class OrionClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.orion_base_url.rstrip("/")
        self._headers = {
            "Content-Type": "application/ld+json",
            "Accept": "application/ld+json",
            "Link": '<https://uri.fiware.org/ns/data-models>; rel="http://www.w3.org/ns/json-ld#context"',
            "fiware-service": settings.orion_service,
            "fiware-servicepath": settings.orion_servicepath,
        }
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def get_entity(self, entity_id: str, entity_type: str | None = None) -> dict[str, Any]:
        params = {"type": entity_type} if entity_type else None
        url = f"{self._base_url}/ngsi-ld/v1/entities/{entity_id}"
        logger.debug("Orion GET entity url=%s params=%s", url, params)
        response = await self._client.get(url, headers=self._headers, params=params)
        response.raise_for_status()
        return response.json()

    async def query_entities(self, entity_type: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        query_params: dict[str, Any] = {"type": entity_type}
        if params:
            query_params.update(params)
        url = f"{self._base_url}/ngsi-ld/v1/entities"
        logger.debug("Orion QUERY entities url=%s params=%s", url, query_params)
        response = await self._client.get(url, headers=self._headers, params=query_params)
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, list) else []

    async def create_entity(self, payload: dict[str, Any]) -> bool:
        url = f"{self._base_url}/ngsi-ld/v1/entities"
        logger.debug("Orion CREATE entity url=%s id=%s", url, payload.get("id"))
        response = await self._client.post(url, headers=self._headers, json=payload)
        if response.status_code in {201, 204}:
            return True
        response.raise_for_status()
        return False

    async def update_entity_attr(self, entity_id: str, attr: str, value: Any) -> bool:
        url = f"{self._base_url}/ngsi-ld/v1/entities/{entity_id}/attrs/{attr}"
        payload = {"type": "Property", "value": value}
        logger.debug("Orion UPDATE attr url=%s payload=%s", url, payload)
        response = await self._client.patch(url, headers=self._headers, json=payload)
        if response.status_code in {204, 200}:
            return True
        response.raise_for_status()
        return False

    async def create_subscription(self, payload: dict[str, Any]) -> str:
        url = f"{self._base_url}/ngsi-ld/v1/subscriptions"
        logger.debug("Orion CREATE subscription url=%s", url)
        response = await self._client.post(url, headers=self._headers, json=payload)
        response.raise_for_status()
        location = response.headers.get("Location", "")
        return location.rsplit("/", maxsplit=1)[-1] if location else ""
