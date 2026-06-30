# 🔺Delta

Gerenciador de tarefas ágil baseado no modelo Kanban.

<p> 
<a href="#escopo">Escopo</a> | 
<a href="#diagrama">Diagrama</a> | 
<a href="#tecnologias">Tecnologias</a> | 
<a href="#requisitos">Requisitos</a> | 
<a href="#estrutura">Estrutura</a> | 
<a href="#rodar">Como rodar</a> | 
<a href="#comandos">Comandos</a> |
<a href="#documentacao">Documentação</a> |
<a href="#creditos">Créditos</a> 
</p>

---

## 📋 Escopo

<a id="escopo"></a>

## 📋 Escopo

<a id="escopo"></a>

**Delta** é um gerenciador de tarefas ágil baseado no modelo Kanban, desenvolvido como uma API backend utilizando FastAPI.

O projeto tem como objetivo fornecer uma base sólida para organização, criação e gerenciamento de tarefas.

A aplicação permite a criação, atualização, listagem e remoção de tarefas organizadas em colunas Kanban (como _To Do_, _In Progress_ e _Done_), garantindo uma visão clara e contínua do fluxo de trabalho.

As tarefas são associadas a usuários, permitindo controle de responsabilidade e isolamento de dados por conta.

O projeto é containerizado com Docker, facilitando o ambiente de desenvolvimento e execução.

## 🖋️ Diagrama

<a id="diagrama"></a>

Diagrama de entidade-relacionamento do banco de dados (gerado no [dbdiagram.io](https://dbdiagram.io) a partir de [`docs/diagrama.dbml`](docs/diagrama.dbml)):

<div align="center">

![Diagrama do banco de dados Delta Tasks](docs/uml.png)

</div>

## 🛠️ Tecnologias

<a id="tecnologias"></a>

<div align="center">

![Python](https://img.shields.io/badge/Python-D71313?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-D71313?style=for-the-badge&logo=FASTAPI&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-D71313?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-D71313?style=for-the-badge&logo=docker&logoColor=white)
![Git](https://img.shields.io/badge/Git-D71313?style=for-the-badge&logo=git&logoColor=white)

</div>

## 🔎 Requisitos

<a id="requisitos"></a>

- Python 3.12+
- PostgreSQL (configurável via `.env` — veja `.env.example`)

## 📦 Estrutura do Repositório

<a id="estrutura"></a>

```bash
delta-tasks/
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── jwt.py
│   │   ├── logger.py
│   │   ├── schemas.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   ├── dependencies.py
│   │   ├── init_db.py
│   │   └── models.py
│   │
│   ├── domains/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── tasks/
│   │   └── projects/
│   │
│   ├── seed/
│   │   ├── __init__.py
│   │   └── run_seed.py
│   │
│   ├── config.py
│   ├── main.py
│   └── __init__.py
│
├── docs/
│   ├── modulos/
│   ├── backlog.md
│   ├── requisitos.md
│   └── uml.png
│
├── logs/
│   └── .gitkeep
│
├── tests/
│   ├── app/
│   ├── conftest.py
│   └── __init__.py
│
├── .dockerignore
├── .env.example
├── .env.test
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── LICENSE
├── Makefile
├── poetry.lock
├── pyproject.toml
├── requirements-dev.txt
├── requirements.txt
├── run.py
├── .gitignore
└── README.md              # Documentação principal
```

## ⚙️ Como rodar o projeto?

<a id="rodar"></a>

Há dois caminhos equivalentes. Use **poetry** se já o tem instalado; senão use **pip + venv**.

### 🐍 Opção A: pip + venv

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt   # runtime apenas
# ou, para desenvolver (inclui ruff, mypy, pytest, etc.):
pip install -r requirements-dev.txt

python run.py                     # sobe a API em http://127.0.0.1:8000 (reload)
```

### 📦 Opção B: Poetry

```bash
make install        # poetry install
make dev            # uvicorn com --reload
```

## 🖥️ Comandos úteis (Makefile)

<a id="comandos"></a>

| Comando                | Descrição                                          |
| ---------------------- | -------------------------------------------------- |
| `make dev`             | Sobe a API com reload                              |
| `make test`            | Roda os testes (pytest)                            |
| `make lint`            | ruff check + bandit                                |
| `make format`          | ruff format                                        |
| `make typecheck`       | mypy (modo estrito)                                |
| `make migrate`         | Aplica as migrations (alembic upgrade head)        |
| `make install-pip`     | Instala dependências de runtime via pip            |
| `make install-pip-dev` | Instala runtime + ferramentas de dev via pip       |
| `make requirements`    | Regera `requirements*.txt` a partir do poetry.lock |

> Os arquivos `requirements.txt` e `requirements-dev.txt` são **gerados** a partir do `poetry.lock`.
> Após alterar dependências no `pyproject.toml`, rode `make requirements` para mantê-los em sincronia.

## 📚 Documentação

<a id="documentacao"></a>

Guias para desenvolvedores sobre como usar e estender os módulos da aplicação
(em [`docs/modulos/`](docs/modulos/)):

- [🔐 Módulo de Autenticação](docs/modulos/autenticacao.md) — login com JWT em cookies, refresh, troca de senha e proteção de rotas.
- [👥 Módulo de Usuários](docs/modulos/usuarios.md) — listagem, consulta, atualização e remoção de contas.

## 👥 Créditos

<a id="creditos"></a>

<div align="center">

| Nome              | Perfil no GitHub                                                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Raphaela Monteiro | [![GitHub](https://img.shields.io/badge/GitHub-111217?style=flat-square&logo=github&logoColor=white)](https://github.com/raphaelamonteiro) |
| Julia Pereira     | [![GitHub](https://img.shields.io/badge/GitHub-111217?style=flat-square&logo=github&logoColor=white)](https://github.com/juliasoares17)    |
| Pedro Garcia      | [![GitHub](https://img.shields.io/badge/GitHub-111217?style=flat-square&logo=github&logoColor=white)](https://github.com/pedro-fs-garcia)  |

</div>
