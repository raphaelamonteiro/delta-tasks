# projeto-eng-software

API de gerenciamento de tarefas com arquitetura escalável. Desenvolvido com boas práticas de Engenharia de Software.

## Requisitos

- Python 3.12+
- PostgreSQL (configurável via `.env` — veja `.env.example`)

## Como rodar

Há dois caminhos equivalentes. Use **poetry** se já o tem instalado; senão use **pip + venv**.

### Opção A — pip + venv (sem poetry)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt   # runtime apenas
# ou, para desenvolver (inclui ruff, mypy, pytest, etc.):
pip install -r requirements-dev.txt

python run.py                     # sobe a API em http://127.0.0.1:8000 (reload)
```

### Opção B — poetry

```bash
make install        # poetry install
make dev            # uvicorn com --reload
```

## Comandos úteis (Makefile)

| Comando                | Descrição                                         |
| ---------------------- | ------------------------------------------------- |
| `make dev`             | Sobe a API com reload                             |
| `make test`            | Roda os testes (pytest)                           |
| `make lint`            | ruff check + bandit                               |
| `make format`          | ruff format                                       |
| `make typecheck`       | mypy (modo estrito)                               |
| `make migrate`         | Aplica as migrations (alembic upgrade head)       |
| `make install-pip`     | Instala dependências de runtime via pip           |
| `make install-pip-dev` | Instala runtime + ferramentas de dev via pip      |
| `make requirements`    | Regera `requirements*.txt` a partir do poetry.lock |

> Os arquivos `requirements.txt` e `requirements-dev.txt` são **gerados** a partir do `poetry.lock`.
> Após alterar dependências no `pyproject.toml`, rode `make requirements` para mantê-los em sincronia.
