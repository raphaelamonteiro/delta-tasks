from typing import Any

from fastapi import status

from app.domains.projects.schemas import (
    ProjectBoardResponse,
    ProjectMemberResponse,
    ProjectSummaryResponse,
)

create_project_swagger: dict[str, Any] = {
    "summary": "Criar projeto",
    "description": (
        "Cria um projeto e gera automaticamente o quadro Kanban com as colunas "
        "padrão. O usuário autenticado é registrado como membro DONO do projeto. "
        "Passo 3 do fluxo de demonstração: crie o quadro e guarde o `id` retornado."
    ),
    "status_code": status.HTTP_201_CREATED,
    "response_model": ProjectBoardResponse,
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "name": "Quadro de Demonstração",
                        "description": "Projeto usado para apresentar o fluxo do Delta Tasks.",
                    }
                }
            }
        }
    },
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
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "name": "Quadro de Demonstração (revisado)",
                        "description": "Escopo ajustado durante a apresentação.",
                    }
                }
            }
        }
    },
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

# UUID fictício apenas para ilustrar o corpo das requisições no Swagger.
_EXAMPLE_USER_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

list_members_swagger: dict[str, Any] = {
    "summary": "Listar membros do projeto",
    "description": (
        "Retorna os membros do projeto com seus papéis. Restrito a membros do "
        "projeto (ou admin global) (RN-003)."
    ),
    "response_model": list[ProjectMemberResponse],
    "responses": {
        200: {"description": "Membros do projeto."},
        401: {"description": "Não autenticado."},
        403: {"description": "Não é membro do projeto."},
        404: {"description": "Projeto não encontrado."},
    },
}

add_member_swagger: dict[str, Any] = {
    "summary": "Adicionar membro ao projeto",
    "description": (
        "Adiciona um usuário existente ao projeto com o papel MEMBRO ou OBSERVADOR. "
        "Restrito ao dono do projeto (RN-009). "
        "Passo 4 do fluxo de demonstração: use no path o `id` do projeto (passo 3) e, "
        "no corpo, o `user_id` retornado pelo register (passo 2)."
    ),
    "status_code": status.HTTP_201_CREATED,
    "response_model": ProjectMemberResponse,
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {"user_id": _EXAMPLE_USER_ID, "role": "member"}
                }
            }
        }
    },
    "responses": {
        201: {"description": "Membro adicionado."},
        400: {"description": "Falha de validação (ex.: papel inválido)."},
        401: {"description": "Não autenticado."},
        403: {"description": "Apenas o dono pode gerenciar os membros."},
        404: {"description": "Projeto ou usuário não encontrado."},
        409: {"description": "Usuário já é membro do projeto."},
    },
}

update_member_role_swagger: dict[str, Any] = {
    "summary": "Alterar papel de um membro",
    "description": (
        "Atualiza o papel de um membro (MEMBRO ou OBSERVADOR). Restrito ao dono do "
        "projeto (RN-009). O papel do dono não pode ser alterado. "
        "Passo 5 do fluxo de demonstração: reutilize o `id` do projeto e o `user_id` do "
        "membro adicionado no passo 4."
    ),
    "response_model": ProjectMemberResponse,
    "openapi_extra": {
        "requestBody": {
            "content": {"application/json": {"example": {"role": "observer"}}}
        }
    },
    "responses": {
        200: {"description": "Papel atualizado."},
        400: {"description": "Falha de validação ou tentativa de alterar o dono."},
        401: {"description": "Não autenticado."},
        403: {"description": "Apenas o dono pode gerenciar os membros."},
        404: {"description": "Projeto ou membro não encontrado."},
    },
}

remove_member_swagger: dict[str, Any] = {
    "summary": "Remover membro do projeto",
    "description": (
        "Remove um membro do projeto, revogando seu acesso ao quadro. Restrito ao "
        "dono do projeto (RN-009). O dono não pode ser removido."
    ),
    "status_code": status.HTTP_204_NO_CONTENT,
    "responses": {
        204: {"description": "Membro removido."},
        400: {"description": "Tentativa de remover o dono."},
        401: {"description": "Não autenticado."},
        403: {"description": "Apenas o dono pode gerenciar os membros."},
        404: {"description": "Projeto ou membro não encontrado."},
    },
}
