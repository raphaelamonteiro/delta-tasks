from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.db.models import Project
from app.domains.auth.dependencies import CurrentUserDep, get_current_user
from app.domains.auth.principal import CurrentUser
from app.domains.projects.dependencies import ProjectServiceDep
from app.domains.projects.exceptions import (
    DuplicateMemberError,
    MemberUserNotFoundError,
    OwnerMembershipError,
    ProjectMemberNotFoundError,
    ProjectNotFoundError,
)
from app.domains.projects.schemas import (
    AddMemberDTO,
    CreateProjectDTO,
    ProjectBoardResponse,
    ProjectMemberResponse,
    ProjectSummaryResponse,
    UpdateMemberRoleDTO,
    UpdateProjectDTO,
)
from app.domains.projects.swagger_utils import (
    add_member_swagger,
    create_project_swagger,
    delete_project_swagger,
    get_board_swagger,
    list_members_swagger,
    list_projects_swagger,
    remove_member_swagger,
    update_member_role_swagger,
    update_project_swagger,
)

logger = get_logger("app.projects.router")

projects_router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
    dependencies=[Depends(get_current_user)],
)


@projects_router.post("", **create_project_swagger)
async def create_project(
    dto: CreateProjectDTO,
    user: CurrentUserDep,
    service: ProjectServiceDep,
) -> ProjectBoardResponse:
    project = await service.create_project(user.id, dto)
    return ProjectBoardResponse.from_project(project)


@projects_router.get("", **list_projects_swagger)
async def list_projects(
    user: CurrentUserDep,
    service: ProjectServiceDep,
) -> list[ProjectSummaryResponse]:
    projects = await service.list_user_projects(user.id)
    return [ProjectSummaryResponse.model_validate(project) for project in projects]


@projects_router.get("/{project_id}", **get_board_swagger)
async def get_board(
    project_id: int,
    user: CurrentUserDep,
    service: ProjectServiceDep,
) -> ProjectBoardResponse:
    try:
        project = await service.get_board(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        ) from exc

    # RN-003: apenas membros (ou admin global) acessam o quadro.
    if not (user.is_admin or user.is_member(project_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project.",
        )

    return ProjectBoardResponse.from_project(project)


def _require_owner(project: Project, user: CurrentUser) -> None:
    if project.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can manage this project.",
        )


@projects_router.patch("/{project_id}", **update_project_swagger)
async def update_project(
    project_id: int,
    dto: UpdateProjectDTO,
    user: CurrentUserDep,
    service: ProjectServiceDep,
) -> ProjectSummaryResponse:
    try:
        project = await service.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        ) from exc

    _require_owner(project, user)

    project = await service.update_project(project, dto)
    return ProjectSummaryResponse.model_validate(project)


@projects_router.delete("/{project_id}", **delete_project_swagger)
async def delete_project(
    project_id: int,
    user: CurrentUserDep,
    service: ProjectServiceDep,
) -> None:
    try:
        project = await service.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        ) from exc

    _require_owner(project, user)

    await service.delete_project(project)


async def _load_project(project_id: int, service: ProjectServiceDep) -> Project:
    try:
        return await service.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        ) from exc


@projects_router.get("/{project_id}/members", **list_members_swagger)
async def list_members(
    project_id: int,
    user: CurrentUserDep,
    service: ProjectServiceDep,
) -> list[ProjectMemberResponse]:
    project = await _load_project(project_id, service)

    # RN-003: apenas membros (ou admin global) veem a composição do projeto.
    if not (user.is_admin or user.is_member(project.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project.",
        )

    members = await service.list_members(project.id)
    return [ProjectMemberResponse.from_member(member) for member in members]


@projects_router.post("/{project_id}/members", **add_member_swagger)
async def add_member(
    project_id: int,
    dto: AddMemberDTO,
    user: CurrentUserDep,
    service: ProjectServiceDep,
) -> ProjectMemberResponse:
    project = await _load_project(project_id, service)
    _require_owner(project, user)

    try:
        member = await service.add_member(project.id, dto.user_id, dto.role)
    except MemberUserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        ) from exc
    except DuplicateMemberError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project.",
        ) from exc

    return ProjectMemberResponse.from_member(member)


@projects_router.patch("/{project_id}/members/{user_id}", **update_member_role_swagger)
async def update_member_role(
    project_id: int,
    user_id: UUID,
    dto: UpdateMemberRoleDTO,
    user: CurrentUserDep,
    service: ProjectServiceDep,
) -> ProjectMemberResponse:
    project = await _load_project(project_id, service)
    _require_owner(project, user)

    try:
        member = await service.update_member_role(project.id, user_id, dto.role)
    except ProjectMemberNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this project.",
        ) from exc
    except OwnerMembershipError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The project owner's role cannot be changed.",
        ) from exc

    return ProjectMemberResponse.from_member(member)


@projects_router.delete("/{project_id}/members/{user_id}", **remove_member_swagger)
async def remove_member(
    project_id: int,
    user_id: UUID,
    user: CurrentUserDep,
    service: ProjectServiceDep,
) -> None:
    project = await _load_project(project_id, service)
    _require_owner(project, user)

    try:
        await service.remove_member(project.id, user_id)
    except ProjectMemberNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this project.",
        ) from exc
    except OwnerMembershipError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The project owner cannot be removed.",
        ) from exc
