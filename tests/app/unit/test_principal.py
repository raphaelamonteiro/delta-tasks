from collections.abc import Sequence
from uuid import uuid4

from app.db.models import GlobalRole, ProjectMember, ProjectRole, User
from app.domains.auth.principal import CurrentUser


def build_user(
    *, role: GlobalRole = GlobalRole.USER, memberships: Sequence[ProjectMember] = ()
) -> User:
    return User(
        id=uuid4(),
        name="User",
        email="user@example.com",
        password_hash="x",
        global_role=role,
        is_active=True,
        memberships=list(memberships),
    )


def test_from_user_maps_project_roles() -> None:
    user = build_user(
        memberships=[
            ProjectMember(project_id=1, role=ProjectRole.OWNER),
            ProjectMember(project_id=2, role=ProjectRole.OBSERVER),
        ]
    )

    principal = CurrentUser.from_user(user)

    assert principal.project_roles == {1: ProjectRole.OWNER, 2: ProjectRole.OBSERVER}


def test_role_in_returns_role_or_none() -> None:
    principal = CurrentUser.from_user(
        build_user(memberships=[ProjectMember(project_id=7, role=ProjectRole.MEMBER)])
    )

    assert principal.role_in(7) is ProjectRole.MEMBER
    assert principal.role_in(999) is None


def test_is_member_reflects_membership() -> None:
    principal = CurrentUser.from_user(
        build_user(memberships=[ProjectMember(project_id=7, role=ProjectRole.MEMBER)])
    )

    assert principal.is_member(7) is True
    assert principal.is_member(999) is False


def test_user_without_memberships_has_empty_roles() -> None:
    principal = CurrentUser.from_user(build_user())

    assert principal.project_roles == {}
    assert principal.is_member(1) is False


def test_delegates_identity_fields() -> None:
    user = build_user()
    principal = CurrentUser.from_user(user)

    assert principal.id == user.id
    assert principal.name == user.name
    assert principal.email == user.email
    assert principal.global_role is GlobalRole.USER
    assert principal.is_active is True


def test_is_admin_distinguishes_global_role() -> None:
    assert CurrentUser.from_user(build_user(role=GlobalRole.ADMIN)).is_admin is True
    assert CurrentUser.from_user(build_user(role=GlobalRole.USER)).is_admin is False
