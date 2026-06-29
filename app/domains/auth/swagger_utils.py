from typing import Any

from fastapi import status

from app.domains.auth.schemas import AuthenticatedUser, RegisterUserResponse

register_responses: dict[int | str, dict[str, Any]] = {
    201: {
        "description": "Usuário registrado com sucesso.",
    },
    401: {
        "description": "Não autenticado.",
    },
    403: {
        "description": "Privilégios de administrador necessários.",
    },
    409: {
        "description": "E-mail já cadastrado.",
    },
    400: {
        "description": "Falha na validação do corpo da requisição.",
    },
}

register_user_swagger: dict[str, Any] = {
    "summary": "Registrar usuário",
    "description": ( "Cria uma nova conta de usuário. " "Retorna 409 se o e-mail já estiver em uso."),
    "status_code": status.HTTP_201_CREATED,
    "response_model": RegisterUserResponse,
    "responses": register_responses,
}

login_swagger: dict[str, Any] = {
    "summary": "Log in",
    "description": (
        "Autentica via e-mail/senha e define cookies HttpOnly de access e refresh token. "
        "Retorna 401 para credenciais inválidas ou conta inativa, sem revelar qual verificação falhou."),
    "response_model": AuthenticatedUser,
    "responses": {
        200: {"description": "Autenticado; cookies de autenticação definidos."},
        401: {"description": "Credenciais inválidas ou conta inativa."},
        400: {"description": "Falha na validação do corpo da requisição."},
    },
}

refresh_swagger: dict[str, Any] = {
    "summary": "Atualizar token de acesso",
    "description": ("Gera um novo token de acesso usando o refresh token armazenado em cookie. "
        "Retorna 401 se o refresh token estiver ausente, inválido ou expirado."),
    "response_model": AuthenticatedUser,
    "responses": {
        200: {"description": "Token de acesso atualizado."},
        401: {"description": "Refresh token ausente ou inválido."},
    },
}

logout_swagger: dict[str, Any] = {
    "summary": "Log out",
    "description": "Remove os cookies de access e refresh token.",
    "status_code": status.HTTP_204_NO_CONTENT,
   "responses": {
        204: {"description": "Logout realizado; cookies de autenticação removidos."},
        401: {"description": "Não autenticado."},
    },
}

me_swagger: dict[str, Any] = {
    "summary": "Usuário atual",
    "description": "Retorna o usuário autenticado a partir do cookie de access token.",
    "response_model": AuthenticatedUser,
    "responses": {
        200: {"description": "Usuário autenticado."},
        401: {"description": "Não autenticado."},
    },
}

change_password_swagger: dict[str, Any] = {
    "summary": "Alterar própria senha",
    "description": (
        "Altera a senha do usuário autenticado. Requer a senha atual. "
        "Retorna 401 se a senha atual estiver incorreta, ou 400 se a nova senha for inválida "
        "ou igual à atual."),
    "status_code": status.HTTP_204_NO_CONTENT,
     "responses": {
        204: {"description": "Senha alterada com sucesso."},
        400: {"description": "Nova senha inválida."},
        401: {"description": "Não autenticado ou senha atual incorreta."},
    },
}
