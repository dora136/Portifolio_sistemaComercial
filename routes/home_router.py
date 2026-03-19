from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pathlib import Path
from collections import defaultdict
import json
from pydantic import BaseModel, Field, ValidationError, field_validator
from config.config import settings
from demo_data import (
    create_lead as demo_create_lead,
    get_solucoes,
    list_comerciais as demo_list_comerciais,
    list_contratos_financeiro,
    list_leads,
    list_parceiros,
)
# Imports
from infrastructure.external.crm import CrmClient, CrmRepository, CrmLead, CnpjSearchResult
from services.add_lead_services import AddLeadService
from utils.mapper import mapper_b
from infrastructure.db.colaboradores_repository import ColaboradoresRepositorySql
from infrastructure.db.solucoes_repository import SolucoesRepositorySql
from infrastructure.db.leads_repository import LeadsRepositorySql
from infrastructure.db.parceiros_repository import ParceirosRepositorySql
from infrastructure.db.financeiro_repository import FinanceiroRepositorySql
from utils.auth_utils import get_authenticated_user

router = APIRouter(prefix="/portfolio", tags=["home"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

META_CONFIG_PATH = BASE_DIR / "data" / "meta_config.json"


def _load_meta() -> dict:
    try:
        return json.loads(META_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"valor_meta": 38000000, "data_meta": "2026-12-31"}


def _save_meta(data: dict):
    META_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    META_CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

_crm_client = None
_crm_repository = None


class LeadCreatePayload(BaseModel):
    lead_id: Optional[int] = Field(default=None, gt=0)
    solution_ids: List[int] = Field(default_factory=list)
    nome: Optional[str] = None
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None
    segmento: Optional[str] = None
    id_crm_lead: Optional[int] = None
    lead_type: Optional[str] = None
    id_colab_comercial: Optional[str] = None

    @field_validator("nome", mode="before")
    @classmethod
    def normalize_nome_fantasia(cls, value):
        if value is None:
            return None
        # Aceita numero e sempre persiste como string.
        return str(value).strip()


def get_crm_repository() -> CrmRepository:
    """Obtém instância do repositório Crm (lazy initialization)."""
    global _crm_client, _crm_repository

    if _crm_repository is None:
        if not settings.CRM_WEBHOOK_URL:
            raise HTTPException(
                status_code=500,
                detail="CRM_WEBHOOK_URL não configurada"
            )
        _crm_client = CrmClient(
            webhook_url=settings.CRM_WEBHOOK_URL,
            company_webhook_url=settings.CRM_COMPANY_WEBHOOK_URL,
            lead_webhook_url=settings.CRM_LEAD_WEBHOOK_URL,
        )
        _crm_repository = CrmRepository(_crm_client)

    return _crm_repository


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


@router.get('/home', response_class=HTMLResponse)
async def home(request: Request, auth_user=Depends(get_authenticated_user)):
    user = _build_user(auth_user)
    dashboard_solucoes = []
    total_parceiros = 0
    total_leads_process = 0
    total_solucoes = 0

    color_var_map = {
        "cloud": "cloud",
        "cyber": "cyber",
        "consulting": "consulting",
        "analytics": "analytics",
        "indicador": "indicador",
        "comercial": "comercial",
        "primary": "primary",
    }

    def resolve_accent(color_id: Optional[str]) -> str:
        if not color_id:
            return "hsl(var(--primary))"
        raw = str(color_id).strip()
        if raw.startswith("#"):
            return raw
        key = raw.lower()
        var_name = color_var_map.get(key, key or "primary")
        return f"hsl(var(--{var_name}))"

    def parse_flag(value: Optional[object]) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value == 1
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "t", "sim", "yes", "y"}:
                return True
            if normalized in {"0", "false", "f", "nao", "no", "n"}:
                return False
        return bool(value)

    total_parceiros_unicos = None
    entradas = []
    if settings.PORTFOLIO_DEMO_MODE:
        solucoes_models = get_solucoes()
        leads = list_leads()
        parceiros = list_parceiros()
        entradas = list_contratos_financeiro("entradas")
        total_parceiros_unicos = sum(1 for parceiro in parceiros if "comercial" in (parceiro.get("modules") or []))
    else:
        try:
            solucoes_repo = SolucoesRepositorySql()
            leads_repo = LeadsRepositorySql()
            parceiros_repo = ParceirosRepositorySql()
            fin_repo = FinanceiroRepositorySql()
            solucoes_models = solucoes_repo.list_solucoes()
            leads = leads_repo.list_comercial_leads()
            parceiros = parceiros_repo.list_parceiros()
            entradas = fin_repo.list_contratos_financeiro("entradas")
            total_parceiros_unicos = sum(
                1 for parceiro in parceiros if bool(getattr(parceiro, "modulo_comercial", False))
            )
        except Exception:
            solucoes_models = []
            leads = []

    total_solucoes = len(solucoes_models)
    default_max_stage = 4
    max_stage_by_solucao = {}
    success_stage_by_solucao: dict[int, set[int]] = {}
    lost_stage_by_solucao: dict[int, set[int]] = {}
    for model in solucoes_models:
        etapas = (model.get("kanban_etapas") if isinstance(model, dict) else model.kanban_etapas) or []
        etapa_ids = []
        model_id = model["id_solucao"] if isinstance(model, dict) else model.id_solucao
        success_stage_by_solucao[model_id] = set()
        lost_stage_by_solucao[model_id] = set()
        for etapa in etapas:
            try:
                etapa_id = int(etapa.get("id"))
            except (TypeError, ValueError, AttributeError):
                continue
            etapa_ids.append(etapa_id)
            if parse_flag(etapa.get("sucesso")):
                success_stage_by_solucao[model_id].add(etapa_id)
            if parse_flag(etapa.get("perdido")):
                lost_stage_by_solucao[model_id].add(etapa_id)
        max_stage_by_solucao[model_id] = max(etapa_ids) if etapa_ids else default_max_stage

    leads_process_by_solucao = {(model["id_solucao"] if isinstance(model, dict) else model.id_solucao): 0 for model in solucoes_models}
    leads_total_by_solucao = {(model["id_solucao"] if isinstance(model, dict) else model.id_solucao): 0 for model in solucoes_models}
    leads_success_by_solucao = {(model["id_solucao"] if isinstance(model, dict) else model.id_solucao): 0 for model in solucoes_models}
    leads_lost_by_solucao = {(model["id_solucao"] if isinstance(model, dict) else model.id_solucao): 0 for model in solucoes_models}
    for lead in leads:
        try:
            solucao_id = int((lead.get("id_solucao") if isinstance(lead, dict) else lead.id_solucao) or 0)
        except (TypeError, ValueError, AttributeError):
            continue
        if solucao_id not in max_stage_by_solucao:
            continue
        try:
            etapa_id = int((lead.get("id_etapa") if isinstance(lead, dict) else lead.id_etapa) or 1)
        except (TypeError, ValueError, AttributeError):
            etapa_id = 1
        leads_total_by_solucao[solucao_id] = leads_total_by_solucao.get(solucao_id, 0) + 1
        success_stage_ids = success_stage_by_solucao.get(solucao_id, set())
        lost_stage_ids = lost_stage_by_solucao.get(solucao_id, set())
        if etapa_id in success_stage_ids:
            leads_success_by_solucao[solucao_id] = leads_success_by_solucao.get(solucao_id, 0) + 1
            continue
        if etapa_id in lost_stage_ids:
            leads_lost_by_solucao[solucao_id] = leads_lost_by_solucao.get(solucao_id, 0) + 1
            continue

        has_terminal_flags = bool(success_stage_ids or lost_stage_ids)
        if has_terminal_flags:
            leads_process_by_solucao[solucao_id] = leads_process_by_solucao.get(solucao_id, 0) + 1
        elif etapa_id < max_stage_by_solucao[solucao_id]:
            leads_process_by_solucao[solucao_id] = leads_process_by_solucao.get(solucao_id, 0) + 1

    # Valor esperado (receita) por solução a partir dos contratos de entradas
    valor_esperado_by_solucao = {(model["id_solucao"] if isinstance(model, dict) else model.id_solucao): 0.0 for model in solucoes_models}
    for contrato in entradas:
        sid = contrato.get("id_solucao", 0)
        if sid in valor_esperado_by_solucao:
            for parcela in contrato.get("parcelas", []):
                val = parcela.get("valor_esperado") or 0
                valor_esperado_by_solucao[sid] += float(val)

    scores = []
    for model in solucoes_models:
        model_id = model["id_solucao"] if isinstance(model, dict) else model.id_solucao
        parceiros = int((model.get("n_parceiros") if isinstance(model, dict) else model.n_parceiros) or 0)
        leads_process = int(leads_process_by_solucao.get(model_id, 0))
        total_parceiros += parceiros
        total_leads_process += leads_process
        score = parceiros + leads_process
        scores.append(score)

    if total_parceiros_unicos is not None:
        total_parceiros = total_parceiros_unicos

    max_score = max(scores) if scores else 0

    for model in solucoes_models:
        model_id = model["id_solucao"] if isinstance(model, dict) else model.id_solucao
        model_name = model["nome_solucao"] if isinstance(model, dict) else model.nome_solucao
        model_type = model["tipo_solucao"] if isinstance(model, dict) else model.tipo_solucao
        model_icon = model["icon_id"] if isinstance(model, dict) else model.icon_id
        model_color = model["color_id"] if isinstance(model, dict) else model.color_id
        parceiros = int((model.get("n_parceiros") if isinstance(model, dict) else model.n_parceiros) or 0)
        leads_process = int(leads_process_by_solucao.get(model_id, 0))
        leads_total = int(leads_total_by_solucao.get(model_id, 0))
        leads_success = int(leads_success_by_solucao.get(model_id, 0))
        leads_lost = int(leads_lost_by_solucao.get(model_id, 0))
        success_rate = round((leads_success * 100) / leads_total) if leads_total > 0 else 0
        score = parceiros + leads_process
        if max_score > 0:
            bar_pct = round((score / max_score) * 100)
            bar_pct = max(bar_pct, 12) if score > 0 else 6
        else:
            bar_pct = 6
        valor_esp = round(valor_esperado_by_solucao.get(model_id, 0), 2)
        dashboard_solucoes.append({
            "id": model_id,
            "name": model_name,
            "type": model_type,
            "icon": model_icon or "layers",
            "accent": resolve_accent(model_color),
            "parceiros_ativos": parceiros,
            "leads_em_processo": leads_process,
            "leads_total": leads_total,
            "leads_sucesso": leads_success,
            "leads_perdido": leads_lost,
            "success_rate": success_rate,
            "bar_pct": bar_pct,
            "valor_esperado": valor_esp,
        })
    total_valor_esperado = sum(s["valor_esperado"] for s in dashboard_solucoes)
    meta_config = _load_meta()

    return templates.TemplateResponse("page_home.html", {
        "request": request,
        "user": user,
        "kpis": [],
        "dashboard_solucoes": dashboard_solucoes,
        "dashboard_metrics": {
            "total_solucoes": total_solucoes,
            "total_parceiros": total_parceiros,
            "total_leads": total_leads_process,
        },
        "meta_config": meta_config,
        "total_valor_esperado": total_valor_esperado,
        "portal_url": settings.PORTAL_URL or "#",
    })


@router.get("/api/dashboard-charts")
async def dashboard_charts(auth_user=Depends(get_authenticated_user)):
    """Retorna dados agregados para os graficos do dashboard."""
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            entradas = list_contratos_financeiro("entradas")
            saidas = list_contratos_financeiro("saidas")
            solucoes = get_solucoes()
            leads = list_leads()
            solucao_names = {s["id_solucao"]: s["nome_solucao"] for s in solucoes}
        else:
            fin_repo = FinanceiroRepositorySql()
            sol_repo = SolucoesRepositorySql()
            leads_repo = LeadsRepositorySql()
            entradas = fin_repo.list_contratos_financeiro("entradas")
            saidas = fin_repo.list_contratos_financeiro("saidas")
            solucoes = sol_repo.list_solucoes()
            leads = leads_repo.list_comercial_leads()
            solucao_names = {s.id_solucao: s.nome_solucao for s in solucoes}

        # --- 1) Receita x Custo por mes (todas as solucoes) ---
        receita_por_mes = defaultdict(float)
        custo_por_mes = defaultdict(float)

        for contrato in entradas:
            for parcela in contrato.get("parcelas", []):
                ref = parcela.get("referencia_esperado") or ""
                val = parcela.get("valor_esperado") or 0
                if ref and val:
                    mes_key = ref[:7]  # YYYY-MM
                    receita_por_mes[mes_key] += float(val)

        for contrato in saidas:
            for parcela in contrato.get("parcelas", []):
                ref = parcela.get("referencia_esperado") or ""
                val = parcela.get("valor_esperado") or 0
                if ref and val:
                    mes_key = ref[:7]
                    custo_por_mes[mes_key] += float(val)

        all_months = sorted(set(list(receita_por_mes.keys()) + list(custo_por_mes.keys())))
        receita_custo_mensal = {
            "labels": all_months,
            "receita": [round(receita_por_mes.get(m, 0), 2) for m in all_months],
            "custo": [round(custo_por_mes.get(m, 0), 2) for m in all_months],
        }

        # --- 2) Leads por solucao (para pizza) ---
        leads_por_solucao = defaultdict(int)
        for lead in leads:
            sid = lead["id_solucao"] if isinstance(lead, dict) else lead.id_solucao
            nome = solucao_names.get(sid, f"Solucao {sid}")
            leads_por_solucao[nome] += 1

        leads_pizza = {
            "labels": list(leads_por_solucao.keys()),
            "data": list(leads_por_solucao.values()),
        }

        # --- 3) Receita x Custo - Data Analytics ---
        ml_receita_mes = defaultdict(float)
        ml_custo_mes = defaultdict(float)

        for contrato in entradas:
            nome_sol = (contrato.get("nome_solucao") or "").strip().lower()
            if "data analytics" in nome_sol:
                for parcela in contrato.get("parcelas", []):
                    ref = parcela.get("referencia_esperado") or ""
                    val = parcela.get("valor_esperado") or 0
                    if ref and val:
                        ml_receita_mes[ref[:7]] += float(val)

        for contrato in saidas:
            nome_sol = (contrato.get("nome_solucao") or "").strip().lower()
            if "data analytics" in nome_sol:
                for parcela in contrato.get("parcelas", []):
                    ref = parcela.get("referencia_esperado") or ""
                    val = parcela.get("valor_esperado") or 0
                    if ref and val:
                        ml_custo_mes[ref[:7]] += float(val)

        ml_months = sorted(set(list(ml_receita_mes.keys()) + list(ml_custo_mes.keys())))
        data_analytics = {
            "labels": ml_months,
            "receita": [round(ml_receita_mes.get(m, 0), 2) for m in ml_months],
            "custo": [round(ml_custo_mes.get(m, 0), 2) for m in ml_months],
        }

        # --- 4) Receita Cloud Computing ---
        gd_receita_mes = defaultdict(float)

        for contrato in entradas:
            nome_sol = (contrato.get("nome_solucao") or "").strip().lower()
            if nome_sol in ("cloud", "cloud computing"):
                for parcela in contrato.get("parcelas", []):
                    ref = parcela.get("referencia_esperado") or ""
                    val = parcela.get("valor_esperado") or 0
                    if ref and val:
                        gd_receita_mes[ref[:7]] += float(val)

        gd_months = sorted(gd_receita_mes.keys())
        receita_cloud = {
            "labels": gd_months,
            "receita": [round(gd_receita_mes.get(m, 0), 2) for m in gd_months],
        }

        # --- 5) Solucoes Comercial ---
        comercial_keywords = ["cloud", "cyber", "analytics", "consulting", "data analytics", "cybersecurity", "sistema comercial", "comercial"]
        comercial_receita_sol = defaultdict(float)
        comercial_custo_sol = defaultdict(float)

        def _is_comercial_solution(nome: str) -> bool:
            nome_lower = nome.strip().lower()
            return any(kw in nome_lower for kw in comercial_keywords)

        for contrato in entradas:
            nome_sol = contrato.get("nome_solucao") or ""
            if _is_comercial_solution(nome_sol):
                for parcela in contrato.get("parcelas", []):
                    val = parcela.get("valor_esperado") or 0
                    if val:
                        comercial_receita_sol[nome_sol.strip()] += float(val)

        for contrato in saidas:
            nome_sol = contrato.get("nome_solucao") or ""
            if _is_comercial_solution(nome_sol):
                for parcela in contrato.get("parcelas", []):
                    val = parcela.get("valor_esperado") or 0
                    if val:
                        comercial_custo_sol[nome_sol.strip()] += float(val)

        all_comercial_names = sorted(set(list(comercial_receita_sol.keys()) + list(comercial_custo_sol.keys())))
        solucoes_comercial = {
            "labels": all_comercial_names,
            "receita": [round(comercial_receita_sol.get(n, 0), 2) for n in all_comercial_names],
            "custo": [round(comercial_custo_sol.get(n, 0), 2) for n in all_comercial_names],
        }

        return {
            "ok": True,
            "receita_custo_mensal": receita_custo_mensal,
            "leads_pizza": leads_pizza,
            "data_analytics": data_analytics,
            "receita_cloud": receita_cloud,
            "solucoes_comercial": solucoes_comercial,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/crm/leads", response_model=List[CrmLead])
async def list_crm_leads(query: Optional[str] = Query(None, description="Filtro por título")):
    """Lista leads do ExternalCRM, opcionalmente filtrando por título."""
    if settings.PORTFOLIO_DEMO_MODE:
        return []
    try:
        repository = get_crm_repository()
        leads = await repository.list_leads(query)
        return leads
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar leads: {str(e)}")


@router.get("/api/crm/lead/{lead_id}", response_model=CrmLead)
async def get_crm_lead(lead_id: int):
    """Obtém um lead específico do ExternalCRM pelo ID."""
    if settings.PORTFOLIO_DEMO_MODE:
        raise HTTPException(status_code=404, detail="Lead demo nao encontrado")
    try:
        repository = get_crm_repository()
        lead = await repository.get_lead(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead não encontrado")
        return lead
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar lead: {str(e)}")


@router.get("/api/crm/cnpj-search", response_model=CnpjSearchResult)
async def search_cnpj(cnpj: str = Query(..., description="CNPJ para pesquisa")):
    """Busca empresa e leads associados pelo CNPJ no ExternalCRM."""
    if settings.PORTFOLIO_DEMO_MODE:
        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "").strip()
        return {"company": {"nome": "Empresa Demo", "cnpj": cnpj_limpo, "id_segmento": "Industria", "id_comercial": "Aline Torres"}, "leads": []}
    try:
        # Remove formatacao do CNPJ (pontos, barra, hifen)
        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "").strip()
        if len(cnpj_limpo) != 14 or not cnpj_limpo.isdigit():
            raise HTTPException(status_code=400, detail="CNPJ invalido. Deve conter 14 digitos.")

        repository = get_crm_repository()
        result = await repository.search_by_cnpj(cnpj_limpo)

        # Converte id_segmento para nome legivel
        if result.company and result.company.id_segmento:
            nome_segmento = mapper_b.id_to_name(result.company.id_segmento, "segmento")
            if nome_segmento:
                result.company.id_segmento = nome_segmento

        # Converte ids de colaboradores para nomes
        try:
            colab_repo = ColaboradoresRepositorySql()

            # Converte id_comercial da company
            if result.company and result.company.id_comercial:
                nome_comercial = colab_repo.get_nome_by_crm_id(result.company.id_comercial)
                if nome_comercial:
                    result.company.id_comercial = nome_comercial

            # Converte id_colab_comercial e id_colab_sdr de cada lead
            for lead in result.leads:
                if lead.id_colab_comercial:
                    nome = colab_repo.get_nome_by_crm_id(lead.id_colab_comercial)
                    if nome:
                        lead.id_colab_comercial = nome
                if lead.id_colab_sdr:
                    nome = colab_repo.get_nome_by_crm_id(lead.id_colab_sdr)
                    if nome:
                        lead.id_colab_sdr = nome
        except Exception:
            pass  # Mantem os ids originais se falhar

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao pesquisar CNPJ: {str(e)}")


@router.get("/api/comerciais")
async def list_comerciais():
    """Lista colaboradores ativos da area Comercial."""
    if settings.PORTFOLIO_DEMO_MODE:
        return {"comerciais": demo_list_comerciais()}
    try:
        colab_repo = ColaboradoresRepositorySql()
        comerciais = colab_repo.list_comerciais_ativos()
        return {"comerciais": [c.model_dump() for c in comerciais]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar comerciais: {str(e)}")


@router.post('/api/add')
async def create_lead(payload: LeadCreatePayload, auth_user=Depends(get_authenticated_user)):
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            nome_usuario = (
                auth_user.get("nome_completo")
                or auth_user.get("name")
                or auth_user.get("username")
                or ""
            ) if auth_user else ""
            result = demo_create_lead(payload.model_dump(), nome_usuario)
        else:
        # Representante Comercial: resolve id_col do colaborador logado pelo nome
            if auth_user:
                nome_usuario = (
                    auth_user.get("nome_completo")
                    or auth_user.get("name")
                    or auth_user.get("username")
                    or ""
                )
                if nome_usuario:
                    try:
                        colab_repo = ColaboradoresRepositorySql()
                        id_col = colab_repo.get_id_col_by_nome(nome_usuario)
                        if id_col is not None:
                            payload.id_colab_comercial = str(id_col)
                    except Exception:
                        pass

            add_service = AddLeadService()
            result = await add_service.processo_completo(payload)
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if result["updated"] == 0:
        raise HTTPException(status_code=404, detail="Lead nao encontrado")

    if result.get("status") == "parceiro_sem_solucao":
        raise HTTPException(status_code=400, detail="Selecione ao menos uma solucao para cadastrar o parceiro.")

    if result.get("status") == "lead_sem_solucao":
        raise HTTPException(status_code=400, detail="Selecione ao menos uma solucao para cadastrar o lead no kanban.")

    if result.get("status") == "lead_duplicado":
        raise HTTPException(status_code=409, detail="Lead ja cadastrado na solucao selecionada.")

    return {"ok": True, "result": result}


class MetaPayload(BaseModel):
    valor_meta: float = Field(gt=0)
    data_meta: str


@router.get("/api/meta")
async def get_meta(auth_user=Depends(get_authenticated_user)):
    return _load_meta()


@router.put("/api/meta")
async def update_meta(payload: MetaPayload, auth_user=Depends(get_authenticated_user)):
    data = {"valor_meta": payload.valor_meta, "data_meta": payload.data_meta}
    _save_meta(data)
    return {"ok": True, **data}
