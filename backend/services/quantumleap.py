from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from config import Settings

logger = logging.getLogger(__name__)


class QuantumLeapClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.quantumleap_base_url.rstrip("/")
        self._headers = {
            "fiware-service": settings.orion_service,
            "fiware-servicepath": settings.orion_servicepath,
        }
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def get_entity_history(
        self,
        entity_id: str,
        attr: str,
        from_date: datetime,
        to_date: datetime,
    ) -> list[dict[str, Any]]:
        params = {
            "fromDate": from_date.isoformat(),
            "toDate": to_date.isoformat(),
            "attrs": attr,
        }
        url = f"{self._base_url}/v2/entities/{entity_id}/attrs/{attr}"
        logger.debug("QuantumLeap history url=%s params=%s", url, params)
        response = await self._client.get(url, headers=self._headers, params=params)
        response.raise_for_status()
        payload = response.json()
        values = payload.get("attr", {}).get("values", []) if isinstance(payload, dict) else []
        return [{"date": item.get("recvTime"), "value": item.get("attrValue")} for item in values]

    async def get_last_n(self, entity_id: str, attr: str, n: int) -> list[dict[str, Any]]:
        params = {"lastN": n}
        url = f"{self._base_url}/v2/entities/{entity_id}/attrs/{attr}"
        logger.debug("QuantumLeap lastN url=%s params=%s", url, params)
        response = await self._client.get(url, headers=self._headers, params=params)
        response.raise_for_status()
        payload = response.json()
        values = payload.get("attr", {}).get("values", []) if isinstance(payload, dict) else []
        return [{"date": item.get("recvTime"), "value": item.get("attrValue")} for item in values]
