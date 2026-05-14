from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
from typing import Any, List

import httpx

from config import get_settings

LOGGER = logging.getLogger(__name__)


class WeatherFetcher:
    """Fetch weather using Open-Meteo (primary) and optional AEMET fallback.

    Provides:
    - fetch_current_weather(lat, lon) -> dict
    - fetch_forecast(lat, lon, days=7) -> list[dict]
    - fetch_historical(lat, lon, days=30) -> list[dict]
    """

    FORECAST_DAILY_VARS = (
        "temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "windspeed_10m_max,relative_humidity_2m_max,relative_humidity_2m_min"
    )

    HISTORICAL_DAILY_VARS = (
        "temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "windspeed_10m_max,relative_humidity_2m_max,relative_humidity_2m_min,"
        "et0_fao_evapotranspiration,soil_temperature_0cm,soil_moisture_0_to_1cm"
    )

    def __init__(self, settings=None) -> None:
        settings = settings or get_settings()
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_forecast(self, lat: float, lon: float, days: int = 7) -> List[dict[str, Any]]:
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": self.FORECAST_DAILY_VARS,
                "forecast_days": days,
                "timezone": "Europe/Madrid",
            }
            url = self._settings.open_meteo_url.rstrip("/")
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            et0_list = daily.get("et0_fao_evapotranspiration") or []
            result: List[dict[str, Any]] = []
            for i, dt in enumerate(dates):
                item = {
                    "date": dt,
                    "validFrom": dt,
                    "validTo": dt,
                    "temperature_max": daily.get("temperature_2m_max", [None])[i],
                    "temperature_min": daily.get("temperature_2m_min", [None])[i],
                    "temperatureMin": daily.get("temperature_2m_min", [None])[i],
                    "temperatureMax": daily.get("temperature_2m_max", [None])[i],
                    "precipitation": daily.get("precipitation_sum", [0])[i],
                    "windSpeed": daily.get("windspeed_10m_max", [None])[i],
                    "relativeHumidity_max": daily.get("relative_humidity_2m_max", [None])[i],
                    "relativeHumidity_min": daily.get("relative_humidity_2m_min", [None])[i],
                    "frostRisk": 0.0,
                    "et0": et0_list[i] if i < len(et0_list) else None,
                }
                result.append(item)
            if result:
                return result
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Open-Meteo forecast failed: %s", exc)

        # Optional AEMET fallback could be implemented here if API key provided
        if self._settings.aemet_api_key:
            LOGGER.info("AEMET fallback requested but not implemented; skipping")

        # If all real sources fail, return climatological average entries
        LOGGER.warning("Weather providers failed; returning climatological average forecast")
        return self._climatology_list(days)

    async def fetch_current_weather(self, lat: float, lon: float) -> dict[str, Any]:
        try:
            # Use forecast endpoint and take today's entry
            forecasts = await self.fetch_forecast(lat, lon, days=1)
            if forecasts:
                f = forecasts[0]
                temp_avg = None
                if f.get("temperature_max") is not None and f.get("temperature_min") is not None:
                    temp_avg = (f["temperature_max"] + f["temperature_min"]) / 2.0
                rh = None
                if f.get("relativeHumidity_max") is not None and f.get("relativeHumidity_min") is not None:
                    rh = (f["relativeHumidity_max"] + f["relativeHumidity_min"]) / 2.0 / 100.0
                return {
                    "dateObserved": f.get("date"),
                    "temperature": temp_avg,
                    "relativeHumidity": rh,
                    "precipitation": f.get("precipitation"),
                    "windSpeed": f.get("windSpeed"),
                    "dataQuality": "live",
                }
        except Exception:
            pass

        # If providers fail, return climatology single entry
        LOGGER.warning("Current weather unavailable; returning climatological average")
        return self._climatology_single()

    async def fetch_current(self, lat: float, lon: float) -> dict[str, Any]:
        return await self.fetch_current_weather(lat, lon)

    async def fetch_historical(self, lat: float, lon: float, days: int = 30) -> List[dict[str, Any]]:
        try:
            end = date.today()
            start = end - timedelta(days=days - 1)
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "daily": self.HISTORICAL_DAILY_VARS,
                "timezone": "Europe/Madrid",
            }
            url = self._settings.open_meteo_archive_url.rstrip("/")
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            result: List[dict[str, Any]] = []
            for i, dt in enumerate(dates):
                temp_avg = None
                tmax = daily.get("temperature_2m_max", [None])[i]
                tmin = daily.get("temperature_2m_min", [None])[i]
                if tmax is not None and tmin is not None:
                    temp_avg = (tmax + tmin) / 2.0
                rh = None
                rh_max = daily.get("relative_humidity_2m_max", [None])[i]
                rh_min = daily.get("relative_humidity_2m_min", [None])[i]
                if rh_max is not None and rh_min is not None:
                    rh = (rh_max + rh_min) / 2.0 / 100.0
                result.append({
                    "date": dt,
                    "temperature": temp_avg,
                    "relativeHumidity": rh,
                    "precipitation": daily.get("precipitation_sum", [0])[i],
                    "windSpeed": daily.get("windspeed_10m_max", [None])[i],
                })
            if result:
                return result
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Open-Meteo historical failed: %s", exc)

        LOGGER.warning("Historical providers failed; returning climatological average series")
        return [self._climatology_single() for _ in range(days)]

    def _climatology_single(self) -> dict[str, Any]:
        # Use documented AEMET 1991-2020 normals for A Coruña
        return {
            "temperature_max": 16.2,
            "temperature_min": 8.4,
            "temperatureMax": 16.2,
            "temperatureMin": 8.4,
            "temperature": (16.2 + 8.4) / 2.0,
            "precipitation": 2.97,
            "relativeHumidity": 0.76,
            "windSpeed": 3.2,
            "dataQuality": "climatological_average",
            "warning": "Live weather unavailable. Using 30-year April climatology for A Coruña.",
        }

    def _climatology_list(self, days: int) -> List[dict[str, Any]]:
        today = date.today()
        result = []
        for i in range(days):
            dt = (today + timedelta(days=i)).isoformat()
            entry = self._climatology_single()
            entry["date"] = dt
            entry["validFrom"] = dt
            entry["validTo"] = dt
            result.append(entry)
        return result

