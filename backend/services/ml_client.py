from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException

from config import Settings


def _score_to_band(score: float) -> str:
    if score >= 0.7:
        return "green"
    if score >= 0.4:
        return "yellow"
    return "red"


class MLClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ml_service_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def rank_crops(self, payload: dict[str, Any], crop_ids: list[str]) -> list[dict[str, Any]]:
        try:
            response = await self._client.post(f"{self._base_url}/suitability", json=payload)
            response.raise_for_status()
            parsed = response.json()
            scores = parsed.get("scores", [])
            normalized = [
                {
                    "cropId": item["cropId"],
                    "score": float(item["score"]),
                    "band": _score_to_band(float(item["score"])),
                    "breakdown": item.get("breakdown"),
                }
                for item in scores
            ]
            return sorted(normalized, key=lambda item: item["score"], reverse=True)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail="Crop scoring service temporarily unavailable.") from exc

    async def simulate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._client.post(f"{self._base_url}/simulate", json=payload)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
        except Exception:
            raise HTTPException(status_code=503, detail="Crop scoring service temporarily unavailable.")
