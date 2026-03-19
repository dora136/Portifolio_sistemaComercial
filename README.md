# NovaCRM - Sistema de Gestao Comercial

Sistema de gestao comercial completo desenvolvido como projeto de portfolio. Construido com **FastAPI**, **Jinja2** e **JavaScript vanilla**. Roda em **modo demo** por padrao, sem necessidade de banco de dados ou integracao externa.

## Funcionalidades

- **Gestao de Leads** - Kanban configuravel por solucao, com drag-and-drop, edicao inline e exclusao
- **Gestao de Parceiros** - Cadastro, ativacao de modulos (Comercial e Indicacao), acompanhamento via kanban
- **Catalogo de Solucoes** - Criacao e configuracao de solucoes com etapas de kanban personalizadas
- **Modulo Financeiro** - Dashboard de indicadores, gestao de entradas/saidas e controle de pagamentos
- **Contratos** - Gestao de contratos com parcelas e status de pagamento
- **Administracao** - Painel administrativo com visao consolidada
- **Cadastro integrado** - Formulario unificado para cadastro de parceiros e leads com busca por CNPJ

## Tech Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + Uvicorn |
| Templates | Jinja2 |
| Frontend | Vanilla JS + CSS custom properties |
| Validacao | Pydantic v2 + pydantic-settings |
| Icones | Lucide Icons |
| Banco (opcional) | SQL Server via SQLAlchemy + pyodbc |
| CRM (opcional) | Integracao com CRM externo via webhooks |

## Como Executar

```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar aplicacao
python main.py
```

Acesse: **http://localhost:7000/portfolio/home**

## Modo Demo

O projeto roda em modo demo por padrao (`PORTFOLIO_DEMO_MODE=True`):

- Dados ficticios pre-carregados (parceiros, leads, solucoes, contratos)
- Sem necessidade de banco de dados ou `.env`
- Sem necessidade de login ou integracao externa
- Todas as operacoes CRUD funcionam em memoria

Para conectar a um banco SQL Server real, copie `.env.example` para `.env` e configure as variaveis.

## Rotas Principais

| Rota | Descricao |
|------|-----------|
| `/portfolio/home` | Dashboard com KPIs e indicadores |
| `/portfolio/parceiros` | Listagem e ativacao de parceiros |
| `/portfolio/parceiros/acompanhamento` | Kanban de acompanhamento |
| `/portfolio/leads` | Kanban de leads por solucao |
| `/portfolio/solucoes` | Catalogo de solucoes |
| `/portfolio/financeiro` | Dashboard financeiro |
| `/portfolio/financeiro/entradas` | Gestao de entradas |
| `/portfolio/financeiro/saidas` | Gestao de saidas |
| `/portfolio/contratos` | Gestao de contratos |
| `/portfolio/administracao` | Painel administrativo |

## Estrutura do Projeto

```
config/              - Configuracoes (Pydantic Settings) e loader de .env
data/                - Dados de configuracao (metas comerciais)
database/            - DB provider (SQL Server) e catalogo de queries
demo_data.py         - Store em memoria para modo demo
domain/              - Modelos Pydantic, contratos (protocols) e regras de negocio
infrastructure/
  db/                - Repositories SQL (parceiros, leads, solucoes, financeiro, colaboradores)
  external/crm/      - Cliente HTTP para CRM externo
routes/              - Routers FastAPI (paginas e endpoints de API)
services/            - Orquestracao de fluxos de cadastro
static/
  css/               - Estilos (CSS custom properties, tema violeta)
  js/                - Logica frontend (kanban, modais, formularios)
  financeiro/        - Dashboard financeiro (Vite build)
templates/           - Templates Jinja2 (paginas, emails)
utils/               - Autenticacao, mapeadores e helpers
```

## Licenca

Projeto de portfolio para fins demonstrativos. Sinta-se livre para usar como referencia.
