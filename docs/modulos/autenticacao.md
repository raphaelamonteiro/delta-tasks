# 🔐 Módulo de Autenticação (`app/domains/auth`)

Guia para desenvolvedores. Se você só precisa **proteger um endpoint novo e obter o
usuário autenticado**, vá direto para
[⭐ Essencial](#-essencial-autenticar-um-endpoint-e-obter-o-usuário). O restante
cobre como o módulo funciona e como consumir os endpoints de auth.

> Relacionado: [Módulo de Usuários](./usuarios.md) ·
> Regras de negócio [RN-001](../requisitos.md#rn-001--provisionamento-de-usuários-restrito-ao-admin)
> e [RN-002](../requisitos.md#rn-002--autenticação-obrigatória).

---

## Visão geral

A autenticação é **stateless**, baseada em **JWT** transportado por **cookies
HttpOnly**. Nenhum token é persistido no banco: a validade vem inteiramente da
assinatura e do claim `exp`.

- **Access token** — vida curta (`ACCESS_TOKEN_EXPIRE_MINUTES`, padrão 15 min).
  Enviado em todas as rotas protegidas (cookie `access_token`, path `/`).
- **Refresh token** — vida longa (`REFRESH_TOKEN_EXPIRE_DAYS`, padrão 60 dias).
  Usado só para renovar o access token (cookie `refresh_token`, path `/auth`).

Os dois tokens são assinados com **chaves independentes**, de forma que vazar uma
não compromete a outra.

Não há auto-cadastro: criar contas é restrito a administradores
([RN-001](../requisitos.md#rn-001--provisionamento-de-usuários-restrito-ao-admin)).
O primeiro admin é criado via [seed](#bootstrap-do-primeiro-admin).

---

## ⭐ Essencial: autenticar um endpoint e obter o usuário

> **Esta é a parte que você mais vai usar.** Para exigir autenticação em qualquer
> endpoint novo, declare um parâmetro do tipo `CurrentUserDep` — o FastAPI resolve o
> cookie, valida o JWT e injeta o principal [`CurrentUser`](../../app/domains/auth/principal.py)
> **já carregado**, com a identidade do usuário **e os vínculos de projeto**. Você
> não lê cookie, não decodifica token, nem consulta o banco.

### Exigir autenticação e usar os dados do usuário

```python
from fastapi import APIRouter

from app.domains.auth.dependencies import CurrentUserDep

router = APIRouter()


@router.get("/tarefas/minhas")
async def minhas_tarefas(user: CurrentUserDep):
    # `user` é o principal autenticado — acesse seus atributos diretamente:
    return {
        "id": user.id,
        "nome": user.name,
        "email": user.email,
        "papel": user.global_role,   # GlobalRole.ADMIN | GlobalRole.USER
        "ativo": user.is_active,
    }
```

Se o cookie `access_token` estiver ausente, inválido, expirado, ou se o usuário
estiver inativo, a requisição é rejeitada com **401** *antes* de entrar na sua
função.

### O que você recebe: o principal `CurrentUser`

`CurrentUserDep` injeta um [`CurrentUser`](../../app/domains/auth/principal.py) —
um snapshot imutável válido durante a requisição. Ele expõe a identidade do usuário
e os papéis por projeto:

| Membro | Tipo | Observação |
| --- | --- | --- |
| `user.id` | `UUID` | Identificador da conta. |
| `user.name` | `str` | Nome. |
| `user.email` | `str` | Único. |
| `user.global_role` | `GlobalRole` | `ADMIN` ou `USER`. |
| `user.is_active` | `bool` | Contas inativas nunca chegam aqui (já barradas no 401). |
| `user.is_admin` | `bool` | Atalho para `global_role == ADMIN`. |
| `user.project_roles` | `dict[int, ProjectRole]` | Mapa `project_id → papel` de **todos** os projetos do usuário. |
| `user.role_in(project_id)` | `ProjectRole \| None` | Papel no projeto, ou `None` se não for membro. |
| `user.is_member(project_id)` | `bool` | Se participa do projeto. |
| `user.user` | `User` | A entidade ORM crua (use só quando precisar persistir). |

Os papéis por projeto são **pré-carregados** do banco no momento da autenticação
(uma única consulta por requisição), então os demais módulos autorizam acesso a um
projeto sem reconsultar nada.

> ⚠️ Para **retornar** o usuário numa resposta, não serialize o principal nem o
> `user.user` direto (a entidade contém `password_hash`). Use um schema de saída —
> por exemplo, `AuthenticatedUser.model_validate(user)`.

### Autorização por projeto ([RN-003](../requisitos.md#rn-003--acesso-restrito-a-membros-do-projeto) / [RN-004](../requisitos.md#rn-004--permissões-por-papel-no-projeto))

É exatamente para isto que os papéis vêm no principal — sem ida extra ao banco:

```python
from fastapi import APIRouter, HTTPException, status

from app.db.models import ProjectRole
from app.domains.auth.dependencies import CurrentUserDep

router = APIRouter()


@router.patch("/projetos/{project_id}/tarefas/{tarefa_id}")
async def mover_tarefa(project_id: int, tarefa_id: int, user: CurrentUserDep):
    papel = user.role_in(project_id)

    # Admin global acessa qualquer projeto (RN-003); não-membros levam 403.
    if not user.is_admin and papel is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Não é membro do projeto.")

    # Papéis no projeto definem o que pode (RN-004): observador é só leitura.
    if papel == ProjectRole.OBSERVER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Observador não edita tarefas.")
    ...
```

### Restringir a administradores

Mesma ideia, trocando a dependência:

```python
from fastapi import APIRouter, Depends

from app.domains.auth.dependencies import AdminUserDep, require_admin

router = APIRouter()


# (a) quando você precisa do admin autenticado:
@router.post("/relatorios")
async def gerar(admin: AdminUserDep): ...


# (b) quando só quer o guard (não usa o usuário):
@router.delete("/recurso/{id}", dependencies=[Depends(require_admin)])
async def remover(id: int): ...
```

`require_admin` já inclui a autenticação: retorna **403** se o usuário não for
`ADMIN` (e **401** se não estiver autenticado).

### Proteger todas as rotas de um router

Coloque a dependência no próprio `APIRouter` para cobrir tudo de uma vez (é o que o
[módulo de usuários](./usuarios.md) faz):

```python
from fastapi import APIRouter, Depends
from app.domains.auth.dependencies import get_current_user

# Todas as rotas deste router passam a exigir autenticação:
router = APIRouter(prefix="/projetos", dependencies=[Depends(get_current_user)])
```

### Resumo das dependências

Todas em [`app.domains.auth.dependencies`](../../app/domains/auth/dependencies.py):

| Dependência | Como usar | Efeito |
| --- | --- | --- |
| `CurrentUserDep` | parâmetro `user: CurrentUserDep` | Exige login e **injeta** o `CurrentUser`. |
| `AdminUserDep` | parâmetro `admin: AdminUserDep` | Exige admin e **injeta** o `CurrentUser`. |
| `get_current_user` | `dependencies=[Depends(get_current_user)]` | Exige login (sem injetar). |
| `require_admin` | `dependencies=[Depends(require_admin)]` | Exige admin (sem injetar). |

---

## Arquitetura

O fluxo segue estritamente **router → service → repository** (o router nunca fala
direto com o repositório):

| Arquivo | Responsabilidade |
| --- | --- |
| [`router.py`](../../app/domains/auth/router.py) | Endpoints HTTP, tradução de exceções de domínio → `HTTPException`, set/clear de cookies. |
| [`service.py`](../../app/domains/auth/service.py) | Regras de negócio: autenticação, emissão/validação de tokens, troca de senha. |
| [`repository.py`](../../app/domains/auth/repository.py) | Acesso ao banco (`User`): busca por e-mail/id, criação, atualização de hash. |
| [`dependencies.py`](../../app/domains/auth/dependencies.py) | Dependências do FastAPI: `get_current_user`, `require_admin` e os tipos anotados. |
| [`principal.py`](../../app/domains/auth/principal.py) | `CurrentUser`: principal autenticado (identidade + papéis por projeto) injetado nas rotas. |
| [`cookies.py`](../../app/domains/auth/cookies.py) | Configuração centralizada dos cookies de auth (nomes, paths, flags). |
| [`schemas.py`](../../app/domains/auth/schemas.py) | DTOs Pydantic de entrada/saída. |
| [`exceptions.py`](../../app/domains/auth/exceptions.py) | Erros de domínio (`InvalidCredentialsError`, etc.). |
| [`core/jwt.py`](../../app/core/jwt.py) | `JWTService`: codifica/decodifica os tokens (puro, sem I/O). |
| [`core/security.py`](../../app/core/security.py) | `PasswordSecurity`: hashing Argon2 das senhas. |

---

## Configuração

Variáveis de ambiente relevantes (veja [`.env.example`](../../.env.example)):

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `ACCESS_TOKEN_SIGNING_KEY` | — | Chave de assinatura do access token. **Use 32+ bytes** (`openssl rand -hex 32`). |
| `REFRESH_TOKEN_SIGNING_KEY` | — | Chave de assinatura do refresh token (independente da acima). |
| `JWT_ALGORITHM` | `HS256` | Algoritmo de assinatura. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Validade do access token. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `60` | Validade do refresh token. |
| `ENVIRONMENT` | `development` | Em `production`, os cookies recebem a flag `Secure` (só trafegam via HTTPS). |
| `SEED_ADMIN_NAME` / `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | — | Dados do primeiro admin criado pelo seed. |

### Bootstrap do primeiro admin

Como `POST /auth/register` exige um admin autenticado, é preciso semear o primeiro
admin antes de qualquer login:

```bash
make seed                 # roda app/seed/run_seed.py
```

O seed é **idempotente** (`INSERT ... ON CONFLICT (email) DO NOTHING`), então pode
rodar a cada boot sem duplicar. Ele já é executado automaticamente no
[`entrypoint.sh`](../../entrypoint.sh) após as migrations.

---

## Endpoints

Prefixo: `/auth`. Todos os corpos são JSON.

| Método | Rota | Auth exigida | Descrição |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | **Admin** | Cria uma nova conta. |
| `POST` | `/auth/login` | — | Autentica e seta os cookies de auth. |
| `POST` | `/auth/refresh` | cookie de refresh | Renova o access token. |
| `POST` | `/auth/logout` | sim | Limpa os cookies de auth. |
| `GET` | `/auth/me` | sim | Retorna o usuário autenticado. |
| `PATCH` | `/auth/me/password` | sim | Troca a própria senha. |

### `POST /auth/register` — criar conta (admin)

- **Body** (`RegisterUserDTO`): `name` (1–100), `email`, `password` (8–128).
- **201** → `RegisterUserResponse` (`id`, `name`, `email`, `global_role`, `is_active`, `created_at`).
- **401** sem autenticação · **403** autenticado mas não-admin · **409** e-mail já cadastrado · **400** corpo inválido.

> Novas contas nascem com `global_role = user` e `is_active = true`.

### `POST /auth/login`

- **Body** (`LoginDTO`): `email`, `password` (mín. 1 — a política de força é checada
  no cadastro/troca, não no login).
- **200** → `AuthenticatedUser` (`id`, `name`, `email`, `global_role`, `is_active`) + cookies `access_token` e `refresh_token`.
- **401** credenciais inválidas **ou** conta inativa — a resposta é a mesma nos dois
  casos, sem revelar qual checagem falhou ([US-002](../requisitos.md)). · **400** corpo inválido.

### `POST /auth/refresh`

- Lê o cookie `refresh_token`. Não tem corpo.
- **200** → `AuthenticatedUser` + novo cookie `access_token`.
- **401** cookie ausente, inválido ou expirado, ou usuário inativo/inexistente.

### `POST /auth/logout`

- Exige estar autenticado. **204** e limpa os dois cookies.

### `GET /auth/me`

- **200** → `AuthenticatedUser`. · **401** se não autenticado.

### `PATCH /auth/me/password`

- **Body** (`ChangePasswordDTO`): `current_password` (mín. 1), `new_password` (8–128).
- **204** senha alterada.
- **401** senha atual incorreta (ou não autenticado).
- **400** nova senha inválida **ou** igual à atual.

---

## Fluxo típico

```
make seed                      # cria o admin inicial (uma vez)
   │
POST /auth/login               # admin → recebe cookies access + refresh
   │
POST /auth/register            # admin cria contas de usuários comuns
   │
(usuário) POST /auth/login     # usuário comum → recebe cookies
   │
GET /auth/me  /  rotas protegidas   # access token no cookie
   │
POST /auth/refresh             # quando o access expira (sem novo login)
   │
POST /auth/logout              # encerra a sessão
```

---

## Tratamento de erros

As exceções de domínio ([`exceptions.py`](../../app/domains/auth/exceptions.py))
**não vazam** para o cliente: o `router` as traduz em `HTTPException`.

| Exceção de domínio | HTTP no router |
| --- | --- |
| `EmailAlreadyExistsError` | 409 |
| `InvalidCredentialsError` | 401 |
| `InactiveUserError` | 401 (mesma resposta de credencial inválida no login) |
| `SamePasswordError` | 400 |
| `TokenError` (em `core/jwt.py`) | vira `InvalidCredentialsError` no service → 401 |

**Validação de corpo:** um handler global em [`app/main.py`](../../app/main.py)
converte o `422` padrão do FastAPI para **400** (`RequestValidationError`). Além
disso, os DTOs herdam de `BaseDTO` com `extra="forbid"`, então campos desconhecidos
no corpo também resultam em **400**.

---

## Exemplos (cURL)

Os cookies são HttpOnly; use um cookie jar (`-c` para gravar, `-b` para enviar).

```bash
# 1. Login do admin (criado via `make seed`)
curl -c cookies.txt -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@deltatask.com","password":"SUA_SENHA_DE_SEED"}'

# 2. Admin cria um usuário comum
curl -b cookies.txt -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Maria","email":"maria@example.com","password":"SenhaForte123"}'

# 3. Usuário comum faz login (novo cookie jar)
curl -c maria.txt -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"maria@example.com","password":"SenhaForte123"}'

# 4. Acessa rota protegida
curl -b maria.txt http://127.0.0.1:8000/auth/me

# 5. Renova o access token e, por fim, sai
curl -b maria.txt -c maria.txt -X POST http://127.0.0.1:8000/auth/refresh
curl -b maria.txt -X POST http://127.0.0.1:8000/auth/logout
```

---

## Testes

- **Unitários** (service, repositório mockado): [`tests/app/unit/test_auth_service.py`](../../tests/app/unit/test_auth_service.py)
- **Integração** (repositório, Postgres real): [`tests/app/integration/test_auth_repository.py`](../../tests/app/integration/test_auth_repository.py)
- **E2E** (rotas, via `httpx`): [`tests/app/e2e/test_auth_routes.py`](../../tests/app/e2e/test_auth_routes.py)

Rode com `make test`. A documentação interativa (Swagger UI) também fica disponível
em `/docs` com a aplicação no ar.
