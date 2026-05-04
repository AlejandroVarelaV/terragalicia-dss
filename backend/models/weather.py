from __future__ import annotations

from pydantic import BaseModel


class WeatherObservedResponse(BaseModel):
    dateObserved: str | int | None = None
    temperature: float | None = None
    relativeHumidity: float | None = None
    precipitation: float | None = None
    windSpeed: float | None = None


class WeatherForecastItem(BaseModel):
    validFrom: str | None = None
    validTo: str | None = None
    temperatureMin: float | None = None
    temperatureMax: float | None = None
    precipitation: float | None = None
    frostRisk: float | None = None


class WeatherBundleResponse(BaseModel):
    current: WeatherObservedResponse
    forecast: list[WeatherForecastItem]
