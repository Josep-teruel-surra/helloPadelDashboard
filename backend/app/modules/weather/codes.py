"""Códigos WMO que usa Open-Meteo → descripción en español e icono para el frontend."""

WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("Despejado", "clear"),
    1: ("Mayormente despejado", "partly-cloudy"),
    2: ("Parcialmente nublado", "partly-cloudy"),
    3: ("Nublado", "cloudy"),
    45: ("Niebla", "fog"),
    48: ("Niebla con escarcha", "fog"),
    51: ("Llovizna débil", "drizzle"),
    53: ("Llovizna", "drizzle"),
    55: ("Llovizna intensa", "drizzle"),
    56: ("Llovizna helada", "drizzle"),
    57: ("Llovizna helada intensa", "drizzle"),
    61: ("Lluvia débil", "rain"),
    63: ("Lluvia", "rain"),
    65: ("Lluvia intensa", "rain"),
    66: ("Lluvia helada", "rain"),
    67: ("Lluvia helada intensa", "rain"),
    71: ("Nevada débil", "snow"),
    73: ("Nevada", "snow"),
    75: ("Nevada intensa", "snow"),
    77: ("Granizo fino", "snow"),
    80: ("Chubascos débiles", "rain"),
    81: ("Chubascos", "rain"),
    82: ("Chubascos fuertes", "rain"),
    85: ("Chubascos de nieve", "snow"),
    86: ("Chubascos de nieve fuertes", "snow"),
    95: ("Tormenta", "storm"),
    96: ("Tormenta con granizo", "storm"),
    99: ("Tormenta con granizo fuerte", "storm"),
}


def describe(code: int) -> dict[str, str | int]:
    description, icon = WMO_CODES.get(code, ("Desconocido", "cloudy"))
    return {"weather_code": code, "description": description, "icon": icon}
