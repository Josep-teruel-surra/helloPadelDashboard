import logging

from fastapi import HTTPException, status

from app.core.cache import TTLCache
from app.core.config import settings
from app.modules.weather import client
from app.modules.weather.schemas import WeatherRead

logger = logging.getLogger(__name__)

# Clave: coordenadas redondeadas a 2 decimales (~1 km), así quienes estén en
# la academia comparten la misma entrada.
cache: TTLCache[WeatherRead] = TTLCache(settings.weather_cache_ttl_seconds)


def _round(value: float) -> float:
    return round(value, 2)


async def get_weather(latitude: float | None, longitude: float | None) -> WeatherRead:
    is_default = latitude is None or longitude is None
    if latitude is None or longitude is None:
        latitude, longitude = settings.weather_default_latitude, settings.weather_default_longitude
    key = (_round(latitude), _round(longitude))

    if cached := cache.get(key):
        return cached

    try:
        data = await client.fetch_forecast(*key)
        weather = client.parse_forecast(
            data,
            latitude=key[0],
            longitude=key[1],
            name=settings.weather_default_name if is_default else None,
            is_default=is_default,
        )
    except client.WeatherUnavailableError as exc:
        logger.warning("Open-Meteo no disponible para %s: %s", key, exc)
        if stale := cache.get_stale(key):
            return stale.model_copy(update={"stale": True})
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "No se pudo obtener el tiempo. Inténtalo más tarde."
        ) from exc

    cache.set(key, weather)
    return weather
