from __future__ import annotations

import hashlib
from typing import Any

import httpx

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
                }
                for item in scores
            ]
            return sorted(normalized, key=lambda item: item["score"], reverse=True)
        except Exception:
            # Fallback deterministic pseudo-score when ML service is not reachable.
            ranked: list[dict[str, Any]] = []
            seed = payload.get("parcel", {}).get("id", "parcel")
            for crop_id in crop_ids:
                digest = hashlib.sha256(f"{seed}:{crop_id}".encode("utf-8")).hexdigest()
                score = (int(digest[:8], 16) % 100) / 100
                ranked.append({"cropId": crop_id, "score": round(score, 3), "band": _score_to_band(score)})
            ranked.sort(key=lambda item: item["score"], reverse=True)
            return ranked

    async def simulate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._client.post(f"{self._base_url}/simulate", json=payload)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        scenario = payload.get("scenario", {})
        irrigation = float(scenario.get("irrigationMm", 0))
        score = max(0.0, min(1.0, 0.45 + (irrigation / 1000.0)))
        return {
            "yieldIndex": round(score, 3),
            "riskIndex": round(max(0.0, 1 - score), 3),
            "waterUseMm": irrigation,
        }
