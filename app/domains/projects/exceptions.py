from uuid import UUID


class ProjectError(Exception):
    """Base error for the projects domain."""


class ProjectNotFoundError(ProjectError):
    def __init__(self, project_id: int) -> None:
        self.project_id = project_id
        super().__init__(f"Project not found: {project_id}")


class MemberUserNotFoundError(ProjectError):
    """O usuário que se tentou adicionar não existe (US-008, Cenário 4)."""

    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        super().__init__(f"User not found: {user_id}")


class ProjectMemberNotFoundError(ProjectError):
    """O usuário informado não é membro do projeto."""

    def __init__(self, project_id: int, user_id: UUID) -> None:
        self.project_id = project_id
        self.user_id = user_id
        super().__init__(f"User {user_id} is not a member of project {project_id}")


class DuplicateMemberError(ProjectError):
    """Tentativa de adicionar um usuário que já é membro (US-008, Cenário 6)."""

    def __init__(self, project_id: int, user_id: UUID) -> None:
        self.project_id = project_id
        self.user_id = user_id
        super().__init__(f"User {user_id} is already a member of project {project_id}")


class OwnerMembershipError(ProjectError):
    """O vínculo do dono não pode ter o papel alterado nem ser removido (RN-009)."""

    def __init__(self, project_id: int, user_id: UUID) -> None:
        self.project_id = project_id
        self.user_id = user_id
        super().__init__(f"The owner membership of project {project_id} cannot be modified")
