from collections.abc import Iterator
from typing import Any

import httpx
import pytest
import respx
from httpx import AsyncClient

from app.core.cache import TTLCache
from app.core.config import settings
from app.modules.users.models import User
from app.modules.weather import service
from tests.conftest import auth_headers

OPEN_METEO_SAMPLE: dict[str, Any] = {
    "latitude": 41.414772,
    "longitude": 2.2254717,
    "timezone": "Europe/Madrid",
    "current": {
        "time": "2026-10-29T11:45",
        "interval": 900,
        "temperature_2m": 19.0,
        "apparent_temperature": 18.1,
        "relative_humidity_2m": 68,
        "precipitation": 0.0,
        "weather_code": 2,
        "wind_speed_10m": 12.3,
        "wind_gusts_10m": 20.9,
        "is_day": 1,
    },
    "hourly": {
        "time": ["2026-10-29T11:00", "2026-10-29T12:00", "2026-10-29T13:00"],
        "temperature_2m": [19.2, 18.9, 19.0],
        "precipitation_probability": [0, 40, None],
        "weather_code": [3, 61, 95],
    },
    "daily": {
        "time": ["2026-10-29", "2026-10-30"],
        "weather_code": [3, 999],
        "temperature_2m_max": [19.4, 20.1],
        "temperature_2m_min": [14.2, 13.8],
        "precipitation_probability_max": [5, 60],
        "sunrise": ["2026-10-29T07:12", "2026-10-30T07:13"],
        "sunset": ["2026-10-29T17:21", "2026-10-30T17:20"],
    },
}


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    fake = FakeClock()
    monkeypatch.setattr(service, "cache", TTLCache(settings.weather_cache_ttl_seconds, clock=fake))
    return fake


@pytest.fixture
def open_meteo(clock: FakeClock) -> Iterator[respx.Route]:
    with respx.mock(assert_all_called=False) as mock:
        yield mock.get(settings.open_meteo_url).respond(json=OPEN_METEO_SAMPLE)


async def get_weather(client: AsyncClient, user: User, **params: Any) -> httpx.Response:
    return await client.get("/api/weather", params=params, headers=auth_headers(user))


async def test_requires_auth(client: AsyncClient, open_meteo: respx.Route) -> None:
    assert (await client.get("/api/weather")).status_code == 401
    assert not open_meteo.called


async def test_defaults_to_barcelona(
    client: AsyncClient, worker: User, open_meteo: respx.Route
) -> None:
    resp = await get_weather(client, worker)
    assert resp.status_code == 200
    location = resp.json()["location"]
    assert location == {
        "latitude": 41.39,
        "longitude": 2.17,
        "name": "Barcelona",
        "is_default": True,
        "timezone": "Europe/Madrid",
    }
    params = open_meteo.calls.last.request.url.params
    assert params["latitude"] == "41.39"
    assert params["longitude"] == "2.17"
    assert params["timezone"] == "auto"


async def test_parses_forecast_in_spanish(
    client: AsyncClient, worker: User, open_meteo: respx.Route
) -> None:
    body = (await get_weather(client, worker, lat=40.4168, lon=-3.7038)).json()

    assert body["location"]["name"] is None
    assert body["location"]["is_default"] is False
    assert body["stale"] is False

    current = body["current"]
    assert current["temperature"] == 19.0
    assert current["description"] == "Parcialmente nublado"
    assert current["icon"] == "partly-cloudy"
    assert current["is_day"] is True
    assert current["wind_speed"] == 12.3

    assert [h["icon"] for h in body["hourly"]] == ["cloudy", "rain", "storm"]
    assert [h["precipitation_probability"] for h in body["hourly"]] == [0, 40, None]

    assert body["daily"][0]["date"] == "2026-10-29"
    assert body["daily"][0]["temperature_max"] == 19.4
    # Código desconocido: no rompe, se muestra genérico.
    assert body["daily"][1]["description"] == "Desconocido"


async def test_caches_by_rounded_coordinates(
    client: AsyncClient, worker: User, other_worker: User, open_meteo: respx.Route
) -> None:
    await get_weather(client, worker, lat=41.3874, lon=2.1686)
    # Otro usuario a pocos metros comparte la entrada.
    await get_weather(client, other_worker, lat=41.3891, lon=2.1702)
    # Y la ubicación por defecto cae en la misma celda.
    await get_weather(client, worker)
    assert open_meteo.call_count == 1

    await get_weather(client, worker, lat=40.4168, lon=-3.7038)
    assert open_meteo.call_count == 2


async def test_cache_expires_after_ttl(
    client: AsyncClient, worker: User, open_meteo: respx.Route, clock: FakeClock
) -> None:
    await get_weather(client, worker)
    clock.now += settings.weather_cache_ttl_seconds - 1
    await get_weather(client, worker)
    assert open_meteo.call_count == 1

    clock.now += 2
    await get_weather(client, worker)
    assert open_meteo.call_count == 2


async def test_upstream_error_without_cache_returns_502(
    client: AsyncClient, worker: User, open_meteo: respx.Route
) -> None:
    open_meteo.respond(status_code=500)
    resp = await get_weather(client, worker)
    assert resp.status_code == 502
    assert "tiempo" in resp.json()["detail"]


@pytest.mark.parametrize(
    "failure",
    [
        {"status_code": 503},
        {"json": {"unexpected": True}},
        {"content": b"<html>no es json</html>"},
    ],
)
async def test_upstream_failure_serves_stale_data(
    client: AsyncClient,
    worker: User,
    open_meteo: respx.Route,
    clock: FakeClock,
    failure: dict[str, Any],
) -> None:
    assert (await get_weather(client, worker)).json()["stale"] is False

    clock.now += settings.weather_cache_ttl_seconds + 1
    open_meteo.respond(**failure)
    resp = await get_weather(client, worker)
    assert resp.status_code == 200
    assert resp.json()["stale"] is True
    assert resp.json()["current"]["temperature"] == 19.0


async def test_timeout_is_handled(
    client: AsyncClient, worker: User, open_meteo: respx.Route
) -> None:
    open_meteo.side_effect = httpx.ConnectTimeout("timeout")
    assert (await get_weather(client, worker)).status_code == 502


@pytest.mark.parametrize(
    "params", [{"lat": 91, "lon": 0}, {"lat": 0, "lon": -181}, {"lat": 41.0}, {"lon": 2.0}]
)
async def test_invalid_coordinates_are_rejected(
    client: AsyncClient, worker: User, open_meteo: respx.Route, params: dict[str, Any]
) -> None:
    resp = await get_weather(client, worker, **params)
    assert resp.status_code == 422
    assert not open_meteo.called


def test_ttl_cache_evicts_oldest_entries() -> None:
    cache: TTLCache[int] = TTLCache(60, max_entries=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3
