"""Cliente de Open-Meteo: pide la previsión y la traduce a nuestros schemas."""

from typing import Any

import httpx

from app.core.config import settings
from app.core.security import utcnow
from app.modules.weather.codes import describe
from app.modules.weather.schemas import (
    CurrentWeather,
    DailyForecast,
    HourlyForecast,
    Location,
    WeatherRead,
)

CURRENT_FIELDS = (
    "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,"
    "weather_code,wind_speed_10m,wind_gusts_10m,is_day"
)
HOURLY_FIELDS = "temperature_2m,precipitation_probability,weather_code"
DAILY_FIELDS = (
    "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
    "sunrise,sunset"
)
TIMEOUT = httpx.Timeout(5.0)


class WeatherUnavailableError(Exception):
    pass


async def fetch_forecast(latitude: float, longitude: float) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": CURRENT_FIELDS,
        "hourly": HOURLY_FIELDS,
        "daily": DAILY_FIELDS,
        "timezone": "auto",
        "forecast_days": 4,
        "forecast_hours": 12,
        "wind_speed_unit": "kmh",
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(settings.open_meteo_url, params=params)
            resp.raise_for_status()
            return resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise WeatherUnavailableError(str(exc)) from exc


def _column(block: dict[str, Any], key: str, i: int) -> Any:
    values = block.get(key) or []
    return values[i] if i < len(values) else None


def parse_forecast(
    data: dict[str, Any], *, latitude: float, longitude: float, name: str | None, is_default: bool
) -> WeatherRead:
    try:
        current = data["current"]
        hourly = data.get("hourly", {})
        daily = data.get("daily", {})
        return WeatherRead(
            location=Location(
                latitude=latitude,
                longitude=longitude,
                name=name,
                is_default=is_default,
                timezone=data.get("timezone", "UTC"),
            ),
            current=CurrentWeather(
                time=current["time"],
                is_day=bool(current.get("is_day", 1)),
                temperature=current["temperature_2m"],
                apparent_temperature=current.get("apparent_temperature"),
                humidity=current.get("relative_humidity_2m"),
                precipitation=current.get("precipitation"),
                wind_speed=current.get("wind_speed_10m"),
                wind_gusts=current.get("wind_gusts_10m"),
                **describe(current["weather_code"]),
            ),
            hourly=[
                HourlyForecast(
                    time=time,
                    temperature=_column(hourly, "temperature_2m", i),
                    precipitation_probability=_column(hourly, "precipitation_probability", i),
                    **describe(_column(hourly, "weather_code", i) or 0),
                )
                for i, time in enumerate(hourly.get("time", []))
            ],
            daily=[
                DailyForecast(
                    date=day,
                    temperature_max=_column(daily, "temperature_2m_max", i),
                    temperature_min=_column(daily, "temperature_2m_min", i),
                    precipitation_probability_max=_column(
                        daily, "precipitation_probability_max", i
                    ),
                    sunrise=_column(daily, "sunrise", i),
                    sunset=_column(daily, "sunset", i),
                    **describe(_column(daily, "weather_code", i) or 0),
                )
                for i, day in enumerate(daily.get("time", []))
            ],
            fetched_at=utcnow(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherUnavailableError(f"Respuesta inesperada de Open-Meteo: {exc}") from exc
