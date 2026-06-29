from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Notification,
    NotificationType,
    ProjectMember,
    ProjectRole,
    Task,
    TaskHistory,
    User,
)
from tests.conftest import UserFactory, login_as


async def _create_board_with_task(
    client: AsyncClient, db_session: AsyncSession
) -> tuple[int, int, list[int]]:
    """Create a project (owner = logged-in user) with a task in its first column.

    Returns ``(project_id, task_id, stage_ids)`` where ``stage_ids`` are the board columns
    in order.
    """
    created = await client.post("/projects", json={"name": "Quadro"})
    body = created.json()
    project_id = body["id"]
    stage_ids = [column["id"] for column in body["columns"]]

    task = Task(project_id=project_id, stage_id=stage_ids[0], title="Tarefa", position=0)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return project_id, task.id, stage_ids


async def _create_project_with_task(
    client: AsyncClient, db_session: AsyncSession
) -> tuple[int, int]:
    project_id, task_id, _ = await _create_board_with_task(client, db_session)
    return project_id, task_id


async def _add_member(
    db_session: AsyncSession, project_id: int, user: User, role: ProjectRole
) -> None:
    db_session.add(ProjectMember(project_id=project_id, user_id=user.id, role=role))
    await db_session.commit()


async def test_assign_responsible_requires_authentication(client: AsyncClient) -> None:
    response = await client.patch("/tasks/1/responsible", json={"responsible_id": str(uuid4())})
    assert response.status_code == 401


async def test_assign_responsible_success(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id = await _create_project_with_task(client, db_session)
    member = await make_user(email="member@example.com")
    await _add_member(db_session, project_id, member, ProjectRole.MEMBER)

    response = await client.patch(
        f"/tasks/{task_id}/responsible", json={"responsible_id": str(member.id)}
    )

    assert response.status_code == 200
    assert response.json()["responsible_id"] == str(member.id)
    assert response.json()["id"] == task_id

    # The board reflects the new responsible immediately.
    board = await client.get(f"/projects/{project_id}")
    card = board.json()["columns"][0]["tasks"][0]
    assert card["responsible_id"] == str(member.id)


async def test_assign_responsible_enqueues_email_notification(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id = await _create_project_with_task(client, db_session)
    member = await make_user(email="member@example.com")
    await _add_member(db_session, project_id, member, ProjectRole.MEMBER)

    await client.patch(f"/tasks/{task_id}/responsible", json={"responsible_id": str(member.id)})

    result = await db_session.execute(select(Notification).where(Notification.task_id == task_id))
    notification = result.scalar_one()
    assert notification.recipient_id == member.id
    assert notification.type is NotificationType.ASSIGNMENT


async def test_assign_responsible_who_is_not_member_returns_400(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id = await _create_project_with_task(client, db_session)
    outsider = await make_user(email="outsider@example.com")

    response = await client.patch(
        f"/tasks/{task_id}/responsible", json={"responsible_id": str(outsider.id)}
    )

    assert response.status_code == 400
    notifications = await db_session.scalars(
        select(Notification).where(Notification.task_id == task_id)
    )
    assert notifications.all() == []
    updated = await db_session.get(Task, task_id)
    assert updated is not None
    assert updated.responsible_id is None


async def test_assign_responsible_forbidden_for_observer(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id = await _create_project_with_task(client, db_session)
    observer = await make_user(email="observer@example.com")
    await _add_member(db_session, project_id, observer, ProjectRole.OBSERVER)
    target = await make_user(email="member@example.com")
    await _add_member(db_session, project_id, target, ProjectRole.MEMBER)

    await login_as(client, observer.email)
    response = await client.patch(
        f"/tasks/{task_id}/responsible", json={"responsible_id": str(target.id)}
    )

    assert response.status_code == 403


async def test_assign_responsible_forbidden_for_non_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id = await _create_project_with_task(client, db_session)
    outsider = await make_user(email="outsider@example.com")

    await login_as(client, outsider.email)
    response = await client.patch(
        f"/tasks/{task_id}/responsible", json={"responsible_id": str(outsider.id)}
    )

    assert response.status_code == 403


async def test_assign_responsible_substitutes_previous(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id = await _create_project_with_task(client, db_session)
    first = await make_user(email="first@example.com")
    second = await make_user(email="second@example.com")
    await _add_member(db_session, project_id, first, ProjectRole.MEMBER)
    await _add_member(db_session, project_id, second, ProjectRole.MEMBER)

    await client.patch(f"/tasks/{task_id}/responsible", json={"responsible_id": str(first.id)})
    response = await client.patch(
        f"/tasks/{task_id}/responsible", json={"responsible_id": str(second.id)}
    )

    assert response.status_code == 200
    assert response.json()["responsible_id"] == str(second.id)
    updated = await db_session.get(Task, task_id)
    assert updated is not None
    assert updated.responsible_id == second.id


async def test_assign_responsible_task_not_found(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    response = await client.patch(
        "/tasks/999999/responsible", json={"responsible_id": str(regular_user.id)}
    )
    assert response.status_code == 404


async def test_assign_responsible_invalid_uuid_returns_400(
    client: AsyncClient,
    regular_user: User,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    _, task_id = await _create_project_with_task(client, db_session)

    response = await client.patch(
        f"/tasks/{task_id}/responsible", json={"responsible_id": "not-a-uuid"}
    )
    assert response.status_code == 400


# --------------------------------------------------------------------------- #
# US-013: Mover tarefa entre colunas
# --------------------------------------------------------------------------- #


async def test_move_task_requires_authentication(client: AsyncClient) -> None:
    response = await client.patch("/tasks/1/stage", json={"stage_id": 1})
    assert response.status_code == 401


async def test_move_task_success_updates_board_and_records_history(
    client: AsyncClient, regular_user: User, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id, stages = await _create_board_with_task(client, db_session)

    response = await client.patch(f"/tasks/{task_id}/stage", json={"stage_id": stages[1]})

    assert response.status_code == 200
    assert response.json()["stage_id"] == stages[1]

    # The board reflects the move immediately.
    board = await client.get(f"/projects/{project_id}")
    columns = board.json()["columns"]
    assert columns[0]["tasks"] == []
    assert [task["id"] for task in columns[1]["tasks"]] == [task_id]

    result = await db_session.execute(select(TaskHistory).where(TaskHistory.task_id == task_id))
    records = result.scalars().all()
    assert len(records) == 1
    record = records[0]
    assert record.from_stage_id == stages[0]
    assert record.to_stage_id == stages[1]
    assert record.from_stage_name == "Pendente"
    assert record.to_stage_name == "Em Progresso"
    assert record.author_id == regular_user.id


async def test_move_task_notifies_responsible(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id, stages = await _create_board_with_task(client, db_session)
    member = await make_user(email="member@example.com")
    await _add_member(db_session, project_id, member, ProjectRole.MEMBER)
    await client.patch(f"/tasks/{task_id}/responsible", json={"responsible_id": str(member.id)})

    await client.patch(f"/tasks/{task_id}/stage", json={"stage_id": stages[1]})

    result = await db_session.execute(
        select(Notification).where(
            Notification.task_id == task_id,
            Notification.type == NotificationType.COLUMN_CHANGE,
        )
    )
    notifications = result.scalars().all()
    assert len(notifications) == 1
    assert notifications[0].recipient_id == member.id


async def test_move_task_to_other_project_column_returns_400(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    _, task_id, stages = await _create_board_with_task(client, db_session)

    other = await make_user(email="other@example.com")
    await login_as(client, other.email)
    other_board = await client.post("/projects", json={"name": "Outro"})
    other_stage = other_board.json()["columns"][1]["id"]

    await login_as(client, regular_user.email)
    response = await client.patch(f"/tasks/{task_id}/stage", json={"stage_id": other_stage})

    assert response.status_code == 400
    updated = await db_session.get(Task, task_id)
    assert updated is not None
    assert updated.stage_id == stages[0]


async def test_move_task_forbidden_for_observer(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id, stages = await _create_board_with_task(client, db_session)
    observer = await make_user(email="observer@example.com")
    await _add_member(db_session, project_id, observer, ProjectRole.OBSERVER)

    await login_as(client, observer.email)
    response = await client.patch(f"/tasks/{task_id}/stage", json={"stage_id": stages[1]})

    assert response.status_code == 403


async def test_move_task_forbidden_for_non_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    _, task_id, stages = await _create_board_with_task(client, db_session)
    outsider = await make_user(email="outsider@example.com")

    await login_as(client, outsider.email)
    response = await client.patch(f"/tasks/{task_id}/stage", json={"stage_id": stages[1]})

    assert response.status_code == 403


async def test_move_task_not_found(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    response = await client.patch("/tasks/999999/stage", json={"stage_id": 1})
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# US-011: Editar tarefa
# --------------------------------------------------------------------------- #


async def test_update_task_requires_authentication(client: AsyncClient) -> None:
    response = await client.patch("/tasks/1", json={"title": "X"})
    assert response.status_code == 401


async def test_update_task_success_reflects_on_board(
    client: AsyncClient, regular_user: User, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id = await _create_project_with_task(client, db_session)

    response = await client.patch(
        f"/tasks/{task_id}",
        json={"title": "Novo título", "description": "Nova desc", "due_date": "2026-12-31"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Novo título"
    assert body["description"] == "Nova desc"
    assert body["due_date"] == "2026-12-31"

    board = await client.get(f"/projects/{project_id}")
    card = board.json()["columns"][0]["tasks"][0]
    assert card["title"] == "Novo título"
    assert card["due_date"] == "2026-12-31"


async def test_update_task_invalid_due_date_returns_400(
    client: AsyncClient, regular_user: User, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    _, task_id = await _create_project_with_task(client, db_session)

    response = await client.patch(f"/tasks/{task_id}", json={"due_date": "invalid-date"})

    assert response.status_code == 400
    assert any("due_date" in error.get("loc", []) for error in response.json()["detail"])


async def test_update_task_empty_title_returns_400(
    client: AsyncClient, regular_user: User, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    _, task_id = await _create_project_with_task(client, db_session)

    response = await client.patch(f"/tasks/{task_id}", json={"title": ""})
    assert response.status_code == 400


async def test_update_task_null_due_date_clears_it(
    client: AsyncClient, regular_user: User, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    _, task_id = await _create_project_with_task(client, db_session)
    await client.patch(f"/tasks/{task_id}", json={"due_date": "2026-12-31"})

    response = await client.patch(f"/tasks/{task_id}", json={"due_date": None})

    assert response.status_code == 200
    assert response.json()["due_date"] is None


async def test_update_task_null_title_is_ignored(
    client: AsyncClient, regular_user: User, db_session: AsyncSession
) -> None:
    await login_as(client, regular_user.email)
    _, task_id = await _create_project_with_task(client, db_session)

    response = await client.patch(f"/tasks/{task_id}", json={"title": None})

    assert response.status_code == 200
    assert response.json()["title"] == "Tarefa"


async def test_update_task_not_found(client: AsyncClient, regular_user: User) -> None:
    await login_as(client, regular_user.email)
    response = await client.patch("/tasks/999999", json={"title": "X"})
    assert response.status_code == 404


async def test_update_task_forbidden_for_observer(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    project_id, task_id = await _create_project_with_task(client, db_session)
    observer = await make_user(email="observer@example.com")
    await _add_member(db_session, project_id, observer, ProjectRole.OBSERVER)

    await login_as(client, observer.email)
    response = await client.patch(f"/tasks/{task_id}", json={"title": "Hack"})

    assert response.status_code == 403


async def test_update_task_forbidden_for_non_member(
    client: AsyncClient,
    regular_user: User,
    make_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    await login_as(client, regular_user.email)
    _, task_id = await _create_project_with_task(client, db_session)
    outsider = await make_user(email="outsider@example.com")

    await login_as(client, outsider.email)
    response = await client.patch(f"/tasks/{task_id}", json={"title": "Hack"})

    assert response.status_code == 403
