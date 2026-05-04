from __future__ import annotations

from typing import Any

import httpx

from config import Settings


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.llm_service_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._client.post(f"{self._base_url}/chat", json=payload)
            response.raise_for_status()
            body = response.json()
            if isinstance(body, dict):
                return body
        except Exception:
            pass

        language = payload.get("language", "es")
        if str(language).lower().startswith("gl"):
            answer = "No puiden contactar co servizo LLM. Baseado no contexto da parcela, recomendo revisar humidade do solo e previsión de choiva antes de fertilizar."
            follow_ups = ["Queres unha proposta de calendario para esta semana?", "Prefires recomendación por cultivo?" ]
        else:
            answer = "No pude contactar con el servicio LLM. Según el contexto de la parcela, recomiendo revisar humedad del suelo y previsión de lluvia antes de fertilizar."
            follow_ups = ["Quieres una propuesta de calendario para esta semana?", "Prefieres recomendaciones por cultivo?"]

        return {
            "answer": answer,
            "references": ["parcel_context", "weather_snapshot", "recent_operations"],
            "followUps": follow_ups,
        }
