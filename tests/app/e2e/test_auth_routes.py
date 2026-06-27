from httpx import AsyncClient

from app.db.models import User
from app.domains.auth.cookies import ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME
from tests.conftest import DEFAULT_PASSWORD, UserFactory, login_as

REGISTER_BODY = {"name": "Created", "email": "created@example.com", "password": "Cr3atedPass!"}


async def test_register_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json=REGISTER_BODY)
    assert response.status_code == 401


async def test_register_forbidden_for_regular_user(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)

    response = await client.post("/auth/register", json=REGISTER_BODY)
    assert response.status_code == 403


async def test_register_succeeds_for_admin(client: AsyncClient, admin_user: User) -> None:
    await login_as(client, admin_user.email)

    response = await client.post("/auth/register", json=REGISTER_BODY)
    assert response.status_code == 201
    assert response.json()["email"] == "created@example.com"


async def test_register_duplicate_email_conflicts(client: AsyncClient, admin_user: User) -> None:
    await login_as(client, admin_user.email)

    body = {**REGISTER_BODY, "email": admin_user.email}
    response = await client.post("/auth/register", json=body)
    assert response.status_code == 409


async def test_register_invalid_body_returns_400(client: AsyncClient, admin_user: User) -> None:
    await login_as(client, admin_user.email)

    body = {**REGISTER_BODY, "password": "short"}
    response = await client.post("/auth/register", json=body)
    assert response.status_code == 400


async def test_login_sets_cookies_and_returns_user(client: AsyncClient, regular_user: User) -> None:
    response = await client.post(
        "/auth/login", json={"email": regular_user.email, "password": DEFAULT_PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["email"] == regular_user.email
    assert ACCESS_COOKIE_NAME in response.cookies
    assert REFRESH_COOKIE_NAME in response.cookies


async def test_login_wrong_password_returns_401(client: AsyncClient, regular_user: User) -> None:
    response = await client.post(
        "/auth/login", json={"email": regular_user.email, "password": "wrong-password"}
    )
    assert response.status_code == 401


async def test_login_inactive_account_returns_401(
    client: AsyncClient, make_user: UserFactory
) -> None:
    user = await make_user(email="inactive@example.com", is_active=False)

    response = await client.post(
        "/auth/login", json={"email": user.email, "password": DEFAULT_PASSWORD}
    )
    assert response.status_code == 401


async def test_login_invalid_body_returns_400(client: AsyncClient) -> None:
    response = await client.post("/auth/login", json={"email": "user@example.com"})
    assert response.status_code == 400


async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)

    response = await client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == regular_user.email


async def test_refresh_without_cookie_returns_401(client: AsyncClient) -> None:
    response = await client.post("/auth/refresh")
    assert response.status_code == 401


async def test_refresh_rotates_access_token(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)

    response = await client.post("/auth/refresh")
    assert response.status_code == 200
    assert ACCESS_COOKIE_NAME in response.cookies


async def test_logout_clears_session(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)

    response = await client.post("/auth/logout")
    assert response.status_code == 204
    assert (await client.get("/auth/me")).status_code == 401


async def test_logout_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/auth/logout")
    assert response.status_code == 401


async def test_change_password_wrong_current_returns_401(
    client: AsyncClient, regular_user: User
) -> None:
    await login_as(client, regular_user.email)

    response = await client.patch(
        "/auth/me/password",
        json={"current_password": "wrong-password", "new_password": "Br4ndNew!"},
    )
    assert response.status_code == 401


async def test_change_password_same_password_returns_400(
    client: AsyncClient, regular_user: User
) -> None:
    await login_as(client, regular_user.email)

    response = await client.patch(
        "/auth/me/password",
        json={"current_password": DEFAULT_PASSWORD, "new_password": DEFAULT_PASSWORD},
    )
    assert response.status_code == 400


async def test_change_password_invalid_new_password_returns_400(
    client: AsyncClient, regular_user: User
) -> None:
    await login_as(client, regular_user.email)

    response = await client.patch(
        "/auth/me/password",
        json={"current_password": DEFAULT_PASSWORD, "new_password": "short"},
    )
    assert response.status_code == 400


async def test_change_password_success_allows_new_login(
    client: AsyncClient, regular_user: User
) -> None:
    await login_as(client, regular_user.email)
    new_password = "Br4ndNewPass!"

    response = await client.patch(
        "/auth/me/password",
        json={"current_password": DEFAULT_PASSWORD, "new_password": new_password},
    )
    assert response.status_code == 204

    old = await client.post(
        "/auth/login", json={"email": regular_user.email, "password": DEFAULT_PASSWORD}
    )
    assert old.status_code == 401
    new = await client.post(
        "/auth/login", json={"email": regular_user.email, "password": new_password}
    )
    assert new.status_code == 200
