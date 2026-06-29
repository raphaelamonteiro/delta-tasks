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
