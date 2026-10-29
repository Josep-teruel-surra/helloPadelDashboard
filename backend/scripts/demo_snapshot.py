"""Genera la «foto» de la API que usa la demo del frontend (sin backend, p. ej. en GitHub Pages).

Se ejecuta contra un backend con los datos de ejemplo recién cargados:

    docker compose exec backend sh -c \
      "alembic downgrade base && alembic upgrade head && python -m app.cli seed"
    docker compose exec -T backend python -m scripts.demo_snapshot > frontend/src/demo/snapshot.json

Guarda, para cada usuario de ejemplo, las respuestas «completas» de cada listado (sin filtros);
la demo filtra y busca sobre ellas en el navegador.
"""

import json
import sys
from datetime import date

import httpx

from app.seed import SEED_ADMIN_EMAIL, SEED_PASSWORD

BASE_URL = "http://localhost:8000/api"
USERS = [SEED_ADMIN_EMAIL, "ana@example.com", "bruno@example.com"]

# Clave en la foto → petición que devuelve todo lo que ese usuario puede ver.
ENDPOINTS = {
    "me": "/users/me",
    "users": "/users?include_inactive=true",
    "home": "/home",
    "weather": "/weather",
    "todos": "/todos?limit=500",
    "notes": "/notes?limit=500",
    "campuses": "/campuses?include_inactive=true",
    "events": "/events?when=all&limit=500",
    "products": "/products?include_inactive=true",
    "movements": "/stock/movements?limit=500",
    "shipments": "/shipments?limit=500",
    "sent_material": "/shipments/sent-material",
    "students": "/students?limit=500",
    "certifications": "/certifications?include_inactive=true",
    "exams": "/exams?limit=500",
}


def snapshot_user(client: httpx.Client, email: str) -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": SEED_PASSWORD})
    resp.raise_for_status()
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    data = {}
    for key, path in ENDPOINTS.items():
        r = client.get(path, headers=headers)
        r.raise_for_status()
        data[key] = r.json()
    return data


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        users = {email: snapshot_user(client, email) for email in USERS}
    json.dump(
        {"generated_on": date.today().isoformat(), "users": users},
        sys.stdout,
        ensure_ascii=False,
        separators=(",", ":"),
    )


if __name__ == "__main__":
    main()
