from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, User
from tests.conftest import login_as


async def test_list_users_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/users")
    assert response.status_code == 401


async def test_list_users_returns_pagination(
    client: AsyncClient, regular_user: User, admin_user: User
) -> None:
    await login_as(client, regular_user.email)

    response = await client.get("/users", params={"limit": 1, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert len(body["items"]) == 1


async def test_get_user_returns_match(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)

    response = await client.get(f"/users/{regular_user.id}")
    assert response.status_code == 200
    assert response.json()["email"] == regular_user.email


async def test_get_user_not_found(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)

    response = await client.get(f"/users/{uuid4()}")
    assert response.status_code == 404


async def test_update_user_forbidden_for_regular_user(
    client: AsyncClient, regular_user: User
) -> None:
    await login_as(client, regular_user.email)

    response = await client.patch(f"/users/{regular_user.id}", json={"name": "Hacker"})
    assert response.status_code == 403


async def test_update_user_succeeds_for_admin(
    client: AsyncClient, admin_user: User, regular_user: User
) -> None:
    await login_as(client, admin_user.email)

    response = await client.patch(f"/users/{regular_user.id}", json={"name": "Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


async def test_update_user_duplicate_email_conflicts(
    client: AsyncClient, admin_user: User, regular_user: User
) -> None:
    await login_as(client, admin_user.email)

    response = await client.patch(f"/users/{regular_user.id}", json={"email": admin_user.email})
    assert response.status_code == 409


async def test_update_user_not_found(client: AsyncClient, admin_user: User) -> None:
    await login_as(client, admin_user.email)

    response = await client.patch(f"/users/{uuid4()}", json={"name": "X"})
    assert response.status_code == 404


async def test_update_user_invalid_body_returns_400(
    client: AsyncClient, admin_user: User, regular_user: User
) -> None:
    await login_as(client, admin_user.email)

    response = await client.patch(f"/users/{regular_user.id}", json={"email": "not-an-email"})
    assert response.status_code == 400


async def test_delete_user_forbidden_for_regular_user(
    client: AsyncClient, regular_user: User, admin_user: User
) -> None:
    await login_as(client, regular_user.email)

    response = await client.delete(f"/users/{admin_user.id}")
    assert response.status_code == 403


async def test_delete_user_succeeds_for_admin(
    client: AsyncClient, admin_user: User, regular_user: User
) -> None:
    await login_as(client, admin_user.email)

    response = await client.delete(f"/users/{regular_user.id}")
    assert response.status_code == 204
    assert (await client.get(f"/users/{regular_user.id}")).status_code == 404


async def test_delete_user_not_found(client: AsyncClient, admin_user: User) -> None:
    await login_as(client, admin_user.email)

    response = await client.delete(f"/users/{uuid4()}")
    assert response.status_code == 404


async def test_delete_user_with_dependencies_conflicts(
    client: AsyncClient, admin_user: User, regular_user: User, db_session: AsyncSession
) -> None:
    db_session.add(Project(name="Owned", owner_id=regular_user.id))
    await db_session.commit()
    await login_as(client, admin_user.email)

    response = await client.delete(f"/users/{regular_user.id}")
    assert response.status_code == 409
