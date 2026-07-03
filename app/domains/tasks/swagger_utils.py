from typing import Any
from fastapi import status
from app.domains.tasks.schemas import TaskHistoryResponse, TaskResponse

create_task_swagger: dict[str, Any] = {
    "summary": "Criar tarefa",
    "description": (
        "Cria uma tarefa em uma coluna do quadro. Restrito a membros com papel DONO ou "
        "MEMBRO (RN-004). Passo 8 do fluxo de demonstração: use o `project_id` do passo 3 "
        "e o `stage_id` de uma coluna do quadro (resposta do passo 3 ou a coluna criada "
        "no passo 7). Guarde o `id` da tarefa retornado."
    ),
    "status_code": status.HTTP_201_CREATED,
    "response_model": TaskResponse,
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "title": "Configurar pipeline de CI",
                        "description": "Rodar testes e lint a cada push.",
                        "due_date": "2026-07-31",
                        "position": 0,
                        "project_id": 1,
                        "stage_id": 1,
                    }
                }
            }
        }
    },
    "responses": {
        201: {"description": "Tarefa criada com sucesso."},
        401: {"description": "Não autenticado."},
        403: {"description": "Sem permissão para criar tarefas neste projeto."},
        400: {"description": "Falha de validação (ex.: nome ausente)."},
    },
}

get_task_history_swagger: dict[str, Any] = {
    "summary": "Visualizar histórico de movimentações",
    "description": (
        "Retorna, em ordem cronológica, os registros de movimentação da tarefa — coluna de "
        "origem, coluna de destino, autor e data/hora (RN-007). O histórico é imutável e "
        "append-only: não há endpoint de atualização ou remoção. Restrito a membros do "
        "projeto (RN-003)."
    ),
    "response_model": list[TaskHistoryResponse],
    "responses": {
        200: {"description": "Histórico da tarefa (lista vazia se não houve movimentações)."},
        401: {"description": "Não autenticado."},
        403: {"description": "Não é membro do projeto."},
        404: {"description": "Tarefa não encontrada."},
    },
}

update_task_swagger: dict[str, Any] = {
    "summary": "Editar tarefa",
    "description": (
        "Atualiza título, descrição e/ou prazo da tarefa. Campos omitidos não são alterados; "
        "``description`` e ``due_date`` podem ser enviados como ``null`` para limpar o valor. "
        "Restrito a membros do projeto com papel DONO ou MEMBRO (RN-004). "
        "Use no path o `id` da tarefa criada no passo 8; envie apenas os campos a alterar."
    ),
    "response_model": TaskResponse,
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "title": "Configurar pipeline de CI/CD",
                        "due_date": "2026-08-15",
                    }
                }
            }
        }
    },
    "responses": {
        200: {"description": "Tarefa atualizada com sucesso."},
        400: {"description": "Falha de validação (ex.: prazo em formato inválido)."},
        401: {"description": "Não autenticado."},
        403: {"description": "Sem permissão para editar a tarefa (ex.: Observador)."},
        404: {"description": "Tarefa não encontrada."},
    },
}

assign_responsible_swagger: dict[str, Any] = {
    "summary": "Atribuir responsável à tarefa",
    "description": (
        "Define o responsável por uma tarefa (RN-006). O responsável indicado deve ser "
        "membro do mesmo projeto da tarefa. Substitui o responsável anterior, caso exista, "
        "e enfileira uma notificação por e-mail para o novo responsável (RN-008). Restrito a "
        "membros do projeto com papel DONO ou MEMBRO (RN-003). "
        "Passo 9 do fluxo de demonstração: use no path o `id` da tarefa (passo 8) e, no "
        "corpo, o `user_id` do membro registrado no passo 2 (já adicionado ao projeto no passo 4)."
    ),
    "response_model": TaskResponse,
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {"responsible_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"}
                }
            }
        }
    },
    "responses": {
        200: {"description": "Responsável atribuído com sucesso."},
        400: {"description": "O responsável indicado não é membro do projeto."},
        401: {"description": "Não autenticado."},
        403: {"description": "Sem permissão para alterar o responsável (ex.: Observador)."},
        404: {"description": "Tarefa não encontrada."},
    },
}

move_task_swagger: dict[str, Any] = {
    "summary": "Mover tarefa entre colunas",
    "description": (
        "Move a tarefa para outra coluna do mesmo quadro (RN-005), registra o histórico da "
        "movimentação — coluna de origem, coluna de destino, autor e data/hora (RN-007) — e "
        "enfileira notificações por e-mail para o responsável da tarefa e o dono do projeto, "
        "exceto para quem realizou a movimentação (RN-008). Restrito a membros do projeto com "
        "papel DONO ou MEMBRO (RN-003). "
        "Passo 10 do fluxo de demonstração: use no path o `id` da tarefa (passo 8) e, no corpo, "
        "o `stage_id` da coluna de destino (outra coluna do quadro — resposta do passo 3 ou 7)."
    ),
    "response_model": TaskResponse,
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {"example": {"stage_id": 2}}
            }
        }
    },
    "responses": {
        200: {"description": "Tarefa movida com sucesso."},
        400: {"description": "A coluna de destino não pertence ao projeto da tarefa."},
        401: {"description": "Não autenticado."},
        403: {"description": "Sem permissão para mover a tarefa (ex.: Observador)."},
        404: {"description": "Tarefa não encontrada."},
    },
}

delete_task_swagger: dict[str, Any] = {
    "summary": "Excluir tarefa",
    "description": (
        "Remove a tarefa e todas as suas associações (membros, comentários). "
    ),
    "status_code": status.HTTP_204_NO_CONTENT,
    "responses": {
        204: {"description": "Tarefa excluída."},
        401: {"description": "Não autenticado."},
        404: {"description": "Tarefa não encontrada."},
    },
}

