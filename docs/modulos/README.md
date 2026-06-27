# 📚 Documentação dos módulos

Guias para desenvolvedores sobre como usar e estender os módulos da aplicação.

| Módulo | Descrição |
| --- | --- |
| [🔐 Autenticação](./autenticacao.md) | Login via JWT em cookies HttpOnly, refresh, troca de senha e proteção de rotas. |
| [👥 Usuários](./usuarios.md) | Listagem, consulta, atualização e remoção de contas (escrita restrita a admin). |

> Convenção comum a todos os módulos: o fluxo é **router → service → repository**
> (o router nunca chama o repositório direto; regra de negócio vai no service).
> A validação de corpo retorna **HTTP 400** (handler global em
> [`app/main.py`](../../app/main.py)).
