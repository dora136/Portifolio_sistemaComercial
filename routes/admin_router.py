from fastapi import APIRouter, Query, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pathlib import Path
from collections import defaultdict

from config.config import settings
from demo_data import get_solucoes, list_comerciais, list_contratos_financeiro, list_leads
from utils.auth_utils import get_authenticated_user, check_admin

router = APIRouter(prefix="/portfolio", tags=["admin"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _build_user(auth_user):
    if auth_user:
        nome = auth_user.get("nome_completo", "Usuário")
        parts = nome.split()
        initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else nome[:2].upper()
        return {
            "id": auth_user.get("id"),
            "name": nome,
            "role": auth_user.get("roles", [""])[0] if auth_user.get("roles") else "",
            "roles": auth_user.get("roles") or [],
            "initials": initials,
        }
    return {"id": None, "name": "Usuário", "role": "", "roles": [], "initials": "US"}


def _parse_flag(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"1", "true", "t", "sim", "yes", "y"}
    return bool(value)


@router.get("/administracao", response_class=HTMLResponse)
async def administracao(
    request: Request,
    status: Optional[str] = Query(default="todos", description="Filtro: ativos, inativos, todos"),
    auth_user=Depends(get_authenticated_user),
):
    redirect = check_admin(auth_user)
    if redirect:
        return redirect
    user = _build_user(auth_user)
    status_filtro = (status or "todos").strip().lower()
    if status_filtro not in ("ativos", "inativos", "todos"):
        status_filtro = "todos"

    if settings.PORTFOLIO_DEMO_MODE:
        colaboradores = list_comerciais()
        solucoes = get_solucoes()
        leads = list_leads()
        entradas = list_contratos_financeiro("entradas")
    else:
        try:
            from infrastructure.db.colaboradores_repository import ColaboradoresRepositorySql
            from infrastructure.db.solucoes_repository import SolucoesRepositorySql
            from infrastructure.db.leads_repository import LeadsRepositorySql
            from infrastructure.db.financeiro_repository import FinanceiroRepositorySql

            colab_repo = ColaboradoresRepositorySql()
            sol_repo = SolucoesRepositorySql()
            leads_repo = LeadsRepositorySql()
            fin_repo = FinanceiroRepositorySql()

            colaboradores = colab_repo.list_comerciais_exceto_ia()
            solucoes = sol_repo.list_solucoes()
            leads = leads_repo.list_comercial_leads()
            entradas = fin_repo.list_contratos_financeiro("entradas")
        except Exception:
            colaboradores, solucoes, leads, entradas = [], [], [], []

    # Aplicar filtro de status
    if status_filtro == "ativos":
        colaboradores = [c for c in colaboradores if ((c.get("status") if isinstance(c, dict) else c.status) or "").strip().lower() == "ativo"]
    elif status_filtro == "inativos":
        colaboradores = [c for c in colaboradores if ((c.get("status") if isinstance(c, dict) else c.status) or "").strip().lower() != "ativo"]

    # Mapas de nomes
    colab_map = {(c["id_col"] if isinstance(c, dict) else c.id_col): (c["nome"] if isinstance(c, dict) else c.nome) for c in colaboradores}
    # Também mapear por id_crm pois id_colab_comercial usa crm id
    colab_crm_map = {}
    for c in colaboradores:
        crm = c["id_crm_colab"] if isinstance(c, dict) else c.id_crm_colab
        nome = c["nome"] if isinstance(c, dict) else c.nome
        if crm:
            colab_crm_map[str(crm)] = nome

    solucao_map = {(s["id_solucao"] if isinstance(s, dict) else s.id_solucao): (s["nome_solucao"] if isinstance(s, dict) else s.nome_solucao) for s in solucoes}

    # Mapear etapas por solução (id -> nome, sucesso, perdido)
    etapas_by_solucao = {}
    success_stages = {}
    lost_stages = {}
    for s in solucoes:
        sid = s["id_solucao"] if isinstance(s, dict) else s.id_solucao
        etapas = (s.get("kanban_etapas") if isinstance(s, dict) else s.kanban_etapas) or []
        etapa_names = {}
        success_set = set()
        lost_set = set()
        for e in etapas:
            try:
                eid = int(e.get("id"))
            except (TypeError, ValueError):
                continue
            etapa_names[eid] = e.get("nome", f"Etapa {eid}")
            if _parse_flag(e.get("sucesso")):
                success_set.add(eid)
            if _parse_flag(e.get("perdido")):
                lost_set.add(eid)
        etapas_by_solucao[sid] = etapa_names
        success_stages[sid] = success_set
        lost_stages[sid] = lost_set

    # Set de nomes dos colaboradores filtrados (IA já excluído pela query)
    nomes_ativos = {(c["nome"] if isinstance(c, dict) else c.nome) for c in colaboradores}

    # Resolver nome do colaborador de cada lead
    # id_colab_comercial é crm id, comercial_nome já vem resolvido
    def resolve_colab_nome(lead):
        # Prioridade: colab_comercial_nome (representante Comercial)
        if (lead.get("colab_comercial_nome") if isinstance(lead, dict) else lead.colab_comercial_nome):
            return lead.get("colab_comercial_nome") if isinstance(lead, dict) else lead.colab_comercial_nome
        # Fallback: comercial_nome (responsável comercial)
        if (lead.get("comercial_nome") if isinstance(lead, dict) else lead.comercial_nome):
            return lead.get("comercial_nome") if isinstance(lead, dict) else lead.comercial_nome
        return None

    # ── KPIs por colaborador ──
    colab_leads_prospeccao = defaultdict(int)
    colab_leads_fechados = defaultdict(int)
    colab_leads_perdidos = defaultdict(int)
    colab_leads_total = defaultdict(int)
    colab_solucoes = defaultdict(lambda: defaultdict(int))
    colab_etapas = defaultdict(lambda: defaultdict(int))  # colab -> "etapa_nome" -> count

    for lead in leads:
        nome_colab = resolve_colab_nome(lead)
        if not nome_colab or nome_colab not in nomes_ativos:
            continue
        sid = lead["id_solucao"] if isinstance(lead, dict) else lead.id_solucao
        etapa = lead["id_etapa"] if isinstance(lead, dict) else lead.id_etapa
        sol_name = solucao_map.get(sid, f"Solução {sid}")

        colab_leads_total[nome_colab] += 1
        colab_solucoes[nome_colab][sol_name] += 1

        # Classificar por status
        s_stages = success_stages.get(sid, set())
        l_stages = lost_stages.get(sid, set())

        if etapa in s_stages:
            colab_leads_fechados[nome_colab] += 1
        elif etapa in l_stages:
            colab_leads_perdidos[nome_colab] += 1
        else:
            colab_leads_prospeccao[nome_colab] += 1

        # Etapa por colaborador
        etapa_names = etapas_by_solucao.get(sid, {})
        etapa_nome = etapa_names.get(etapa, f"Etapa {etapa}")
        colab_etapas[nome_colab][etapa_nome] += 1

    # ── Valor esperado por mês por colaborador ──
    # Mapear id_comercial_lead → colab nome via leads
    lead_to_colab = {}
    for lead in leads:
        nome_colab = resolve_colab_nome(lead)
        if nome_colab and nome_colab in nomes_ativos:
            lead_to_colab[lead["id_comercial"] if isinstance(lead, dict) else lead.id_comercial] = nome_colab

    colab_valor_por_mes = defaultdict(lambda: defaultdict(float))
    for contrato in entradas:
        lead_id = contrato.get("id_comercial_lead", 0)
        nome_colab = lead_to_colab.get(lead_id)
        if not nome_colab:
            continue
        for parcela in contrato.get("parcelas", []):
            ref = parcela.get("referencia_esperado") or ""
            val = parcela.get("valor_esperado") or 0
            if ref and val:
                mes = ref[:7]  # YYYY-MM
                colab_valor_por_mes[nome_colab][mes] += float(val)

    # ── Montar dados para o template ──
    all_colabs = sorted(set(
        list(colab_leads_total.keys()) +
        list(colab_valor_por_mes.keys())
    ))

    # Filtrar "Sem responsável" se não tiver leads relevantes
    if not all_colabs:
        all_colabs = [(c["nome"] if isinstance(c, dict) else c.nome) for c in colaboradores]

    # KPIs totais
    total_leads = len(leads)
    total_prospeccao = sum(colab_leads_prospeccao.values())
    total_fechados = sum(colab_leads_fechados.values())
    total_perdidos = sum(colab_leads_perdidos.values())
    taxa_conversao = round((total_fechados / total_leads * 100), 1) if total_leads > 0 else 0

    # Dados por colaborador para os gráficos
    chart_colabs = [c for c in all_colabs if c != "Sem responsável"][:20]

    chart_prospeccao = [colab_leads_prospeccao.get(c, 0) for c in chart_colabs]
    chart_fechados = [colab_leads_fechados.get(c, 0) for c in chart_colabs]
    chart_perdidos = [colab_leads_perdidos.get(c, 0) for c in chart_colabs]

    # Soluções por colaborador (stacked bar)
    all_solucoes = sorted(set(
        sol for colab_sols in colab_solucoes.values() for sol in colab_sols
    ))
    chart_solucoes_data = {}
    for sol in all_solucoes:
        chart_solucoes_data[sol] = [colab_solucoes.get(c, {}).get(sol, 0) for c in chart_colabs]

    # Valor por mês (line chart)
    all_meses = sorted(set(
        mes for colab_meses in colab_valor_por_mes.values() for mes in colab_meses
    ))
    chart_valor_mes = {}
    for c in chart_colabs:
        chart_valor_mes[c] = [colab_valor_por_mes.get(c, {}).get(m, 0) for m in all_meses]

    # Etapas por colaborador (heatmap/table data)
    all_etapas = sorted(set(
        etapa for colab_et in colab_etapas.values() for etapa in colab_et
    ))
    chart_etapas_data = []
    for c in chart_colabs:
        row = {"colab": c}
        for etapa in all_etapas:
            row[etapa] = colab_etapas.get(c, {}).get(etapa, 0)
        chart_etapas_data.append(row)

    # Ranking por performance (fechados - perdidos)
    ranking = sorted(
        [{"nome": c, "fechados": colab_leads_fechados.get(c, 0),
          "perdidos": colab_leads_perdidos.get(c, 0),
          "prospeccao": colab_leads_prospeccao.get(c, 0),
          "total": colab_leads_total.get(c, 0),
          "taxa": round(colab_leads_fechados.get(c, 0) / colab_leads_total.get(c, 1) * 100, 1)}
         for c in chart_colabs],
        key=lambda x: x["fechados"],
        reverse=True,
    )

    return templates.TemplateResponse("page_administracao.html", {
        "request": request,
        "user": user,
        "kpis": [],
        "portal_url": settings.PORTAL_URL or "#",
        "status_filtro": status_filtro,
        # KPIs globais
        "total_leads": total_leads,
        "total_prospeccao": total_prospeccao,
        "total_fechados": total_fechados,
        "total_perdidos": total_perdidos,
        "taxa_conversao": taxa_conversao,
        "total_colaboradores": len(chart_colabs),
        # Chart data
        "chart_colabs": chart_colabs,
        "chart_prospeccao": chart_prospeccao,
        "chart_fechados": chart_fechados,
        "chart_perdidos": chart_perdidos,
        "chart_solucoes_data": chart_solucoes_data,
        "all_solucoes": all_solucoes,
        "chart_valor_mes": chart_valor_mes,
        "all_meses": all_meses,
        "chart_etapas_data": chart_etapas_data,
        "all_etapas": all_etapas,
        "ranking": ranking,
    })
