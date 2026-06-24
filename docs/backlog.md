# Backlog - Delta Tasks (Gerenciador de Tarefas Kanban)

Histórias de usuário do MVP, agrupadas por épico. Cada história referencia as regras de
negócio (`RN-###`) e as entidades de domínio (`E-###`) definidas em
[requisitos.md](requisitos.md). IDs são estáveis: se uma história for descartada, o ID não
é reutilizado.

**Filosofia**: MVP enxuto - apenas backend (API REST) em Python, não multitenant. Convenções
de papéis, estrutura e decisões de escopo em
[requisitos.md §3](requisitos.md#3-decisões-de-escopo-lacunas-resolvidas).

## Épicos

| Épico | Tema | Histórias |
|-------|------|-----------|
| 1 | Autenticação e Usuários | US-001 a US-004 |
| 2 | Projetos (Quadros), Colunas e Membros | US-005 a US-009 |
| 3 | Tarefas (Cards) e Fluxo Kanban | US-010 a US-015 |
| 4 | Comentários | US-016 a US-017 |
| 5 | Notificações (e-mail assíncrono) | US-018 a US-020 |

## Épico 1 - Autenticação e Usuários

### US-001 - Admin cria usuário

- **As a** Administrador do sistema
- **I want** criar contas informando nome, e-mail e senha inicial
- **So that** somente pessoas autorizadas tenham acesso ao sistema
- **Business rules**: [RN-001](requisitos.md#rn-001--provisionamento-de-usuários-restrito-ao-admin), [RN-002](requisitos.md#rn-002--autenticação-obrigatória)
- **Domain entities**: [E-001 Usuário](requisitos.md#e-001-usuário)
- **Acceptance criteria**:
  - **Given** um Admin autenticado,  
    **when** cria um usuário com e-mail ainda não cadastrado,  
    **then** a conta é criada com a senha armazenada como hash e o usuário consegue autenticar-se.
  - **Given** um e-mail já existente,  
    **when** o Admin tenta criar outro usuário com o mesmo e-mail,  
    **then** a operação é rejeitada com erro de e-mail duplicado.
  - **Given** um usuário não-Admin,  
    **when** tenta criar uma conta,  
    **then** recebe HTTP 403.

### US-002 - Login com e-mail e senha

- **As a** usuário cadastrado
- **I want** autenticar-me com e-mail e senha
- **So that** receber um token de acesso e usar o sistema
- **Business rules**: [RN-001](requisitos.md#rn-001--provisionamento-de-usuários-restrito-ao-admin), [RN-002](requisitos.md#rn-002--autenticação-obrigatória)
- **Domain entities**: [E-001 Usuário](requisitos.md#e-001-usuário)
- **Acceptance criteria**:
  - **Given** credenciais válidas de um usuário ativo,  
    **when** faz login,  
    **then** recebe um token JWT válido.
  - **Given** senha incorreta ou conta desativada,  
    **when** tenta o login,  
    **then** recebe HTTP 401 sem indicar qual campo falhou.

### US-003 - Admin desativa/reativa usuário

- **As a** Administrador do sistema
- **I want** desativar ou reativar contas
- **So that** revogar ou restaurar acesso sem apagar dados
- **Business rules**: [RN-001](requisitos.md#rn-001--provisionamento-de-usuários-restrito-ao-admin)
- **Domain entities**: [E-001 Usuário](requisitos.md#e-001-usuário)
- **Acceptance criteria**:
  - **Given** um usuário ativo,  
    **when** o Admin o desativa,  
    **then** ele deixa de conseguir autenticar e tokens existentes deixam de ser aceitos.
  - **Given** um usuário desativado,  
    **when** o Admin o reativa,  
    **then** ele volta a conseguir autenticar.

### US-004 - Usuário altera a própria senha

- **As a** usuário autenticado
- **I want** alterar minha senha informando a senha atual
- **So that** manter minha conta segura
- **Business rules**: [RN-002](requisitos.md#rn-002--autenticação-obrigatória)
- **Domain entities**: [E-001 Usuário](requisitos.md#e-001-usuário)
- **Acceptance criteria**:
  - **Given** a senha atual correta,  
    **when** informa uma nova senha,  
    **then** a senha é atualizada (hash) e o login passa a exigir a nova senha.
  - **Given** a senha atual incorreta,  
    **when** tenta alterar,  
    **then** a operação é rejeitada com HTTP 400/401.

## Épico 2 - Projetos (Quadros), Colunas e Membros

### US-005 - Criar projeto

- **As a** usuário autenticado
- **I want** criar um projeto com nome e descrição
- **So that** organizar o trabalho de uma equipe em um quadro Kanban
- **Business rules**: [RN-003](requisitos.md#rn-003--acesso-restrito-a-membros-do-projeto), [RN-005](requisitos.md#rn-005--colunas-flexíveis-com-conjunto-padrão)
- **Domain entities**: [E-002 Projeto](requisitos.md#e-002-projeto), [E-003 Membro do Projeto](requisitos.md#e-003-membro-do-projeto), [E-004 Coluna](requisitos.md#e-004-coluna)
- **Acceptance criteria**:
  - **Given** um usuário autenticado,  
    **when** cria um projeto,  
    **then** ele se torna o Dono (membro com papel `DONO`) e o quadro é criado com as colunas padrão (Pendente, Em Progresso, Em Revisão, Concluído).
  - **Given** um nome de projeto vazio,  
    **when** tenta criar,  
    **then** a operação é rejeitada com erro de validação.

### US-006 - Visualizar meus projetos e o quadro

- **As a** membro de um projeto
- **I want** listar os projetos de que participo e abrir o quadro com colunas e tarefas
- **So that** ter visibilidade do fluxo de trabalho
- **Business rules**: [RN-003](requisitos.md#rn-003--acesso-restrito-a-membros-do-projeto), [RN-005](requisitos.md#rn-005--colunas-flexíveis-com-conjunto-padrão)
- **Domain entities**: [E-002 Projeto](requisitos.md#e-002-projeto), [E-004 Coluna](requisitos.md#e-004-coluna), [E-005 Tarefa](requisitos.md#e-005-tarefa)
- **Acceptance criteria**:
  - **Given** um membro do projeto,  
    **when** abre o quadro,  
    **then** vê as colunas na ordem definida, cada uma com suas tarefas.
  - **Given** um usuário que não é membro,  
    **when** tenta acessar o projeto,  
    **then** recebe HTTP 403.

### US-007 - Editar/excluir projeto

- **As a** Dono do projeto
- **I want** editar os dados ou excluir o projeto
- **So that** manter o quadro atualizado ou removê-lo quando não for mais necessário
- **Business rules**: [RN-009](requisitos.md#rn-009--gestão-do-projeto-restrita-ao-dono)
- **Domain entities**: [E-002 Projeto](requisitos.md#e-002-projeto)
- **Acceptance criteria**:
  - **Given** o Dono,  
    **when** edita nome/descrição,  
    **then** as alterações são persistidas.
  - **Given** um Membro (não-Dono),  
    **when** tenta editar ou excluir o projeto,  
    **then** recebe HTTP 403.

### US-008 - Gerenciar membros do projeto

- **As a** Dono do projeto
- **I want** adicionar/remover membros e definir o papel (Membro ou Observador)
- **So that** controlar quem acessa o quadro e com qual permissão
- **Business rules**: [RN-003](requisitos.md#rn-003--acesso-restrito-a-membros-do-projeto), [RN-004](requisitos.md#rn-004--permissões-por-papel-no-projeto), [RN-009](requisitos.md#rn-009--gestão-do-projeto-restrita-ao-dono)
- **Domain entities**: [E-003 Membro do Projeto](requisitos.md#e-003-membro-do-projeto), [E-001 Usuário](requisitos.md#e-001-usuário)
- **Acceptance criteria**:
  - **Given** o Dono,  
    **when** adiciona um usuário existente como Membro,  
    **then** esse usuário passa a acessar o projeto conforme o papel atribuído.
  - **Given** um Observador,  
    **when** tenta adicionar ou remover um membro,  
    **then** recebe HTTP 403.

### US-009 - Gerenciar colunas do quadro

- **As a** Dono do projeto
- **I want** criar, renomear, reordenar e remover colunas do quadro
- **So that** adaptar o fluxo Kanban à forma de trabalho da equipe
- **Business rules**: [RN-005](requisitos.md#rn-005--colunas-flexíveis-com-conjunto-padrão), [RN-009](requisitos.md#rn-009--gestão-do-projeto-restrita-ao-dono)
- **Domain entities**: [E-004 Coluna](requisitos.md#e-004-coluna), [E-002 Projeto](requisitos.md#e-002-projeto)
- **Acceptance criteria**:
  - **Given** o Dono,  
    **when** cria, renomeia ou reordena uma coluna,  
    **then** o quadro reflete a alteração e as tarefas existentes permanecem em suas colunas.
  - **Given** uma coluna que contém tarefas,  
    **when** o Dono tenta removê-la,  
    **then** a operação é rejeitada até que as tarefas sejam movidas para outra coluna.
  - **Given** um Membro ou Observador,  
    **when** tenta alterar as colunas,  
    **then** recebe HTTP 403.

## Épico 3 - Tarefas (Cards) e Fluxo Kanban

### US-010 - Criar tarefa

- **As a** Membro do projeto
- **I want** criar uma tarefa com título, descrição e prazo
- **So that** registrar um item de trabalho no quadro
- **Business rules**: [RN-003](requisitos.md#rn-003--acesso-restrito-a-membros-do-projeto), [RN-004](requisitos.md#rn-004--permissões-por-papel-no-projeto), [RN-005](requisitos.md#rn-005--colunas-flexíveis-com-conjunto-padrão)
- **Domain entities**: [E-005 Tarefa](requisitos.md#e-005-tarefa), [E-004 Coluna](requisitos.md#e-004-coluna)
- **Acceptance criteria**:
  - **Given** um Membro,  
    **when** cria uma tarefa sem informar a coluna,  
    **then** ela é criada na primeira coluna do quadro.
  - **Given** um Observador,  
    **when** tenta criar uma tarefa,  
    **then** recebe HTTP 403.

### US-011 - Editar tarefa

- **As a** Membro do projeto
- **I want** editar título, descrição e prazo de uma tarefa
- **So that** manter as informações da tarefa atualizadas
- **Business rules**: [RN-004](requisitos.md#rn-004--permissões-por-papel-no-projeto)
- **Domain entities**: [E-005 Tarefa](requisitos.md#e-005-tarefa)
- **Acceptance criteria**:
  - **Given** um Membro,  
    **when** edita os campos da tarefa,  
    **then** as alterações são persistidas.
  - **Given** um prazo em formato inválido,  
    **when** tenta salvar,  
    **then** recebe erro de validação.

### US-012 - Atribuir responsável

- **As a** Membro do projeto
- **I want** definir o responsável de uma tarefa
- **So that** deixar claro quem executa o trabalho
- **Business rules**: [RN-006](requisitos.md#rn-006--responsável-deve-ser-membro-do-projeto), [RN-008](requisitos.md#rn-008--notificações-por-evento)
- **Domain entities**: [E-005 Tarefa](requisitos.md#e-005-tarefa), [E-003 Membro do Projeto](requisitos.md#e-003-membro-do-projeto)
- **Acceptance criteria**:
  - **Given** um membro do projeto,  
    **when** é definido como responsável de uma tarefa,  
    **then** a atribuição é salva e ele recebe notificação por e-mail.
  - **Given** um usuário que não é membro do projeto,  
    **when** é indicado como responsável,  
    **then** a operação é rejeitada.

### US-013 - Mover tarefa entre colunas

- **As a** Membro do projeto
- **I want** mover uma tarefa entre as colunas do quadro
- **So that** refletir o andamento real do trabalho
- **Business rules**: [RN-005](requisitos.md#rn-005--colunas-flexíveis-com-conjunto-padrão), [RN-007](requisitos.md#rn-007--histórico-de-movimentação-imutável), [RN-008](requisitos.md#rn-008--notificações-por-evento)
- **Domain entities**: [E-005 Tarefa](requisitos.md#e-005-tarefa), [E-007 Histórico de Movimentação](requisitos.md#e-007-histórico-de-movimentação)
- **Acceptance criteria**:
  - **Given** uma tarefa em uma coluna,  
    **when** é movida para outra coluna do mesmo quadro,  
    **then** a nova coluna é salva e um registro de histórico (origem→destino, com nomes, autor, data/hora) é criado.
  - **Given** uma movimentação concluída,  
    **when** o registro é criado,  
    **then** os envolvidos na tarefa são notificados por e-mail.
  - **Given** uma coluna de destino que pertence a outro projeto,  
    **when** se tenta mover a tarefa para ela,  
    **then** a operação é rejeitada.

### US-014 - Visualizar histórico de movimentações

- **As a** membro do projeto
- **I want** ver o histórico de mudanças de coluna de uma tarefa
- **So that** auditar como e por quem a tarefa evoluiu
- **Business rules**: [RN-007](requisitos.md#rn-007--histórico-de-movimentação-imutável), [RN-003](requisitos.md#rn-003--acesso-restrito-a-membros-do-projeto)
- **Domain entities**: [E-007 Histórico de Movimentação](requisitos.md#e-007-histórico-de-movimentação)
- **Acceptance criteria**:
  - **Given** uma tarefa com movimentações,  
    **when** abro seu histórico,  
    **then** vejo a lista cronológica com coluna de origem, coluna de destino, autor e data/hora.
  - **Given** qualquer usuário,  
    **when** tenta editar ou excluir um registro de histórico,  
    **then** a ação é impossível (não há endpoint) e os dados permanecem intactos.

### US-015 - Excluir tarefa

- **As a** Membro do projeto (ou Dono)
- **I want** excluir uma tarefa
- **So that** remover itens criados por engano ou obsoletos
- **Business rules**: [RN-004](requisitos.md#rn-004--permissões-por-papel-no-projeto)
- **Domain entities**: [E-005 Tarefa](requisitos.md#e-005-tarefa)
- **Acceptance criteria**:
  - **Given** um Membro,  
    **when** exclui uma tarefa,  
    **then** ela deixa de aparecer no quadro.
  - **Given** um Observador,  
    **when** tenta excluir uma tarefa,  
    **then** recebe HTTP 403.

## Épico 4 - Comentários

### US-016 - Comentar em tarefa

- **As a** Membro do projeto
- **I want** adicionar comentários a uma tarefa
- **So that** discutir e registrar contexto sobre o trabalho
- **Business rules**: [RN-003](requisitos.md#rn-003--acesso-restrito-a-membros-do-projeto), [RN-004](requisitos.md#rn-004--permissões-por-papel-no-projeto), [RN-008](requisitos.md#rn-008--notificações-por-evento)
- **Domain entities**: [E-006 Comentário](requisitos.md#e-006-comentário), [E-005 Tarefa](requisitos.md#e-005-tarefa)
- **Acceptance criteria**:
  - **Given** um Membro,  
    **when** adiciona um comentário,  
    **then** ele é salvo com autor e data/hora e os envolvidos na tarefa são notificados por e-mail.
  - **Given** um Observador,  
    **when** tenta comentar,  
    **then** recebe HTTP 403.

### US-017 - Listar comentários da tarefa

- **As a** membro do projeto (incluindo Observador)
- **I want** ver os comentários de uma tarefa em ordem cronológica
- **So that** acompanhar a discussão
- **Business rules**: [RN-003](requisitos.md#rn-003--acesso-restrito-a-membros-do-projeto)
- **Domain entities**: [E-006 Comentário](requisitos.md#e-006-comentário)
- **Acceptance criteria**:
  - **Given** uma tarefa com comentários,  
    **when** abro a tarefa,  
    **then** vejo os comentários em ordem cronológica com autor e data/hora.
  - **Given** um não-membro,  
    **when** tenta listar os comentários,  
    **then** recebe HTTP 403.

## Épico 5 - Notificações (e-mail assíncrono)

### US-018 - Notificar atribuição

- **As a** usuário atribuído como responsável
- **I want** receber um e-mail quando for atribuído a uma tarefa
- **So that** saber que há trabalho aguardando minha ação
- **Business rules**: [RN-008](requisitos.md#rn-008--notificações-por-evento)
- **Domain entities**: [E-008 Notificação](requisitos.md#e-008-notificação), [E-005 Tarefa](requisitos.md#e-005-tarefa)
- **Acceptance criteria**:
  - **Given** que fui atribuído como responsável,  
    **when** a atribuição é salva,  
    **then** é gerada uma notificação por e-mail de forma assíncrona, sem bloquear a resposta da API.
  - **Given** falha temporária no servidor SMTP,  
    **when** o envio falha,  
    **then** a notificação fica registrada como `FALHA` e é re-tentada.

### US-019 - Notificar mudança de coluna

- **As a** envolvido na tarefa (responsável, Dono)
- **I want** receber e-mail quando a tarefa mudar de coluna
- **So that** acompanhar o progresso sem precisar consultar o quadro
- **Business rules**: [RN-008](requisitos.md#rn-008--notificações-por-evento)
- **Domain entities**: [E-008 Notificação](requisitos.md#e-008-notificação), [E-005 Tarefa](requisitos.md#e-005-tarefa)
- **Acceptance criteria**:
  - **Given** uma tarefa movida de coluna,  
    **when** a movimentação é registrada,  
    **then** os envolvidos recebem e-mail com a coluna de origem e a de destino.
  - **Given** que o autor da mudança também é um envolvido,  
    **when** a notificação é gerada,  
    **then** ele não recebe e-mail da própria ação.

### US-020 - Notificar novo comentário

- **As a** envolvido na tarefa
- **I want** receber e-mail quando houver um novo comentário
- **So that** participar da discussão em tempo hábil
- **Business rules**: [RN-008](requisitos.md#rn-008--notificações-por-evento)
- **Domain entities**: [E-008 Notificação](requisitos.md#e-008-notificação), [E-006 Comentário](requisitos.md#e-006-comentário)
- **Acceptance criteria**:
  - **Given** um novo comentário em uma tarefa,  
    **when** é salvo,  
    **then** os envolvidos (exceto o autor) recebem e-mail de forma assíncrona.
  - **Given** o servidor SMTP indisponível,  
    **when** o envio falha,  
    **then** a notificação é registrada e re-tentada.
