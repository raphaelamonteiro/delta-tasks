from typing import Any

from fastapi import status

from app.domains.users.schemas import UserListResponse, UserResponse

list_users_swagger: dict[str, Any] = {
    "summary": "Lista usuários",
    "description": "Retorna uma lista paginada de usuários.",
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
    "description": ( "Atualiza parcialmente um usuário. "
    "Retorna 409 se o novo e-mail já estiver em uso."),

    "response_model": UserResponse,
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