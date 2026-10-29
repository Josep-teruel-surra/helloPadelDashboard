from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.users.models import User
from tests.conftest import auth_headers

MARKDOWN = "# Torneo\n\n- Inscripciones hasta el **viernes**\n- 16 parejas"


async def create_note(client: AsyncClient, user: User, **payload: Any) -> dict[str, Any]:
    payload.setdefault("title", "Torneo de noviembre")
    resp = await client.post("/api/notes", json=payload, headers=auth_headers(user))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def list_ids(client: AsyncClient, user: User, **params: Any) -> list[str]:
    resp = await client.get("/api/notes", params=params, headers=auth_headers(user))
    assert resp.status_code == 200
    return [n["id"] for n in resp.json()]


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/notes")).status_code == 401
    assert (await client.post("/api/notes", json={"title": "x"})).status_code == 401


async def test_create_personal_by_default_keeps_markdown(client: AsyncClient, worker: User) -> None:
    note = await create_note(client, worker, content_md=MARKDOWN)
    assert note["scope"] == "personal"
    assert note["content_md"] == MARKDOWN
    assert note["author"] == {"id": str(worker.id), "full_name": worker.full_name}
    assert note["can_edit"] is True


async def test_content_defaults_to_empty(client: AsyncClient, worker: User) -> None:
    note = await create_note(client, worker)
    assert note["content_md"] == ""


@pytest.mark.parametrize("payload", [{"title": ""}, {"title": "x" * 201}, {}])
async def test_invalid_create_is_rejected(
    client: AsyncClient, worker: User, payload: dict[str, Any]
) -> None:
    resp = await client.post("/api/notes", json=payload, headers=auth_headers(worker))
    assert resp.status_code == 422


@pytest.mark.parametrize("intruder", ["other_worker", "admin"])
async def test_personal_note_is_invisible_to_others(
    client: AsyncClient, admin: User, worker: User, other_worker: User, intruder: str
) -> None:
    other = {"admin": admin, "other_worker": other_worker}[intruder]
    note = await create_note(client, worker, content_md="privado")
    url = f"/api/notes/{note['id']}"
    headers = auth_headers(other)

    assert note["id"] not in await list_ids(client, other)
    assert note["id"] not in await list_ids(client, other, q="privado")
    assert (await client.get(url, headers=headers)).status_code == 404
    assert (await client.patch(url, json={"title": "hack"}, headers=headers)).status_code == 404
    assert (await client.delete(url, headers=headers)).status_code == 404

    resp = await client.get(url, headers=auth_headers(worker))
    assert resp.json()["title"] == note["title"]


async def test_author_updates_and_deletes_personal_note(client: AsyncClient, worker: User) -> None:
    note = await create_note(client, worker)
    url = f"/api/notes/{note['id']}"
    headers = auth_headers(worker)

    resp = await client.patch(url, json={"content_md": MARKDOWN}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["content_md"] == MARKDOWN
    assert body["title"] == note["title"]
    assert body["updated_at"] > note["updated_at"]

    assert (await client.delete(url, headers=headers)).status_code == 204
    assert (await client.get(url, headers=headers)).status_code == 404


@pytest.mark.parametrize("payload", [{"title": None}, {"content_md": None}, {"title": "  "}])
async def test_invalid_updates_are_rejected(
    client: AsyncClient, worker: User, payload: dict[str, Any]
) -> None:
    note = await create_note(client, worker)
    resp = await client.patch(
        f"/api/notes/{note['id']}", json=payload, headers=auth_headers(worker)
    )
    assert resp.status_code == 422


async def test_scope_cannot_be_changed(client: AsyncClient, worker: User) -> None:
    note = await create_note(client, worker)
    resp = await client.patch(
        f"/api/notes/{note['id']}", json={"scope": "company"}, headers=auth_headers(worker)
    )
    # El campo se ignora: la nota sigue siendo personal.
    assert resp.status_code == 200
    assert resp.json()["scope"] == "personal"


async def test_company_note_is_readable_by_everyone(
    client: AsyncClient, admin: User, worker: User, other_worker: User
) -> None:
    note = await create_note(client, worker, scope="company", content_md=MARKDOWN)
    for user in (admin, worker, other_worker):
        assert note["id"] in await list_ids(client, user)
        resp = await client.get(f"/api/notes/{note['id']}", headers=auth_headers(user))
        assert resp.status_code == 200
        assert resp.json()["content_md"] == MARKDOWN


async def test_non_author_cannot_edit_or_delete_company_note(
    client: AsyncClient, worker: User, other_worker: User
) -> None:
    note = await create_note(client, worker, scope="company")
    url = f"/api/notes/{note['id']}"
    headers = auth_headers(other_worker)

    assert (await client.get(url, headers=headers)).json()["can_edit"] is False
    assert (await client.patch(url, json={"title": "x"}, headers=headers)).status_code == 403
    assert (await client.delete(url, headers=headers)).status_code == 403


async def test_admin_can_edit_and_delete_company_note(
    client: AsyncClient, admin: User, worker: User
) -> None:
    note = await create_note(client, worker, scope="company")
    url = f"/api/notes/{note['id']}"
    headers = auth_headers(admin)

    resp = await client.patch(url, json={"title": "Revisada"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["can_edit"] is True
    # El autor sigue siendo quien la creó.
    assert resp.json()["author"]["id"] == str(worker.id)
    assert (await client.delete(url, headers=headers)).status_code == 204


async def test_list_filters_and_search(
    client: AsyncClient, worker: User, other_worker: User
) -> None:
    personal = await create_note(client, worker, title="Lista de la compra")
    company = await create_note(client, other_worker, scope="company", title="Horarios")
    search = await create_note(
        client, other_worker, scope="company", title="Otro", content_md="Cambiar 100% las redes"
    )

    assert set(await list_ids(client, worker, scope="personal")) == {personal["id"]}
    assert set(await list_ids(client, worker, scope="company")) == {company["id"], search["id"]}
    assert await list_ids(client, worker, q="horarios") == [company["id"]]
    assert await list_ids(client, worker, q="REDES") == [search["id"]]
    # Los comodines de LIKE se tratan como texto literal.
    assert await list_ids(client, worker, q="100%") == [search["id"]]
    assert await list_ids(client, worker, q="%") == [search["id"]]


async def test_list_orders_by_last_update(client: AsyncClient, worker: User) -> None:
    first = await create_note(client, worker, title="Primera")
    second = await create_note(client, worker, title="Segunda")
    assert await list_ids(client, worker) == [second["id"], first["id"]]

    await client.patch(
        f"/api/notes/{first['id']}", json={"content_md": "editada"}, headers=auth_headers(worker)
    )
    assert await list_ids(client, worker) == [first["id"], second["id"]]
    assert await list_ids(client, worker, limit=1) == [first["id"]]
