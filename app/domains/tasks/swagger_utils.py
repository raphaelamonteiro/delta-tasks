from typing import Any

from app.domains.tasks.schemas import TaskResponse

assign_responsible_swagger: dict[str, Any] = {
    "summary": "Atribuir responsável à tarefa",
    "description": (
        "Define o responsável por uma tarefa (RN-006). O responsável indicado deve ser "
        "membro do mesmo projeto da tarefa. Substitui o responsável anterior, caso exista, "
        "e enfileira uma notificação por e-mail para o novo responsável (RN-008). Restrito a "
        "membros do projeto com papel DONO ou MEMBRO (RN-003)."
    ),
    "response_model": TaskResponse,
    "responses": {
        200: {"description": "Responsável atribuído com sucesso."},
        400: {"description": "O responsável indicado não é membro do projeto."},
        401: {"description": "Não autenticado."},
        403: {"description": "Sem permissão para alterar o responsável (ex.: Observador)."},
        404: {"description": "Tarefa não encontrada."},
    },
}
