from typing import Optional, List, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel, Field

from config.config import settings
from demo_data import (
    delete_lead as demo_delete_lead,
    get_contrato_financeiro as demo_get_contrato_financeiro,
    get_solucoes_for_frontend,
    list_comerciais as demo_list_comerciais,
    list_contratos_financeiro,
    list_leads,
    list_leads_by_comercial,
    list_leads_by_parceiro,
    save_contrato_financeiro as demo_save_contrato_financeiro,
    update_lead as demo_update_lead,
)
from utils.auth_utils import get_authenticated_user

router = APIRouter(prefix="/portfolio")

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _sort_solucoes_gd_first(solucoes: list[dict]) -> list[dict]:
    def _is_primary(name: str) -> bool:
        normalized = name.lower().strip()
        return normalized in {"cloud", "cloud computing"} or "cloud computing" in normalized

    def sort_key(item: dict):
        name = str(item.get("name") or "").strip().lower()
        is_primary = 0 if _is_primary(name) else 1
        return (is_primary, name)

    return sorted(solucoes or [], key=sort_key)


class SolucaoUpdatePayload(BaseModel):
    tipo_solucao: Optional[str] = None
    descricao: Optional[str] = None
    aplicacoes_basicas: List[str] = Field(default_factory=list)


class LeadSolucaoUpdate(BaseModel):
    id_solucao: int
    id_etapa_kanban: int = 1
    id_comercial_parceiro: Optional[int] = None
    informacoes: List[dict] = Field(default_factory=list)


class LeadUpdatePayload(BaseModel):
    id_comercial: int
    id_colab_comercial: Optional[str] = None
    solucoes: List[LeadSolucaoUpdate]


class ParcelaContratoPayload(BaseModel):
    referencia_esperado: Optional[str] = None
    referencia_real: Optional[str] = None
    valor_esperado: Optional[float] = None
    valor_real: Optional[float] = None


class ContratoFinanceiroPayload(BaseModel):
    id_contrato: Optional[int] = None
    id_comercial_lead: int
    id_solucao: int
    id_comercial_parceiro: int
    id_responsavel: Optional[int] = None
    status: Optional[str] = None
    num_parcelas: Optional[int] = None
    infos_json: dict[str, Any] = Field(default_factory=dict)
    parcelas: List[ParcelaContratoPayload] = Field(default_factory=list)


def _build_user(auth_user):
    if auth_user:
        nome = (
            auth_user.get("nome_completo")
            or auth_user.get("name")
            or auth_user.get("username")
            or auth_user.get("email")
            or "Usuário"
        )
        parts = nome.split()
        initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else nome[:2].upper()

        # Resolve id_col do colaborador na tabela dadm_colaboradores pelo nome
        id_col = None
        if settings.PORTFOLIO_DEMO_MODE:
            id_col = next((c["id_col"] for c in demo_list_comerciais() if c["nome"] == nome), None)
        else:
            try:
                from infrastructure.db.colaboradores_repository import ColaboradoresRepositorySql
                colab_repo = ColaboradoresRepositorySql()
                id_col = colab_repo.get_id_col_by_nome(nome)
            except Exception:
                pass

        return {
            "id": auth_user.get("id"),
            "id_col": id_col,
            "name": nome,
            "nome_completo": auth_user.get("nome_completo"),
            "username": auth_user.get("username"),
            "email": auth_user.get("email"),
            "role": auth_user.get("roles", [""])[0] if auth_user.get("roles") else "",
            "roles": auth_user.get("roles") or [],
            "initials": initials,
        }
    return {"id": None, "id_col": None, "name": "Usuário", "role": "", "roles": [], "initials": "US"}


@router.get('/leads', response_class=HTMLResponse)
async def leads(request: Request, auth_user=Depends(get_authenticated_user)):
    kpis = []
    leads = []
    user = _build_user(auth_user)

    # Busca solucoes ativas do banco de dados
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            solucoes = get_solucoes_for_frontend()
        else:
            from infrastructure.db.solucoes_repository import SolucoesRepositorySql
            repo = SolucoesRepositorySql()
            solucoes = [sol.model_dump() for sol in repo.list_solucoes_ativas()]
        solucoes = _sort_solucoes_gd_first(solucoes)
    except Exception:
        solucoes = []

    # Busca leads reais do Comercial
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            leads = list_leads()
        else:
            from infrastructure.db.leads_repository import LeadsRepositorySql
            leads_repo = LeadsRepositorySql()
            leads = [lead.model_dump() for lead in leads_repo.list_comercial_leads()]
    except Exception:
        pass

    # Calcular valor esperado (receita) por lead a partir dos contratos financeiros
    try:
        entradas = list_contratos_financeiro("entradas") if settings.PORTFOLIO_DEMO_MODE else __import__("infrastructure.db.financeiro_repository", fromlist=["FinanceiroRepositorySql"]).FinanceiroRepositorySql().list_contratos_financeiro("entradas")
        # Mapear (id_comercial_lead, id_solucao) → soma valor_esperado
        valor_por_lead = {}
        for contrato in entradas:
            key = (contrato.get("id_comercial_lead", 0), contrato.get("id_solucao", 0))
            for parcela in contrato.get("parcelas", []):
                val = parcela.get("valor_esperado") or 0
                valor_por_lead[key] = valor_por_lead.get(key, 0) + float(val)
        # Injetar value em cada lead
        for lead in leads:
            key = (lead.get("id_comercial", 0), lead.get("id_solucao", 0))
            lead["value"] = valor_por_lead.get(key, 0)
    except Exception:
        pass

    return templates.TemplateResponse("page_leads.html", {
        "request": request,
        "user": user,
        "kpis": kpis,
        "leads": leads,
        "solucoes": solucoes,
        "portal_url": settings.PORTAL_URL or "#",
    })


@router.put('/api/leads')
async def update_lead(payload: LeadUpdatePayload):
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            total_updated = demo_update_lead(payload.model_dump())
        else:
            from infrastructure.db.leads_repository import LeadsRepositorySql
            leads_repo = LeadsRepositorySql()
            total_updated = 0
            for sol in payload.solucoes:
                updated = leads_repo.update_comercial_lead(
                    id_comercial=payload.id_comercial,
                    id_solucao=sol.id_solucao,
                    id_etapa_kanban=sol.id_etapa_kanban,
                    id_comercial_parceiro=sol.id_comercial_parceiro,
                    informacoes=sol.informacoes,
                    id_colab_comercial=payload.id_colab_comercial,
                )
                total_updated += updated
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"ok": True, "updated": total_updated}


@router.delete('/api/leads/{id_comercial}/{id_solucao}')
async def delete_lead(id_comercial: int, id_solucao: int):
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            deleted = demo_delete_lead(id_comercial, id_solucao)
        else:
            from infrastructure.db.leads_repository import LeadsRepositorySql
            leads_repo = LeadsRepositorySql()
            deleted = leads_repo.delete_comercial_lead(
                id_comercial=id_comercial,
                id_solucao=id_solucao,
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    return {"ok": True, "deleted": deleted}


@router.get('/api/leads/parceiro/{parceiro_id}')
async def get_leads_by_parceiro(parceiro_id: int):
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            leads = list_leads_by_parceiro(parceiro_id)
            solucoes = get_solucoes_for_frontend()
        else:
            from infrastructure.db.leads_repository import LeadsRepositorySql
            from infrastructure.db.solucoes_repository import SolucoesRepositorySql
            leads_repo = LeadsRepositorySql()
            solucoes_repo = SolucoesRepositorySql()
            leads = [lead.model_dump() for lead in leads_repo.list_comercial_leads_by_parceiro(parceiro_id)]
            solucoes = [sol.model_dump() for sol in solucoes_repo.list_solucoes_ativas()]
        solucoes = _sort_solucoes_gd_first(solucoes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"leads": leads, "solucoes": solucoes}


@router.get('/api/leads/comercial/{comercial_id}')
async def get_leads_by_comercial(comercial_id: int):
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            leads = list_leads_by_comercial(comercial_id)
            solucoes = get_solucoes_for_frontend()
        else:
            from infrastructure.db.leads_repository import LeadsRepositorySql
            from infrastructure.db.solucoes_repository import SolucoesRepositorySql
            leads_repo = LeadsRepositorySql()
            solucoes_repo = SolucoesRepositorySql()
            leads = [lead.model_dump() for lead in leads_repo.list_comercial_leads_by_comercial(comercial_id)]
            solucoes = [sol.model_dump() for sol in solucoes_repo.list_solucoes_ativas()]
        solucoes = _sort_solucoes_gd_first(solucoes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"leads": leads, "solucoes": solucoes}


@router.get('/api/contratos-financeiro')
async def get_contrato_financeiro(
    id_comercial_lead: int,
    id_solucao: int,
    id_comercial_parceiro: int,
):
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            contrato = demo_get_contrato_financeiro(id_comercial_lead, id_solucao, id_comercial_parceiro)
        else:
            from infrastructure.db.financeiro_repository import FinanceiroRepositorySql
            repo = FinanceiroRepositorySql()
            contrato = repo.get_contrato_financeiro(
                id_comercial_lead=id_comercial_lead,
                id_solucao=id_solucao,
                id_comercial_parceiro=id_comercial_parceiro,
            )
        return {"ok": True, "exists": contrato is not None, "contrato": contrato}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/api/contratos-financeiro')
async def save_contrato_financeiro(payload: ContratoFinanceiroPayload):
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            result = demo_save_contrato_financeiro(payload.model_dump())
        else:
            from domain.models import ContratoFinanceiroModel, ParcelaFinanceiroModel
            from infrastructure.db.financeiro_repository import FinanceiroRepositorySql

            contrato = ContratoFinanceiroModel(
                id_contrato=payload.id_contrato,
                id_comercial_lead=payload.id_comercial_lead,
                id_solucao=payload.id_solucao,
                id_comercial_parceiro=payload.id_comercial_parceiro,
                id_responsavel=payload.id_responsavel,
                status=payload.status,
                num_parcelas=payload.num_parcelas,
                infos_json=payload.infos_json or {},
                parcelas=[
                    ParcelaFinanceiroModel(
                        referencia_esperado=parcela.referencia_esperado,
                        referencia_real=parcela.referencia_real,
                        valor_esperado=parcela.valor_esperado,
                        valor_real=parcela.valor_real,
                    )
                    for parcela in payload.parcelas
                ],
            )

            repo = FinanceiroRepositorySql()
            result = repo.save_contrato_financeiro(contrato)
        return {"ok": True, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
