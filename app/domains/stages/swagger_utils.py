from typing import Any
from fastapi import status


create_stage_swagger: dict[str, Any] = {
    "summary": "Criar coluna",
    "description": "Cria uma coluna no quadro Kanban.",
    "status_code": status.HTTP_201_CREATED,
}


update_stage_swagger: dict[str, Any] = {
    "summary": "Renomear coluna",
    "description": "Atualiza o nome da coluna.",
}


delete_stage_swagger: dict[str, Any] = {
    "summary": "Excluir coluna",
    "description": (
        "Remove a coluna somente se não possuir tarefas."
    ),
    "status_code": status.HTTP_204_NO_CONTENT,
}