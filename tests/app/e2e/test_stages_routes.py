from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProjectMember, ProjectRole, Task, User
from tests.conftest import UserFactory, login_as


async def _create_board(client: AsyncClient) -> tuple[int, list[int]]:
    """Create a project (owner = logged-in user) and return ``(project_id, stage_ids)``."""
    created = await client.post("/projects", json={"name": "Quadro"})
    body = created.json()
    return body["id"], [column["id"] for column in body["columns"]]


async def _add_member(
    db_session: AsyncSession, project_id: int, user: User, role: ProjectRole
) -> None:
    db_session.add(ProjectMember(project_id=project_id, user_id=user.id, role=role))
    await db_session.commit()


async def test_create_stage_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/stages", json={"project_id": 1, "name": "Nova"})
    assert response.status_code == 401


async def test_create_stage_appends_to_the_end_of_board(
    client: AsyncClient, regular_user: User
) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)

    response = await client.post("/stages", json={"project_id": project_id, "name": "Aprovação"})

    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == project_id
    assert body["position"] == len(stage_ids)

    listed = await client.get(f"/stages/project/{project_id}")
    columns = listed.json()
    assert [column["position"] for column in columns] == list(range(len(stage_ids) + 1))
    assert columns[-1]["name"] == "Aprovação"


async def test_create_stage_forbidden_for_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, _ = await _create_board(client)
    member = await make_user(email="member@example.com")
    await _add_member(db_session, project_id, member, ProjectRole.MEMBER)

    await login_as(client, member.email)
    response = await client.post("/stages", json={"project_id": project_id, "name": "Nova"})

    assert response.status_code == 403


async def test_create_stage_forbidden_for_non_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
) -> None:
    await login_as(client, regular_user.email)
    project_id, _ = await _create_board(client)
    outsider = await make_user(email="outsider@example.com")

    await login_as(client, outsider.email)
    response = await client.post("/stages", json={"project_id": project_id, "name": "Nova"})

    assert response.status_code == 403


async def test_list_stages_allows_observer(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)
    observer = await make_user(email="observer@example.com")
    await _add_member(db_session, project_id, observer, ProjectRole.OBSERVER)

    await login_as(client, observer.email)
    response = await client.get(f"/stages/project/{project_id}")

    assert response.status_code == 200
    assert [column["id"] for column in response.json()] == stage_ids


async def test_list_stages_forbidden_for_non_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
) -> None:
    await login_as(client, regular_user.email)
    project_id, _ = await _create_board(client)
    outsider = await make_user(email="outsider@example.com")

    await login_as(client, outsider.email)
    response = await client.get(f"/stages/project/{project_id}")

    assert response.status_code == 403


async def test_get_stage_allows_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)
    member = await make_user(email="member@example.com")
    await _add_member(db_session, project_id, member, ProjectRole.MEMBER)

    await login_as(client, member.email)
    response = await client.get(f"/stages/{stage_ids[0]}")

    assert response.status_code == 200
    assert response.json()["id"] == stage_ids[0]


async def test_get_stage_forbidden_for_non_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
) -> None:
    await login_as(client, regular_user.email)
    _, stage_ids = await _create_board(client)
    outsider = await make_user(email="outsider@example.com")

    await login_as(client, outsider.email)
    response = await client.get(f"/stages/{stage_ids[0]}")

    assert response.status_code == 403


async def test_get_stage_not_found(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    response = await client.get("/stages/999999")
    assert response.status_code == 404


async def test_rename_stage_by_owner(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)

    response = await client.patch(f"/stages/{stage_ids[0]}", json={"name": "Backlog"})

    assert response.status_code == 200
    assert response.json()["name"] == "Backlog"

    listed = await client.get(f"/stages/project/{project_id}")
    assert listed.json()[0]["name"] == "Backlog"


async def test_rename_stage_forbidden_for_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)
    member = await make_user(email="member@example.com")
    await _add_member(db_session, project_id, member, ProjectRole.MEMBER)

    await login_as(client, member.email)
    response = await client.patch(f"/stages/{stage_ids[0]}", json={"name": "Backlog"})

    assert response.status_code == 403


async def test_rename_stage_not_found(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    response = await client.patch("/stages/999999", json={"name": "Backlog"})
    assert response.status_code == 404


async def test_delete_empty_stage_by_owner(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)

    response = await client.delete(f"/stages/{stage_ids[-1]}")

    assert response.status_code == 204
    listed = await client.get(f"/stages/project/{project_id}")
    assert [column["id"] for column in listed.json()] == stage_ids[:-1]


async def test_delete_stage_with_tasks_returns_400(
    client: AsyncClient, regular_user: User, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)
    db_session.add(Task(project_id=project_id, stage_id=stage_ids[0], title="Tarefa", position=0))
    await db_session.commit()

    response = await client.delete(f"/stages/{stage_ids[0]}")

    assert response.status_code == 400


async def test_delete_stage_forbidden_for_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)
    member = await make_user(email="member@example.com")
    await _add_member(db_session, project_id, member, ProjectRole.MEMBER)

    await login_as(client, member.email)
    response = await client.delete(f"/stages/{stage_ids[0]}")

    assert response.status_code == 403


async def test_delete_stage_not_found(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    response = await client.delete("/stages/999999")
    assert response.status_code == 404


async def test_reorder_stages_by_owner(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)
    reversed_ids = list(reversed(stage_ids))

    response = await client.put(
        f"/stages/project/{project_id}/reorder", json={"stage_ids": reversed_ids}
    )

    assert response.status_code == 200
    body = response.json()
    assert [column["id"] for column in body] == reversed_ids
    assert [column["position"] for column in body] == list(range(len(stage_ids)))

    listed = await client.get(f"/stages/project/{project_id}")
    assert [column["id"] for column in listed.json()] == reversed_ids


async def test_reorder_stages_rejects_incomplete_ids(
    client: AsyncClient, regular_user: User
) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)

    response = await client.put(
        f"/stages/project/{project_id}/reorder", json={"stage_ids": stage_ids[:-1]}
    )

    assert response.status_code == 400


async def test_reorder_stages_forbidden_for_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, stage_ids = await _create_board(client)
    member = await make_user(email="member@example.com")
    await _add_member(db_session, project_id, member, ProjectRole.MEMBER)

    await login_as(client, member.email)
    response = await client.put(
        f"/stages/project/{project_id}/reorder", json={"stage_ids": list(reversed(stage_ids))}
    )

    assert response.status_code == 403
