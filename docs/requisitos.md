# Requisitos — Delta Tasks (Gerenciador de Tarefas Kanban)

Backend de um gerenciador de tarefas no modelo Kanban. Documento de requisitos: modelo
de domínio, regras de negócio (`RN-###`) e requisitos não funcionais (`NFR-###`). O
backlog de histórias de usuário está em [backlog.md](backlog.md).

## 1. Visão geral

Equipes descentralizadas perdem prazos por falta de visibilidade do fluxo de trabalho. O
sistema oferece quadros Kanban por projeto, com colunas flexíveis, movimentação de tarefas
entre colunas com histórico seguro/auditável, atribuição estrita de responsáveis e
notificações assíncronas por e-mail. Filosofia de **MVP enxuto**: o menor conjunto de
requisitos que entregue valor.

- **Entrega**: apenas backend (API REST), em Python.
- **Não multitenant**: ambiente único e fechado; o isolamento entre equipes é feito por
  projeto via RBAC.

## 2. Escopo do MVP

- Autenticação e gestão de usuários (contas criadas pelo Admin).
- CRUD de projetos (cada projeto é um quadro Kanban).
- Gestão de membros do projeto e papéis (RBAC por projeto).
- Colunas flexíveis por quadro (criar, renomear, reordenar, remover), com conjunto padrão.
- CRUD de tarefas com responsável e prazo.
- Movimentação de tarefas entre colunas, com histórico imutável.
- Comentários em tarefas.
- Notificações por e-mail (assíncronas) para os eventos relevantes.

## 3. Decisões de escopo (lacunas resolvidas)

Decisões tomadas para preencher lacunas do enunciado. Itens marcados como *(decidido)*
foram escolhidos explicitamente; *(derivado)* foram inferidos do desafio de negócio e da
filosofia de MVP, e podem ser revistos.

| # | Decisão |
|---|---------|
| RBAC | Admin global do sistema + papéis por projeto: **Dono**, **Membro**, **Observador**. *(decidido)* |
| Estrutura | **Projeto = Quadro** com **colunas flexíveis** (criar/renomear/reordenar/remover). Ao criar o projeto, são geradas as colunas padrão **Pendente, Em Progresso, Em Revisão, Concluído** como fallback. *(decidido)* |
| Tarefa | Cada tarefa **pertence a uma coluna** e tem um **responsável** (opcional). O papel de revisor foi removido. *(decidido)* |
| Autenticação | Sem auto-cadastro: contas criadas só pelo Admin. Login por e-mail/senha com **JWT**; senha com hash. *(decidido / derivado)* |
| Notificações | **E-mail (SMTP) assíncrono** para: atribuição, mudança de coluna e novo comentário. *(decidido)* |
| Prazo | Tarefa possui campo de **prazo** (due date) para apoiar a visibilidade de prazos. *(derivado)* |
| Histórico | Histórico de mudanças de coluna é **imutável** (append-only) e guarda os **nomes das colunas** no momento da mudança. *(derivado do enunciado)* |
| Stack | Python, API REST, banco relacional. *(derivado)* |

## 4. Modelo de domínio

Entidades do domínio (`E-###`) referenciadas pelas histórias de usuário e regras de negócio.

### E-001 Usuário

- **Descrição**: pessoa com acesso ao sistema. Contas são criadas pelo Admin.
- **Atributos**: `id`, `nome`, `email` (único), `senha_hash`, `papel_global`
  (`ADMIN` | `USUARIO`), `ativo` (bool), `criado_em`, `atualizado_em`.
- **Relacionamentos**: participa de projetos via [E-003 Membro do Projeto](#e-003-membro-do-projeto);
  pode ser responsável de [E-005 Tarefa](#e-005-tarefa); autor de
  [E-006 Comentário](#e-006-comentário); destinatário de [E-008 Notificação](#e-008-notificação).
- **Regras**: [RN-001](#rn-001--provisionamento-de-usuários-restrito-ao-admin),
  [RN-002](#rn-002--autenticação-obrigatória).

### E-002 Projeto

- **Descrição**: um projeto é um quadro Kanban. Agrupa colunas, tarefas e membros.
- **Atributos**: `id`, `nome`, `descricao`, `dono_id` (→ E-001), `criado_em`, `atualizado_em`.
- **Relacionamentos**: possui N [E-004 Coluna](#e-004-coluna); possui N
  [E-005 Tarefa](#e-005-tarefa); possui N [E-003 Membro do Projeto](#e-003-membro-do-projeto).
- **Regras**: [RN-003](#rn-003--acesso-restrito-a-membros-do-projeto),
  [RN-005](#rn-005--colunas-flexíveis-com-conjunto-padrão),
  [RN-009](#rn-009--gestão-do-projeto-restrita-ao-dono).

### E-003 Membro do Projeto

- **Descrição**: associação entre [E-001 Usuário](#e-001-usuário) e
  [E-002 Projeto](#e-002-projeto) com um papel no escopo do projeto.
- **Atributos**: `id`, `projeto_id` (→ E-002), `usuario_id` (→ E-001), `papel_projeto`
  (`DONO` | `MEMBRO` | `OBSERVADOR`), `criado_em`. Par (`projeto_id`, `usuario_id`) único.
- **Relacionamentos**: o criador do projeto é registrado como `DONO`.
- **Regras**: [RN-003](#rn-003--acesso-restrito-a-membros-do-projeto),
  [RN-004](#rn-004--permissões-por-papel-no-projeto),
  [RN-009](#rn-009--gestão-do-projeto-restrita-ao-dono).

### E-004 Coluna

- **Descrição**: lista/coluna do quadro Kanban; representa um estágio do fluxo. Customizável
  por projeto.
- **Atributos**: `id`, `projeto_id` (→ E-002), `nome`, `ordem` (posição no quadro), `criado_em`.
- **Relacionamentos**: pertence a um [E-002 Projeto](#e-002-projeto); possui N
  [E-005 Tarefa](#e-005-tarefa).
- **Padrão (fallback)**: ao criar um projeto, são geradas automaticamente as colunas
  `Pendente`, `Em Progresso`, `Em Revisão` e `Concluído`. O Dono pode renomeá-las,
  reordená-las, adicionar novas e remover existentes.
- **Regras**: [RN-005](#rn-005--colunas-flexíveis-com-conjunto-padrão),
  [RN-009](#rn-009--gestão-do-projeto-restrita-ao-dono).

### E-005 Tarefa

- **Descrição**: cartão (card) do quadro. Representa um item de trabalho e pertence a uma coluna.
- **Atributos**: `id`, `projeto_id` (→ E-002), `coluna_id` (→ E-004), `titulo`, `descricao`,
  `responsavel_id` (→ E-001, opcional), `prazo` (data, opcional), `ordem` (posição na coluna),
  `criado_em`, `atualizado_em`.
- **Relacionamentos**: pertence a uma [E-004 Coluna](#e-004-coluna); possui N
  [E-006 Comentário](#e-006-comentário); possui N
  [E-007 Histórico de Movimentação](#e-007-histórico-de-movimentação).
- **Regras**: [RN-005](#rn-005--colunas-flexíveis-com-conjunto-padrão),
  [RN-006](#rn-006--responsável-deve-ser-membro-do-projeto).

### E-006 Comentário

- **Descrição**: mensagem de texto associada a uma tarefa.
- **Atributos**: `id`, `tarefa_id` (→ E-005), `autor_id` (→ E-001), `texto`, `criado_em`.
- **Regras**: [RN-003](#rn-003--acesso-restrito-a-membros-do-projeto),
  [RN-004](#rn-004--permissões-por-papel-no-projeto).

### E-007 Histórico de Movimentação

- **Descrição**: registro append-only de cada mudança de coluna de uma tarefa.
- **Atributos**: `id`, `tarefa_id` (→ E-005), `coluna_origem_id`, `coluna_destino_id`,
  `coluna_origem_nome`, `coluna_destino_nome` (snapshot do nome no momento da mudança),
  `autor_id` (→ E-001), `criado_em`. Registros não são editáveis nem removíveis.
- **Regras**: [RN-007](#rn-007--histórico-de-movimentação-imutável).

### E-008 Notificação

- **Descrição**: registro persistente (outbox) de uma notificação a ser enviada por e-mail.
- **Atributos**: `id`, `destinatario_id` (→ E-001), `tipo`
  (`ATRIBUICAO` | `MUDANCA_COLUNA` | `NOVO_COMENTARIO`), `tarefa_id` (→ E-005),
  `status_envio` (`PENDENTE` | `ENVIADA` | `FALHA`), `tentativas`, `criado_em`, `enviado_em`.
- **Regras**: [RN-008](#rn-008--notificações-por-evento).

## 5. Requisitos Funcionais (Regras de Negócio)

### RN-001 — Provisionamento de usuários restrito ao Admin

- **Statement**: Apenas usuários com papel global `ADMIN` podem criar, desativar ou
  reativar contas. Não há auto-cadastro.
- **Rationale**: Controle de acesso centralizado em ambiente fechado (não multitenant).
- **Applies to**: [E-001 Usuário](#e-001-usuário).
- **Status**: active

### RN-002 — Autenticação obrigatória

- **Statement**: Todo endpoint, exceto o de login, exige um token JWT válido; requisições
  sem token ou com token expirado/inválido são rejeitadas com HTTP 401.
- **Rationale**: Garantir que apenas usuários autenticados acessem o sistema.
- **Applies to**: [E-001 Usuário](#e-001-usuário) (todas as operações).
- **Status**: active

### RN-003 — Acesso restrito a membros do projeto

- **Statement**: Um usuário só pode visualizar ou operar sobre um projeto e seus recursos
  (colunas, tarefas, comentários, histórico) se for membro daquele projeto; caso contrário
  recebe HTTP 403. O Admin global pode acessar para fins administrativos.
- **Rationale**: Isolamento de dados entre equipes sem multitenancy.
- **Applies to**: [E-002 Projeto](#e-002-projeto), [E-003 Membro do Projeto](#e-003-membro-do-projeto),
  [E-004 Coluna](#e-004-coluna), [E-005 Tarefa](#e-005-tarefa),
  [E-006 Comentário](#e-006-comentário), [E-007 Histórico de Movimentação](#e-007-histórico-de-movimentação).
- **Status**: active

### RN-004 — Permissões por papel no projeto

- **Statement**: No escopo de um projeto: o **Dono** gerencia o projeto, seus membros e suas
  colunas, e possui todas as permissões de Membro; o **Membro** cria, edita, move e exclui
  tarefas e comenta; o **Observador** tem acesso somente leitura.
- **Rationale**: RBAC granular por projeto.
- **Applies to**: [E-003 Membro do Projeto](#e-003-membro-do-projeto),
  [E-005 Tarefa](#e-005-tarefa), [E-006 Comentário](#e-006-comentário).
- **Status**: active

### RN-005 — Colunas flexíveis com conjunto padrão

- **Statement**: Cada projeto é um quadro cujas colunas são customizáveis (criar, renomear,
  reordenar, remover). Ao criar um projeto, são geradas automaticamente as colunas padrão
  `Pendente`, `Em Progresso`, `Em Revisão` e `Concluído`, que servem de ponto de partida.
  Toda tarefa pertence a exatamente uma coluna do seu projeto. Um projeto deve ter ao menos
  uma coluna; uma coluna que contém tarefas não pode ser removida antes que suas tarefas
  sejam movidas para outra coluna.
- **Rationale**: Flexibilidade do fluxo Kanban (requisito do enunciado), com um padrão
  sensato como fallback.
- **Applies to**: [E-002 Projeto](#e-002-projeto), [E-004 Coluna](#e-004-coluna),
  [E-005 Tarefa](#e-005-tarefa).
- **Status**: active

### RN-006 — Responsável deve ser membro do projeto

- **Statement**: O responsável de uma tarefa, quando definido, deve ser membro do projeto ao
  qual a tarefa pertence; atribuir um não-membro é rejeitado.
- **Rationale**: Atribuição estrita de responsáveis (requisito do enunciado).
- **Applies to**: [E-005 Tarefa](#e-005-tarefa), [E-003 Membro do Projeto](#e-003-membro-do-projeto).
- **Status**: active

### RN-007 — Histórico de movimentação imutável

- **Statement**: Toda mudança de coluna de uma tarefa gera um registro append-only contendo
  coluna de origem, coluna de destino (com os nomes no momento da mudança), autor e data/hora;
  registros de histórico não podem ser editados nem excluídos.
- **Rationale**: Segurança e rastreabilidade do histórico de mudanças (requisito do enunciado).
- **Applies to**: [E-005 Tarefa](#e-005-tarefa), [E-007 Histórico de Movimentação](#e-007-histórico-de-movimentação).
- **Status**: active

### RN-008 — Notificações por evento

- **Statement**: O sistema gera notificações por e-mail, de forma assíncrona, quando:
  (a) um usuário é atribuído como responsável de uma tarefa; (b) uma tarefa muda de coluna;
  (c) um novo comentário é adicionado. Os destinatários são o responsável da tarefa e o Dono
  do projeto, excluindo o autor da ação.
- **Rationale**: Visibilidade do fluxo de trabalho (requisito do enunciado).
- **Applies to**: [E-008 Notificação](#e-008-notificação), [E-005 Tarefa](#e-005-tarefa),
  [E-006 Comentário](#e-006-comentário).
- **Status**: active

### RN-009 — Gestão do projeto restrita ao Dono

- **Statement**: Editar dados do projeto, excluí-lo, gerenciar membros (adicionar, remover
  ou alterar papel) e gerenciar colunas (criar, renomear, reordenar, remover) são ações
  permitidas somente ao Dono do projeto (ou ao Admin global).
- **Rationale**: Governança do projeto.
- **Applies to**: [E-002 Projeto](#e-002-projeto), [E-003 Membro do Projeto](#e-003-membro-do-projeto),
  [E-004 Coluna](#e-004-coluna).
- **Status**: active

## 6. Requisitos não funcionais

### NFR-001 — Autenticação segura

- **Category**: security
- **Requirement**: Senhas armazenadas com hash adaptativo (bcrypt ou argon2), nunca em
  texto puro; autenticação via JWT assinado, com expiração ≤ 24h; tráfego sob TLS 1.2+.
- **Verification**: revisão de configuração e testes automatizados de login; inspeção de
  que nenhuma senha aparece em logs ou respostas.

### NFR-002 — Autorização (RBAC)

- **Category**: security
- **Requirement**: Toda requisição a recurso protegido valida o papel global e o papel no
  projeto antes de executar; tentativas não autorizadas retornam 401/403.
- **Verification**: suíte de testes automatizados cobrindo cada papel (Admin, Dono, Membro,
  Observador, não-membro).

### NFR-003 — Auditoria do histórico de movimentação

- **Category**: observability
- **Requirement**: 100% das mudanças de coluna são registradas com autor, data/hora, coluna
  de origem e de destino; registros imutáveis e consultáveis por tarefa.
- **Verification**: testes automatizados que verificam a criação do registro a cada
  movimentação e a ausência de endpoints de edição/exclusão do histórico.

### NFR-004 — Notificações assíncronas

- **Category**: performance
- **Requirement**: O envio de e-mail não bloqueia a resposta da API; o disparo é delegado a
  processamento em background (fila/worker ou task assíncrona). O tempo de resposta do
  endpoint que origina a notificação não depende do tempo de envio do e-mail.
- **Verification**: teste medindo a latência do endpoint com SMTP lento/mockado; inspeção
  da fila / registro de outbox.

### NFR-005 — Desempenho das operações CRUD

- **Category**: performance
- **Requirement**: P95 de latência dos endpoints CRUD ≤ 300 ms sob carga leve (até 50 req/s)
  em ambiente local.
- **Verification**: teste de carga local (ex.: Locust ou k6).

### NFR-006 — Confiabilidade de entrega de e-mail

- **Category**: availability
- **Requirement**: Cada notificação possui registro persistente com status
  (`PENDENTE`, `ENVIADA`, `FALHA`) e ao menos uma re-tentativa automática em caso de falha.
- **Verification**: teste com SMTP indisponível verificando a re-tentativa e a marcação de status.

### NFR-007 — Privacidade dos dados pessoais (LGPD)

- **Category**: compliance
- **Requirement**: Dados pessoais (nome, e-mail) acessíveis apenas a usuários autorizados;
  senhas nunca expostas em respostas/logs; o Admin pode remover/anonimizar uma conta.
- **Verification**: revisão de endpoints e payloads; teste de remoção de conta.

## 7. Fora de escopo (MVP)

- Frontend / interface gráfica.
- Multitenancy (organizações isoladas).
- Múltiplos quadros por projeto (cada projeto é um único quadro).
- Auto-cadastro, verificação de e-mail, recuperação de senha, OAuth/SSO.
- Anexos, checklists, etiquetas/labels e subtarefas.
- Notificações in-app, push ou via WebSocket.
- Relatórios, métricas e dashboards analíticos.
- Integrações externas (calendário, Slack, etc.).
