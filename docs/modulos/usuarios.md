# 👥 Módulo de Usuários (`app/domains/users`)

Guia para desenvolvedores: gestão de contas de usuário (listar, consultar,
atualizar e remover). Operações de leitura exigem autenticação; operações de
escrita exigem papel de **admin**.

> Relacionado: [Módulo de Autenticação](./autenticacao.md) ·
> Regras [RN-001](../requisitos.md#rn-001--provisionamento-de-usuários-restrito-ao-admin)
> e [RN-002](../requisitos.md#rn-002--autenticação-obrigatória).

---

## Visão geral

Este módulo cobre o ciclo de vida das contas **após** a criação (que pertence ao
[`POST /auth/register`](./autenticacao.md#post-authregister--criar-conta-admin)).
Ele depende inteiramente do módulo de autenticação para identidade e permissões.

- **Todas** as rotas exigem um usuário autenticado — o guard está no próprio
  `APIRouter` ([RN-002](../requisitos.md#rn-002--autenticação-obrigatória)).
- **Escrita** (`PATCH`, `DELETE`) exige `global_role = admin`
  ([RN-001](../requisitos.md#rn-001--provisionamento-de-usuários-restrito-ao-admin)).

---

## Arquitetura

Mesmo padrão **router → service → repository** do resto da aplicação:

| Arquivo | Responsabilidade |
| --- | --- |
| [`router.py`](../../app/domains/users/router.py) | Endpoints HTTP, paginação, tradução de exceções → `HTTPException`. |
| [`service.py`](../../app/domains/users/service.py) | Regras: aplica `UpdateUserDTO`, faz o hash de senha quando trocada. |
| [`repository.py`](../../app/domains/users/repository.py) | Acesso ao banco: busca, listagem paginada, update e delete. |
| [`dependencies.py`](../../app/domains/users/dependencies.py) | Monta `UserService`/`UserRepository`. |
| [`schemas.py`](../../app/domains/users/schemas.py) | DTOs: `UserResponse`, `UpdateUserDTO`, `UserListResponse`. |
| [`exceptions.py`](../../app/domains/users/exceptions.py) | Erros de domínio (`UserNotFoundError`, etc.). |

A proteção das rotas é feita **reutilizando** as dependências do módulo de auth
([`get_current_user`](./autenticacao.md#exigir-apenas-autenticação) e
[`require_admin`](./autenticacao.md#exigir-papel-de-admin)):

```python
# app/domains/users/router.py
users_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)],  # toda rota exige autenticação
)
```

---

## Endpoints

Prefixo: `/users`.

| Método | Rota | Auth exigida | Descrição |
| --- | --- | --- | --- |
| `GET` | `/users` | autenticado | Lista usuários (paginado). |
| `GET` | `/users/{user_id}` | autenticado | Retorna um usuário. |
| `PATCH` | `/users/{user_id}` | **Admin** | Atualiza parcialmente um usuário. |
| `DELETE` | `/users/{user_id}` | **Admin** | Remove um usuário. |

`user_id` é um **UUID**.

### `GET /users` — listar (paginado)

- **Query**: `limit` (1–100, padrão 50), `offset` (≥ 0, padrão 0).
- **200** → `UserListResponse`:

```json
{
  "items": [ { "id": "…", "name": "…", "email": "…", "global_role": "user",
               "is_active": true, "created_at": "…", "updated_at": "…" } ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

A listagem é ordenada por `created_at`. `total` é a contagem global (ignora a
paginação), útil para montar a paginação no cliente.

### `GET /users/{user_id}`

- **200** → `UserResponse`. · **404** se não existir.

### `PATCH /users/{user_id}` — atualização parcial (admin)

- **Body** (`UpdateUserDTO`) — todos os campos são **opcionais**; só os enviados
  são alterados (`exclude_unset`):

  | Campo | Regras |
  | --- | --- |
  | `name` | 1–100 caracteres |
  | `email` | e-mail válido, ≤ 255 |
  | `password` | 8–128 — é re-hasheada antes de salvar (nunca armazenada em texto) |
  | `global_role` | `admin` \| `user` |
  | `is_active` | `true` \| `false` — use para **desativar/reativar** contas |

- **200** → `UserResponse`.
- **404** não encontrado · **409** e-mail já em uso · **400** corpo inválido.

> **Desativação de contas** ([RN-001](../requisitos.md#rn-001--provisionamento-de-usuários-restrito-ao-admin)):
> prefira `PATCH … {"is_active": false}` a deletar. Uma conta inativa não consegue
> mais logar (ver [login](./autenticacao.md#post-authlogin)), mas preserva o
> histórico relacionado.

### `DELETE /users/{user_id}` (admin)

- **204** removido.
- **404** não encontrado.
- **409** o usuário ainda possui registros relacionados (ex.: é dono de projeto) e
  não pode ser excluído — nesse caso, **desative** em vez de excluir.

---

## Schemas

Definidos em [`schemas.py`](../../app/domains/users/schemas.py):

- **`UserResponse`** — representação pública: `id`, `name`, `email`, `global_role`,
  `is_active`, `created_at`, `updated_at`. (Nunca inclui `password_hash`.)
- **`UpdateUserDTO`** — atualização parcial; herda `extra="forbid"`, então campos
  desconhecidos resultam em **400**.
- **`UserListResponse`** — envelope de paginação (`items`, `total`, `limit`, `offset`).

---

## Tratamento de erros

| Exceção de domínio | HTTP no router |
| --- | --- |
| `UserNotFoundError` | 404 |
| `EmailAlreadyTakenError` | 409 |
| `UserHasDependenciesError` | 409 |
| Validação de corpo (`RequestValidationError`) | 400 (handler global em [`app/main.py`](../../app/main.py)) |

---

## Exemplos (cURL)

Reaproveite o cookie jar de um login de **admin** (veja
[Autenticação → Exemplos](./autenticacao.md#exemplos-curl)).

```bash
# Listar (página de 10)
curl -b cookies.txt "http://127.0.0.1:8000/users?limit=10&offset=0"

# Consultar um usuário
curl -b cookies.txt http://127.0.0.1:8000/users/<UUID>

# Promover a admin
curl -b cookies.txt -X PATCH http://127.0.0.1:8000/users/<UUID> \
  -H "Content-Type: application/json" \
  -d '{"global_role":"admin"}'

# Desativar a conta (recomendado no lugar de excluir)
curl -b cookies.txt -X PATCH http://127.0.0.1:8000/users/<UUID> \
  -H "Content-Type: application/json" \
  -d '{"is_active":false}'

# Excluir
curl -b cookies.txt -X DELETE http://127.0.0.1:8000/users/<UUID>
```

---

## Estendendo o módulo

Mantenha o fluxo **router → service → repository**: o router nunca chama o
repositório diretamente, e regra de negócio nova vai no `service`.

- **Nova regra/transformação** (ex.: normalizar e-mail, validar transição de papel)
  → `UserService`.
- **Nova consulta/escrita no banco** → `UserRepository` (cada método deve traduzir
  falhas de integridade do SQLAlchemy nas exceções de domínio adequadas, como já
  ocorre com `EmailAlreadyTakenError`).
- **Novo endpoint** → `router.py`, injetando `UserServiceDep` e capturando as
  exceções de domínio para devolver o HTTP correto.

---

## Testes

- **Unitários** (service): [`tests/app/unit/test_users_service.py`](../../tests/app/unit/test_users_service.py)
- **Integração** (repositório): [`tests/app/integration/test_users_repository.py`](../../tests/app/integration/test_users_repository.py)
- **E2E** (rotas): [`tests/app/e2e/test_users_routes.py`](../../tests/app/e2e/test_users_routes.py)

Rode com `make test`. Swagger UI disponível em `/docs` com a aplicação no ar.
