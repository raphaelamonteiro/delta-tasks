from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    GlobalRole,
    Notification,
    NotificationStatus,
    NotificationType,
    Project,
    ProjectMember,
    ProjectRole,
    Stage,
    Task,
    TaskHistory,
    User,
)
from app.domains.tasks.repository import TaskRepository


@pytest.fixture
def repo(db_session: AsyncSession) -> TaskRepository:
    return TaskRepository(db_session)


async def _make_user(db_session: AsyncSession, email: str) -> User:
    user = User(name="User", email=email, password_hash="x", global_role=GlobalRole.USER)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _make_project_with_task(db_session: AsyncSession, owner: User) -> tuple[Project, Task]:
    project = Project(name="Quadro", owner_id=owner.id)
    project.members.append(ProjectMember(user_id=owner.id, role=ProjectRole.OWNER))
    project.stages = [Stage(name="Pendente", position=0)]
    db_session.add(project)
    await db_session.commit()

    task = Task(
        project_id=project.id,
        stage_id=project.stages[0].id,
        title="Tarefa",
        position=0,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return project, task


async def _make_board_with_task(
    db_session: AsyncSession, owner: User
) -> tuple[Project, list[Stage], Task]:
    project = Project(name="Quadro", owner_id=owner.id)
    project.members.append(ProjectMember(user_id=owner.id, role=ProjectRole.OWNER))
    project.stages = [Stage(name="Pendente", position=0), Stage(name="Em Progresso", position=1)]
    db_session.add(project)
    await db_session.commit()

    task = Task(project_id=project.id, stage_id=project.stages[0].id, title="Tarefa", position=0)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return project, list(project.stages), task


async def test_get_returns_task_or_none(repo: TaskRepository, db_session: AsyncSession) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    _, task = await _make_project_with_task(db_session, owner)

    fetched = await repo.get(task.id)
    assert fetched is not None
    assert fetched.id == task.id
    assert await repo.get(999999) is None


async def test_assign_responsible_to_member_persists_and_enqueues_notification(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    _, task = await _make_project_with_task(db_session, owner)

    assigned = await repo.assign_responsible(task, owner.id)

    assert assigned is True
    assert task.responsible_id == owner.id

    db_session.expunge_all()
    reloaded = await repo.get(task.id)
    assert reloaded is not None
    assert reloaded.responsible_id == owner.id

    result = await db_session.execute(select(Notification).where(Notification.task_id == task.id))
    notifications = result.scalars().all()
    assert len(notifications) == 1
    notification = notifications[0]
    assert notification.recipient_id == owner.id
    assert notification.type is NotificationType.ASSIGNMENT
    assert notification.status is NotificationStatus.PENDING


async def test_assign_responsible_non_member_returns_false_and_persists_nothing(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    _, task = await _make_project_with_task(db_session, owner)
    outsider = await _make_user(db_session, "outsider@example.com")

    assigned = await repo.assign_responsible(task, outsider.id)

    assert assigned is False
    assert task.responsible_id is None

    db_session.expunge_all()
    reloaded = await repo.get(task.id)
    assert reloaded is not None
    assert reloaded.responsible_id is None

    notifications = await db_session.scalars(
        select(Notification).where(Notification.task_id == task.id)
    )
    assert notifications.all() == []


async def test_update_persists_changes(repo: TaskRepository, db_session: AsyncSession) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    _, task = await _make_project_with_task(db_session, owner)

    updated = await repo.update(
        task, {"title": "Novo", "description": "desc", "due_date": date(2026, 12, 31)}
    )

    assert updated.title == "Novo"
    assert updated.description == "desc"
    assert updated.due_date == date(2026, 12, 31)

    db_session.expunge_all()
    reloaded = await repo.get(task.id)
    assert reloaded is not None
    assert reloaded.title == "Novo"
    assert reloaded.description == "desc"
    assert reloaded.due_date == date(2026, 12, 31)


async def test_update_clears_nullable_fields(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    _, task = await _make_project_with_task(db_session, owner)
    await repo.update(task, {"description": "desc", "due_date": date(2026, 12, 31)})

    await repo.update(task, {"description": None, "due_date": None})

    db_session.expunge_all()
    reloaded = await repo.get(task.id)
    assert reloaded is not None
    assert reloaded.description is None
    assert reloaded.due_date is None


async def test_get_stages_returns_requested_stages(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    _, stages, _ = await _make_board_with_task(db_session, owner)

    found = await repo.get_stages({stages[0].id, stages[1].id})

    assert set(found) == {stages[0].id, stages[1].id}
    assert found[stages[1].id].name == "Em Progresso"


async def test_move_to_stage_persists_and_records_history(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    _, stages, task = await _make_board_with_task(db_session, owner)
    source, dest = stages[0], stages[1]

    moved = await repo.move_to_stage(task, source, dest, owner.id, set())

    assert moved.stage_id == dest.id

    db_session.expunge_all()
    reloaded = await repo.get(task.id)
    assert reloaded is not None
    assert reloaded.stage_id == dest.id

    result = await db_session.execute(select(TaskHistory).where(TaskHistory.task_id == task.id))
    records = result.scalars().all()
    assert len(records) == 1
    record = records[0]
    assert record.from_stage_id == source.id
    assert record.to_stage_id == dest.id
    assert record.from_stage_name == "Pendente"
    assert record.to_stage_name == "Em Progresso"
    assert record.author_id == owner.id
    assert record.created_at is not None


async def test_move_to_stage_appends_to_end_of_destination(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    project, stages, task = await _make_board_with_task(db_session, owner)
    db_session.add(
        Task(project_id=project.id, stage_id=stages[1].id, title="Existente", position=0)
    )
    await db_session.commit()

    moved = await repo.move_to_stage(task, stages[0], stages[1], owner.id, set())

    assert moved.position == 1


async def test_move_to_stage_enqueues_one_notification_per_recipient(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    member = await _make_user(db_session, "member@example.com")
    _, stages, task = await _make_board_with_task(db_session, owner)

    await repo.move_to_stage(task, stages[0], stages[1], member.id, {owner.id, member.id})

    result = await db_session.execute(select(Notification).where(Notification.task_id == task.id))
    notifications = result.scalars().all()
    assert {n.recipient_id for n in notifications} == {owner.id, member.id}
    assert all(n.type is NotificationType.COLUMN_CHANGE for n in notifications)


async def test_move_to_stage_without_recipients_enqueues_nothing(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    _, stages, task = await _make_board_with_task(db_session, owner)

    await repo.move_to_stage(task, stages[0], stages[1], owner.id, set())

    notifications = await db_session.scalars(
        select(Notification).where(Notification.task_id == task.id)
    )
    assert notifications.all() == []


async def test_get_project_owner_id_returns_owner(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    project, _, _ = await _make_board_with_task(db_session, owner)

    assert await repo.get_project_owner_id(project.id) == owner.id


async def test_list_history_returns_chronological_with_author(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    _, stages, task = await _make_board_with_task(db_session, owner)
    await repo.move_to_stage(task, stages[0], stages[1], owner.id, set())
    await repo.move_to_stage(task, stages[1], stages[0], owner.id, set())

    db_session.expunge_all()
    history = await repo.list_history(task.id)

    assert [(record.from_stage_name, record.to_stage_name) for record in history] == [
        ("Pendente", "Em Progresso"),
        ("Em Progresso", "Pendente"),
    ]
    assert history[0].author.name == "User"
    assert history[0].created_at <= history[1].created_at


async def test_list_history_empty_for_task_without_movements(
    repo: TaskRepository, db_session: AsyncSession
) -> None:
    owner = await _make_user(db_session, "owner@example.com")
    _, task = await _make_project_with_task(db_session, owner)

    assert await repo.list_history(task.id) == []
