from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from config import Settings


class WeatherFetcher:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_forecast(self, lat: float, lon: float) -> list[dict[str, Any]]:
        meteo = await self._fetch_meteogalicia(lat=lat, lon=lon)
        if meteo:
            return meteo

        ow = await self._fetch_openweather(lat=lat, lon=lon)
        if ow:
            return ow

        return self._read_seed_forecast()

    async def fetch_current(self, lat: float, lon: float) -> dict[str, Any]:
        meteo = await self._fetch_meteogalicia_current(lat=lat, lon=lon)
        if meteo:
            return meteo

        ow = await self._fetch_openweather_current(lat=lat, lon=lon)
        if ow:
            return ow

        observed = self._read_seed_observed()
        return observed[-1] if observed else {}

    async def _fetch_meteogalicia(self, lat: float, lon: float) -> list[dict[str, Any]]:
        try:
            url = f"{self._settings.meteogalicia_base_url.rstrip('/')}/meteo/fake-forecast"
            response = await self._client.get(url, params={"lat": lat, "lon": lon})
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    async def _fetch_meteogalicia_current(self, lat: float, lon: float) -> dict[str, Any]:
        try:
            url = f"{self._settings.meteogalicia_base_url.rstrip('/')}/meteo/fake-current"
            response = await self._client.get(url, params={"lat": lat, "lon": lon})
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
        return {}

    async def _fetch_openweather(self, lat: float, lon: float) -> list[dict[str, Any]]:
        if not self._settings.openweather_api_key:
            return []
        try:
            response = await self._client.get(
                f"{self._settings.openweather_base_url.rstrip('/')}/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self._settings.openweather_api_key,
                    "units": "metric",
                },
            )
            response.raise_for_status()
            data = response.json().get("list", [])
            return [
                {
                    "date": item.get("dt_txt"),
                    "temperature": item.get("main", {}).get("temp"),
                    "humidity": item.get("main", {}).get("humidity"),
                    "precipitation": item.get("rain", {}).get("3h", 0),
                }
                for item in data[:7]
            ]
        except Exception:
            return []

    async def _fetch_openweather_current(self, lat: float, lon: float) -> dict[str, Any]:
        if not self._settings.openweather_api_key:
            return {}
        try:
            response = await self._client.get(
                f"{self._settings.openweather_base_url.rstrip('/')}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self._settings.openweather_api_key,
                    "units": "metric",
                },
            )
            response.raise_for_status()
            payload = response.json()
            return {
                "dateObserved": payload.get("dt"),
                "temperature": payload.get("main", {}).get("temp"),
                "relativeHumidity": payload.get("main", {}).get("humidity"),
                "precipitation": payload.get("rain", {}).get("1h", 0),
                "windSpeed": payload.get("wind", {}).get("speed"),
            }
        except Exception:
            return {}

    def _read_seed_observed(self) -> list[dict[str, Any]]:
        path = Path(self._settings.seed_data_dir) / "seed_weather_observed.json"
        return self._read_json(path)

    def _read_seed_forecast(self) -> list[dict[str, Any]]:
        path = Path(self._settings.seed_data_dir) / "seed_weather_forecast.json"
        return self._read_json(path)[:7]

    @staticmethod
    def _read_json(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
