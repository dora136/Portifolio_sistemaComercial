# Leads

## Rota e Template
- Rota: `GET /portfolio/leads`
- Template: `templates/page_leads.html`
- Layout base: `templates/base.html`
- Router: `routes/lead_router.py`

## Dados Injetados no Frontend
- `window.LEADS_DATA`: lista de leads (modelo base em `domain.models.LeadModel`).
- `window.SOLUCOES_DATA`: solucoes ativas com kanban, parceiros e campos de registro.

Campos principais de `LEADS_DATA`:
- `id` (formato `{id_comercial}-{id_solucao}`), `id_comercial`, `id_solucao`, `id_etapa`
- `name`, `company`, `nome_fantasia`, `razao_social`, `cnpj`
- `id_colab_comercial`, `colab_comercial_nome`, `comercial_nome`
- `id_comercial_parceiro`, `representante_parceiro_nome`
- `informacoes` (lista de campos dinamicos com name, type, value)
- `lastAction`, `createdAt`, `email`

## Fonte de Dados
- `LeadsRepositorySql.list_comercial_leads()` para montar `LEADS_DATA`.
- `SolucoesRepositorySql.list_solucoes_ativas()` para tabs e kanban por solucao.
- Nomes de colaboradores resolvidos via `ColaboradoresRepositorySql` com cache interno.

## UI
- Tabs por solucao (service tabs).
- Kanban com colunas por etapa.
- Cards com nome, empresa, responsavel e data.

## Regras e Comportamento
- Etapas ordenadas por `ordem_id` e filtradas por `ativo` (etapas com `ativo = 0` nao aparecem).
- Fallback para kanban padrao se a solucao nao tiver etapas.
- Leads filtrados por solucao e por etapa (match por `id_etapa`).
- Lead em etapa de sucesso nao pode ser movido para outra etapa (HTTP 409).
- Clique no card abre slide-over com edicao.

## Slide-over de Lead
- Componente: `static/js/lead-slideover.js`.
- Exibe dados gerais, informacoes da solucao, historico e campos editaveis.
- Campos dinamicos usam `lead.informacoes`; se vazio, usa `solucao.registroInfo`.
- Campos especiais: `Estagio` (select de etapas) e `Parceiro` (select de parceiros).
- Botao `Excluir` aparece apenas no slide-over (nao no card).

## APIs Utilizadas
- `PUT /portfolio/api/leads`: salva edicoes do lead (etapa, parceiro, informacoes).
- `DELETE /portfolio/api/leads/{id_comercial}/{id_solucao}`: exclui lead do kanban.
- `GET /portfolio/api/leads/parceiro/{parceiro_id}`: leads e solucoes de um parceiro.
- `GET /portfolio/api/leads/comercial/{comercial_id}`: leads e solucoes por comercial.
