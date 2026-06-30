# Diagramas UML — Delta Tasks

Modelagem da Fase 2, derivada de [requisitos.md](../requisitos.md) e [backlog.md](../backlog.md).

| Arquivo | Diagrama | Fase |
|---------|----------|------|
| [casos-de-uso.puml](casos-de-uso.puml) | Casos de Uso (atores × funcionalidades, US-001..US-020) | 2 — Modelagem |
| [classes-dominio.puml](classes-dominio.puml) | Classes de Domínio (entidades E-001..E-008, enums e relacionamentos) | 2 — Modelagem |
| [classes-arquitetura-tasks.puml](classes-arquitetura-tasks.puml) | Classes de Projeto: camadas `router → service → repository → models` e design patterns (fatia `tasks`) | 3 — Arquitetura |

> Observação: `../uml.png` é um **ERD** (modelo físico de tabelas), não substitui estes
> diagramas UML de Casos de Uso e de Classes.

## Como renderizar (escolha uma)

1. **VS Code (recomendado, zero config de Java):** instale a extensão
   **PlantUML** (`jebbs.plantuml`), abra o `.puml` e use `Alt+D` para pré-visualizar.
   Exporte com `Ctrl+Shift+P → PlantUML: Export Current Diagram` (PNG/SVG).
2. **Online (sem instalar nada):** cole o conteúdo do `.puml` em
   <https://www.plantuml.com/plantuml>.
3. **CLI:** requer Java + Graphviz (`dot`):
   ```bash
   sudo apt install graphviz
   java -jar plantuml.jar -tpng docs/diagrams/*.puml
   ```
   Sem Graphviz, force o motor interno adicionando `!pragma layout smetana`
   logo após o `@startuml`.
