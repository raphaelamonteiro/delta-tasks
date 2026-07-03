from typing import Any

from fastapi import status

from app.domains.stages.schemas import StageResponse

create_stage_swagger: dict[str, Any] = {
    "summary": "Criar coluna",
    "description": (
        "Cria uma coluna no quadro Kanban, posicionada ao final (RN-005). Restrito ao "
        "dono do projeto (RN-009). Passo 7 do fluxo de demonstração: use o `project_id` "
        "do projeto criado no passo 3 e guarde o `id` da coluna retornado."
    ),
    "status_code": status.HTTP_201_CREATED,
    "response_model": StageResponse,
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {"project_id": 1, "name": "Bloqueado"}
                }
            }
        }
    },
}

reorder_stages_swagger: dict[str, Any] = {
    "summary": "Reordenar colunas",
    "description": (
        "Redefine a ordem das colunas do quadro (RN-005). O corpo deve conter exatamente "
        "os ids das colunas do projeto, na nova ordem. Restrito ao dono do projeto. "
        "Use no path o `project_id` do passo 3."
    ),
    "response_model": list[StageResponse],
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {"example": {"stage_ids": [5, 1, 2, 3, 4]}}
            }
        }
    },
}

update_stage_swagger: dict[str, Any] = {
    "summary": "Renomear coluna",
    "description": (
        "Atualiza o nome da coluna. Restrito ao dono do projeto (RN-009). Use no path o "
        "`id` de uma coluna do quadro (resposta do passo 3 ou da coluna criada no passo 7)."
    ),
    "response_model": StageResponse,
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {"example": {"name": "Em Homologação"}}
            }
        }
    },
}

delete_stage_swagger: dict[str, Any] = {
    "summary": "Excluir coluna",
    "description": (
        "Remove a coluna somente se não possuir tarefas. Restrito ao dono do projeto (RN-009)."
    ),
    "status_code": status.HTTP_204_NO_CONTENT,
}
