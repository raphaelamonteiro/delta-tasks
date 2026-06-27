from dataclasses import dataclass
from uuid import UUID

from app.db.models import GlobalRole, ProjectRole, User


@dataclass(frozen=True, slots=True)
class CurrentUser:
    """Authenticated principal, válido durante uma única requisição.

    Carrega o ``User`` autenticado junto com um snapshot dos vínculos de projeto
    (``project_id`` -> papel), pré-carregado no momento da autenticação. Assim os
    demais módulos autorizam o acesso a um projeto via :meth:`role_in` /
    :meth:`is_member` sem emitir consultas adicionais ao banco.
    """

    user: User
    project_roles: dict[int, ProjectRole]

    @classmethod
    def from_user(cls, user: User) -> "CurrentUser":
        return cls(user=user, project_roles={m.project_id: m.role for m in user.memberships})

    @property
    def id(self) -> UUID:
        return self.user.id

    @property
    def name(self) -> str:
        return self.user.name

    @property
    def email(self) -> str:
        return self.user.email

    @property
    def global_role(self) -> GlobalRole:
        return self.user.global_role

    @property
    def is_active(self) -> bool:
        return self.user.is_active

    @property
    def is_admin(self) -> bool:
        return self.user.global_role == GlobalRole.ADMIN

    def role_in(self, project_id: int) -> ProjectRole | None:
        """Papel do usuário no projeto, ou ``None`` se não for membro."""
        return self.project_roles.get(project_id)

    def is_member(self, project_id: int) -> bool:
        return project_id in self.project_roles
