# Parceiros

## Rota e Template
- Rota: `GET /portfolio/parceiros`
- Template: `templates/page_parceiros.html`
- Layout base: `templates/base.html`
- Router: `routes/parceiros_router.py`

## Dados Injetados no Frontend
- `window.PARTNERS_DATA`: lista de parceiros montada no backend.

Campos principais em cada parceiro:
- `id`, `name`, `cnpj`, `razaoSocial`, `state`, `createdAt`
- `modules`: lista com `comercial` e/ou `indicador`
- `status`: `active`, `pending` ou `blocked`
- `folPath`: caminho da pasta do parceiro
- `comercialSolutions`: lista de solucoes Comercial do parceiro (com KPIs)
- `indicadorData`: KPIs do modulo Indicacao (quando ativo)

Campos de `comercialSolutions`:
- `id`, `name`, `icon`, `color`, `status`, `startDate`, `endDate`
- `closedLeads`, `leadsGenerated`, `leadsNegotiation`

Campos de `indicadorData`:
- `leadsGenerated`, `leadsNegotiation`, `leadsClosed`, `conversionRate`

## Fonte de Dados
- `ParceirosRepositorySql.list_parceiros()` (base dos parceiros).
- `ParceirosRepositorySql.get_comercial_solutions()` (solucoes Comercial com KPIs de leads por parceiro).
- `ParceirosRepositorySql.get_indicacao_stats()` (KPIs do modulo Indicacao: gerados, negociacao, fechados, taxa).
- Status consolidado via `get_partner_status()` em `routes/parceiros_router.py`.

## Regras de Status
- `get_partner_status()` resolve o status consolidado:
  - `blocked`: se status_comercial ou status_indicacao contiver "bloqueado", "blocked" ou "inativo".
  - `active`: se modulo_comercial ou modulo_indicacao estiver ativo.
  - `pending`: demais casos.

## UI
- Master panel com busca e filtros de Status e Modulo.
- Lista de parceiros com status e tags de modulos.
- Detail panel com dados cadastrais e cards por modulo (Comercial e Indicacao).
- KPIs do modulo Comercial: leads gerados, em negociacao e fechados por solucao.
- KPIs do modulo Indicacao: leads gerados, negociacao, fechados e taxa de conversao.

## Interacoes
- Busca filtra por nome ou CNPJ.
- Filtros criam chips aplicados e atualizam a lista.
- Selecionar parceiro atualiza o detail panel.
- Clique em solucao Comercial abre o slide-over de leads.

## Modulos e Acoes
- Ativar Indicacao: `POST /portfolio/parceiros/{parceiro_id}/indicacao/ativar`.
- Ativar Comercial: abre modal de solucoes e envia `POST /portfolio/parceiros/{parceiro_id}/portfolio/ativar`.
- Lista de solucoes ativas para o modal: `GET /portfolio/parceiros/solucoes-ativas`.

## Slide-over de Lead
- Disparado ao clicar em uma solucao no detail.
- Busca dados em `GET /portfolio/api/leads/parceiro/{parceiro_id}`.
- Reutiliza `static/js/lead-slideover.js`.
