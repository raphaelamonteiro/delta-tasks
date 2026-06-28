from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProjectMember, ProjectRole, Task, User
from tests.conftest import UserFactory, login_as

DEFAULT_COLUMNS = ["Pendente", "Em Progresso", "Em Revisão", "Concluído"]


async def test_create_project_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/projects", json={"name": "Quadro"})
    assert response.status_code == 401


async def test_create_project_success(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)

    response = await client.post("/projects", json={"name": "Quadro", "description": "Time A"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Quadro"
    assert body["description"] == "Time A"
    assert body["owner_id"] == str(regular_user.id)
    assert [column["name"] for column in body["columns"]] == DEFAULT_COLUMNS
    assert [column["position"] for column in body["columns"]] == [0, 1, 2, 3]


async def test_create_project_registers_owner_as_member(
    client: AsyncClient, regular_user: User, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)

    response = await client.post("/projects", json={"name": "Quadro"})
    project_id = response.json()["id"]

    result = await db_session.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    )
    member = result.scalar_one()
    assert member.user_id == regular_user.id
    assert member.role is ProjectRole.OWNER


async def test_create_project_without_name_returns_400(
    client: AsyncClient, regular_user: User
) -> None:
    await login_as(client, regular_user.email)

    response = await client.post("/projects", json={"description": "sem nome"})
    assert response.status_code == 400


async def test_create_project_empty_name_returns_400(
    client: AsyncClient, regular_user: User
) -> None:
    await login_as(client, regular_user.email)

    response = await client.post("/projects", json={"name": ""})
    assert response.status_code == 400


async def test_create_project_without_description_succeeds(
    client: AsyncClient, regular_user: User
) -> None:
    await login_as(client, regular_user.email)

    response = await client.post("/projects", json={"name": "Quadro"})

    assert response.status_code == 201
    assert response.json()["description"] is None


async def test_list_projects_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get("/projects")).status_code == 401


async def test_list_returns_only_member_projects(
    client: AsyncClient, regular_user: User, make_user: UserFactory
) -> None:
    await login_as(client, regular_user.email)
    mine = await client.post("/projects", json={"name": "Meu"})
    my_id = mine.json()["id"]

    other = await make_user(email="other@example.com")
    await login_as(client, other.email)
    await client.post("/projects", json={"name": "Outro"})

    await login_as(client, regular_user.email)
    response = await client.get("/projects")

    assert response.status_code == 200
    assert [project["id"] for project in response.json()] == [my_id]


async def test_get_board_shows_ordered_columns_and_tasks(
    client: AsyncClient, regular_user: User, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    created = await client.post("/projects", json={"name": "Quadro"})
    project_id = created.json()["id"]
    first_column = created.json()["columns"][0]
    db_session.add(
        Task(project_id=project_id, stage_id=first_column["id"], title="Tarefa 1", position=0)
    )
    await db_session.commit()

    response = await client.get(f"/projects/{project_id}")

    assert response.status_code == 200
    columns = response.json()["columns"]
    assert [column["name"] for column in columns] == DEFAULT_COLUMNS
    assert [task["title"] for task in columns[0]["tasks"]] == ["Tarefa 1"]
    assert columns[1]["tasks"] == []


async def test_get_board_forbidden_for_non_member(
    client: AsyncClient, regular_user: User, make_user: UserFactory
) -> None:
    await login_as(client, regular_user.email)
    created = await client.post("/projects", json={"name": "Quadro"})
    project_id = created.json()["id"]

    other = await make_user(email="other@example.com")
    await login_as(client, other.email)
    response = await client.get(f"/projects/{project_id}")

    assert response.status_code == 403


async def test_get_board_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get("/projects/1")).status_code == 401


async def test_get_board_allows_global_admin(
    client: AsyncClient, regular_user: User, admin_user: User
) -> None:
    await login_as(client, regular_user.email)
    created = await client.post("/projects", json={"name": "Quadro"})
    project_id = created.json()["id"]

    await login_as(client, admin_user.email)
    response = await client.get(f"/projects/{project_id}")

    assert response.status_code == 200


async def test_get_board_not_found(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    response = await client.get("/projects/999999")
    assert response.status_code == 404


async def _create_project(client: AsyncClient) -> dict[str, Any]:
    response = await client.post("/projects", json={"name": "Quadro", "description": "d1"})
    data: dict[str, Any] = response.json()
    return data


async def test_update_project_success(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    project = await _create_project(client)

    response = await client.patch(
        f"/projects/{project['id']}", json={"name": "Novo", "description": "d2"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Novo"
    assert response.json()["description"] == "d2"
    board = await client.get(f"/projects/{project['id']}")
    assert board.json()["name"] == "Novo"


async def test_delete_project_success(
    client: AsyncClient, regular_user: User, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    project = await _create_project(client)
    project_id = project["id"]
    db_session.add(
        Task(project_id=project_id, stage_id=project["columns"][0]["id"], title="T", position=0)
    )
    await db_session.commit()

    response = await client.delete(f"/projects/{project_id}")

    assert response.status_code == 204
    assert (await client.get(f"/projects/{project_id}")).status_code == 404
    members = await db_session.scalars(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    )
    tasks = await db_session.scalars(select(Task).where(Task.project_id == project_id))
    assert members.all() == []
    assert tasks.all() == []


async def test_update_forbidden_for_non_owner_member(
    client: AsyncClient, regular_user: User, make_user: UserFactory, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    project = await _create_project(client)
    member = await make_user(email="member@example.com")
    db_session.add(
        ProjectMember(project_id=project["id"], user_id=member.id, role=ProjectRole.MEMBER)
    )
    await db_session.commit()

    await login_as(client, member.email)
    response = await client.patch(f"/projects/{project['id']}", json={"name": "Hack"})

    assert response.status_code == 403


async def test_delete_forbidden_for_non_owner_member(
    client: AsyncClient, regular_user: User, make_user: UserFactory, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    project = await _create_project(client)
    member = await make_user(email="member@example.com")
    db_session.add(
        ProjectMember(project_id=project["id"], user_id=member.id, role=ProjectRole.MEMBER)
    )
    await db_session.commit()

    await login_as(client, member.email)
    response = await client.delete(f"/projects/{project['id']}")

    assert response.status_code == 403


async def test_update_requires_authentication(client: AsyncClient) -> None:
    assert (await client.patch("/projects/1", json={"name": "X"})).status_code == 401


async def test_delete_requires_authentication(client: AsyncClient) -> None:
    assert (await client.delete("/projects/1")).status_code == 401


async def test_update_not_found(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    assert (await client.patch("/projects/999999", json={"name": "X"})).status_code == 404


async def test_delete_not_found(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    assert (await client.delete("/projects/999999")).status_code == 404
