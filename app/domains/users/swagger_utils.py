from typing import Any

from fastapi import status

from app.domains.users.schemas import UserListResponse, UserResponse

list_users_swagger: dict[str, Any] = {
    "summary": "Lista usuários",
    "description": (
        "Retorna uma lista paginada de usuários. Útil no fluxo de demonstração para "
        "localizar o `id` do usuário registrado (passo 2) caso não o tenha guardado."
    ),
    "response_model": UserListResponse,
    "responses": {
        200: {"description": "Usuários listados com sucesso."},
    },
}

get_user_swagger: dict[str, Any] = {
    "summary": "Obter usuário",
    "description": "Retorna um único usuário pelo ID.",
    "response_model": UserResponse,
    "responses": {
        200: {"description": "Usuário encontrado."},
        404: {"description": "Usuário não encontrado."},
    },
}

update_user_swagger: dict[str, Any] = {
    "summary": "Atualizar usuário",
    "description": (
        "Atualiza parcialmente um usuário. Retorna 409 se o novo e-mail já estiver em uso. "
        "Restrito a administradores. Passo 6 do fluxo de demonstração: use no path o "
        "`user_id` do register (passo 2) para ajustar o perfil do usuário; envie apenas "
        "os campos que deseja alterar."
    ),
    "response_model": UserResponse,
    "openapi_extra": {
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "name": "Bruno Lima Souza",
                        "is_active": True,
                    }
                }
            }
        }
    },
    "responses": {
        200: {"description": "Usuário atualizado com sucesso."},
        404: {"description": "Usuário não encontrado."},
        409: {"description": "E-mail já cadastrado."},
        400: {"description": "Falha na validação do corpo da requisição."},
    },
}
    
delete_user_swagger: dict[str, Any] = {
    "summary": "Excluir usuário",
    "description": (
        "Remove permanentemente um usuário. "
        "Retorna 409 se o usuário ainda possuir registros relacionados."
    ),
    "status_code": status.HTTP_204_NO_CONTENT,
    "responses": {
        204: {"description": "Usuário excluído com sucesso."},
        404: {"description": "Usuário não encontrado."},
        409: {"description": "Usuário possui registros relacionados e não pode ser excluído."},
    },
}