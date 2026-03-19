# Home

## Rota e Template
- Rota: `GET /portfolio/home`
- Template: `templates/page_home.html`
- Layout base: `templates/base.html`
- Router: `routes/home_router.py`

## Contexto Jinja (dados recebidos)
- `user`: dados do usuario autenticado (name, role, initials).
- `dashboard_metrics`: resumo geral do ecossistema.
- `dashboard_solucoes`: lista de linhas do detalhamento por solucao.
- `portal_url`: URL do portal principal para link de retorno.

Campos em `dashboard_metrics`:
- `total_solucoes`
- `total_parceiros`
- `total_leads` (leads em processo)

Campos em cada item de `dashboard_solucoes`:
- `id`, `name`, `type`, `icon`, `accent`
- `parceiros_ativos`
- `leads_em_processo`
- `leads_total`
- `leads_sucesso`
- `leads_perdido`
- `success_rate`
- `bar_pct` (barra proporcional ao score max)

## Fonte de Dados
- `SolucoesRepositorySql.list_solucoes()` para o portfolio e configuracoes de kanban.
- `LeadsRepositorySql.list_comercial_leads()` para contagem de leads por solucao.

## Regras de Calculo
- `max_etapa` por solucao: maior `id` das etapas do kanban (default 4).
- `leads_em_processo`: etapa atual < `max_etapa`.
- `leads_sucesso`: etapa marcada com flag `sucesso` no kanban.
- `leads_perdido`: etapa marcada com flag `perdido` no kanban.
- `success_rate`: `round(leads_sucesso * 100 / leads_total)` (0 se nao ha leads).
- `activation_rate` (no template): `total_leads / total_parceiros * 100`.
- `bar_pct`: proporcional ao score (parceiros + leads_processo), minimo 12% se score > 0.
- Status visual por linha (regras):
  - Novo: parceiros = 0 e leads = 0.
  - Alerta: parceiros = 0 e leads > 0.
  - Atencao: leads > parceiros.
  - Ativo: demais casos.

## UI
- Cards de resumo: Portfolio, Total de parceiros, Leads em pipeline, Taxa de ativacao.
- Tabela "Detalhamento por Ecossistema" com KPI por solucao (parceiros, leads, taxa de sucesso).
- Empty state quando nao ha solucoes cadastradas.

## Scripts e Estilos
- CSS: `static/css/main.css` (classes `home-*`).
- JS: somente `static/js/app.js` (navegacao e modais globais).

## APIs Disponiveis neste Router
- `GET /portfolio/api/crm/leads`: lista leads do ExternalCRM.
- `GET /portfolio/api/crm/lead/{lead_id}`: detalhe de lead CRM.
- `GET /portfolio/api/crm/cnpj-search?cnpj=...`: busca empresa/leads por CNPJ.
- `GET /portfolio/api/comerciais`: lista colaboradores ativos (para select de responsavel).
- `POST /portfolio/api/add`: cadastro global de parceiro/lead (usa `AddLeadService`).
