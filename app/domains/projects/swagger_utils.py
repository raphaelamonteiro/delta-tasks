from typing import Any

from fastapi import status

from app.domains.projects.schemas import ProjectBoardResponse, ProjectSummaryResponse

create_project_swagger: dict[str, Any] = {
    "summary": "Criar projeto",
    "description": (
        "Cria um projeto e gera automaticamente o quadro Kanban com as colunas "
        "padrão. O usuário autenticado é registrado como membro DONO do projeto."
    ),
    "status_code": status.HTTP_201_CREATED,
    "response_model": ProjectBoardResponse,
    "responses": {
        201: {"description": "Projeto criado com sucesso."},
        401: {"description": "Não autenticado."},
        400: {"description": "Falha de validação (ex.: nome ausente)."},
    },
}

list_projects_swagger: dict[str, Any] = {
    "summary": "Listar meus projetos",
    "description": "Retorna apenas os projetos dos quais o usuário autenticado é membro.",
    "response_model": list[ProjectSummaryResponse],
    "responses": {
        200: {"description": "Projetos do usuário."},
        401: {"description": "Não autenticado."},
    },
}

get_board_swagger: dict[str, Any] = {
    "summary": "Visualizar o quadro do projeto",
    "description": (
        "Retorna o quadro Kanban do projeto: colunas na ordem definida, cada uma "
        "com suas tarefas. Restrito a membros do projeto (ou admin global)."
    ),
    "response_model": ProjectBoardResponse,
    "responses": {
        200: {"description": "Quadro do projeto."},
        401: {"description": "Não autenticado."},
        403: {"description": "Não é membro do projeto."},
        404: {"description": "Projeto não encontrado."},
    },
}

update_project_swagger: dict[str, Any] = {
    "summary": "Editar projeto",
    "description": "Atualiza nome e/ou descrição. Restrito ao dono do projeto (RN-009).",
    "response_model": ProjectSummaryResponse,
    "responses": {
        200: {"description": "Projeto atualizado."},
        400: {"description": "Falha de validação."},
        401: {"description": "Não autenticado."},
        403: {"description": "Apenas o dono pode editar o projeto."},
        404: {"description": "Projeto não encontrado."},
    },
}

delete_project_swagger: dict[str, Any] = {
    "summary": "Excluir projeto",
    "description": (
        "Remove o projeto e todas as suas associações (membros, colunas e tarefas). "
        "Restrito ao dono do projeto (RN-009)."
    ),
    "status_code": status.HTTP_204_NO_CONTENT,
    "responses": {
        204: {"description": "Projeto excluído."},
        401: {"description": "Não autenticado."},
        403: {"description": "Apenas o dono pode excluir o projeto."},
        404: {"description": "Projeto não encontrado."},
    },
}
