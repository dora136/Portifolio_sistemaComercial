# Solucoes

## Rota e Template
- Rota: `GET /portfolio/solucoes`
- Template: `templates/page_solucoes.html`
- Layout base: `templates/base.html`
- Router: `routes/solucoes_router.py`

## Dados Injetados no Frontend
- `window.SOLUCOES_DATA`: catalogo de solucoes com detalhes para o UI.
- `window.CAN_MANAGE_SOLUCOES`: booleano de permissao (admin ou parceria_admin).

Campos principais em cada solucao:
- `id`, `name`, `category`, `description`
- `applications` (lista de aplicacoes basicas)
- `partnersCount`, `partners` (nomes dos parceiros vinculados)
- `leads` (lista de `{id_comercial, name}`)
- `avgTicket`, `avgImplementation` (placeholder)
- `icon`, `accentVar` (icone e cor da solucao)
- `kanbanEtapas` (lista de etapas do kanban)
- `registroInfo` (lista de campos de registro)

Campos de `kanbanEtapas`:
- `id`, `nome_etapa`, `color_HEX`, `ativo`, `ordem_id`, `sucesso`, `perdido`

Campos de `registroInfo`:
- `name`, `type` (number, date, string, bool), `value`

## Fonte de Dados
- `SolucoesRepositorySql.list_solucoes()` para base do catalogo.
- `SolucoesRepositorySql.get_parceiros_by_solucao()` para nomes de parceiros.
- `LeadsRepositorySql.get_leads_by_solucao()` para lista de leads vinculados.

## UI
- Master panel com busca e cards das solucoes.
- Detail panel com cards de Sobre, Estatisticas, Aplicacoes, Registro e Kanban.
- Modais: editar solucao, criar solucao, confirmar exclusao, lista de parceiros, lista de leads.

## Permissoes
- `can_manage_solucoes` depende de roles do usuario (`admin` ou `parceria_admin`).
- Se falso, botoes de criar/editar/excluir nao aparecem.

## Regras e Comportamento
- Selecionar solucao atualiza o detail panel.
- Editor usa tabs: Caracteristicas, Cadastro, Campos, Kanban.
- Kanban editor permite ordenar etapas por drag and drop.
- Flags `sucesso` e `perdido` sao mutuamente exclusivas.
- Etapa com `ativo = 0` fica desativada na edicao e nao aparece no kanban da pagina Leads.
- Para solucao `id = 1` (Indicacao), o kanban e bloqueado (gerenciado via CRM externo).
- Ao criar solucao sem campos de registro, 3 campos padrao sao gerados (Data Recebimento, Data Agendamento Reuniao, Data Primeira Reuniao).
- Kanban padrao (se nao definido): Triagem -> Reuniao -> Proposta -> Fechamento.

## APIs Utilizadas
- `POST /portfolio/solucoes`: cria nova solucao (com kanban_etapas, registro_info, icon_id, color_id).
- `PUT /portfolio/solucoes/{solucao_id}`: edita solucao existente (todos os campos editaveis).
- `DELETE /portfolio/solucoes/{solucao_id}`: remove solucao (retorna 409 se ha parceiros ativos).

## Slide-over de Lead
- Modal de Leads lista leads vinculados a solucao.
- Clique em um lead chama `GET /portfolio/api/leads/comercial/{id_comercial}` e abre o slide-over.
- Reutiliza `static/js/lead-slideover.js`.
