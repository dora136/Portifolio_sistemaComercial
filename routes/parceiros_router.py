from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError
from config.config import settings
from demo_data import (
    activate_indicacao as demo_activate_indicacao,
    activate_comercial as demo_activate_comercial,
    delete_parceiro as demo_delete_parceiro,
    get_solucoes_for_frontend,
    list_contratos_financeiro,
    list_parceiros as demo_list_parceiros,
    list_parceiros_kanban as demo_list_parceiros_kanban,
    parceiro_has_leads,
    update_parceiro as demo_update_parceiro,
    update_parceiro_kanban_status as demo_update_parceiro_kanban_status,
    update_parceiro_responsaveis as demo_update_parceiro_responsaveis,
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


class ComercialActivatePayload(BaseModel):
    solution_ids: list[int] = Field(min_length=1)


class ParceiroKanbanStatusPayload(BaseModel):
    id_comercial: int
    id_solucao: int
    id_status_kanban: int


class ParceiroResponsaveisPayload(BaseModel):
    id_comercial: int
    id_colab_comercial: Optional[int] = None


class ParceiroUpdatePayload(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None


def get_partner_status(modulo_comercial: Optional[bool], modulo_indicacao: Optional[bool], status_comercial: Optional[str], status_indicacao: Optional[str]) -> str:
    status_values = {(status_comercial or "").strip().lower(), (status_indicacao or "").strip().lower()}
    if {"bloqueado", "blocked", "inativo"} & status_values:
        return "blocked"
    if modulo_comercial or modulo_indicacao:
        return "active"
    return "pending"


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
        return {
            "id": auth_user.get("id"),
            "name": nome,
            "role": auth_user.get("roles", [""])[0] if auth_user.get("roles") else "",
            "roles": auth_user.get("roles") or [],
            "initials": initials,
        }
    return {"id": None, "name": "Usuário", "role": "", "roles": [], "initials": "US"}


@router.get('/parceiros', response_class=HTMLResponse)
async def parceiros(request: Request, auth_user=Depends(get_authenticated_user)):
    kpis = []
    user = _build_user(auth_user)

    if settings.PORTFOLIO_DEMO_MODE:
        partners = demo_list_parceiros()
    else:
        try:
            from infrastructure.db.parceiros_repository import ParceirosRepositorySql
            repo = ParceirosRepositorySql()
            parceiros_models = repo.list_parceiros()
        except (ValidationError, ValueError, Exception):
            parceiros_models = []

        partners = []
        for model in parceiros_models:
            modules = []
            if model.modulo_comercial:
                modules.append("comercial")
            if model.modulo_indicacao:
                modules.append("indicador")

            comercial_solutions = []
            if model.modulo_comercial:
                try:
                    comercial_solutions = [sol.model_dump() for sol in repo.get_comercial_solutions(model.id)]
                except Exception:
                    comercial_solutions = []

            partners.append({
                "id": str(model.id),
                "name": model.nome,
                "cnpj": model.cnpj or "",
                "razaoSocial": model.razao_social or "",
                "state": model.estado or "",
                "createdAt": model.data_criacao or "",
                "modules": modules,
                "status": get_partner_status(model.modulo_comercial, model.modulo_indicacao, model.status_comercial, model.status_indicacao),
                "folPath": model.fol_path or "",
                "comercialSolutions": comercial_solutions,
                "indicadorData": (repo.get_indicacao_stats(model.id).model_dump()
                                  if model.modulo_indicacao else None),
            })

    return templates.TemplateResponse("page_parceiros.html", {
        "request": request,
        "user": user,
        "kpis": kpis,
        "partners": partners,
        "portal_url": settings.PORTAL_URL or "#",
    })


@router.get('/parceiros/acompanhamento', response_class=HTMLResponse)
async def parceiros_acompanhamento(request: Request, auth_user=Depends(get_authenticated_user)):
    kpis = []
    user = _build_user(auth_user)

    parceiros_kanban = []
    solucoes = []
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            parceiros_kanban = demo_list_parceiros_kanban()
            solucoes = get_solucoes_for_frontend()
        else:
            from infrastructure.db.parceiros_repository import ParceirosRepositorySql
            from infrastructure.db.solucoes_repository import SolucoesRepositorySql
            parceiros_repo = ParceirosRepositorySql()
            solucoes_repo = SolucoesRepositorySql()
            parceiros_kanban = parceiros_repo.list_parceiros_kanban()
            solucoes = [sol.model_dump() for sol in solucoes_repo.list_solucoes_ativas()]
        solucoes = _sort_solucoes_gd_first(solucoes)
    except (ValidationError, ValueError, Exception):
        parceiros_kanban = []
        solucoes = []

    # Calcular valor esperado por parceiro a partir dos contratos financeiros
    try:
        entradas = list_contratos_financeiro("entradas") if settings.PORTFOLIO_DEMO_MODE else __import__("infrastructure.db.financeiro_repository", fromlist=["FinanceiroRepositorySql"]).FinanceiroRepositorySql().list_contratos_financeiro("entradas")
        valor_por_parceiro = {}
        for contrato in entradas:
            key = (contrato.get("id_comercial_lead", 0), contrato.get("id_solucao", 0))
            for parcela in contrato.get("parcelas", []):
                val = parcela.get("valor_esperado") or 0
                valor_por_parceiro[key] = valor_por_parceiro.get(key, 0) + float(val)
        for p in parceiros_kanban:
            key = (p.get("id_comercial", 0), p.get("id_solucao", 0))
            p["value"] = valor_por_parceiro.get(key, 0)
    except Exception:
        pass

    return templates.TemplateResponse("page_parceiros_acompanhamento.html", {
        "request": request,
        "user": user,
        "kpis": kpis,
        "parceiros_kanban": parceiros_kanban,
        "solucoes": solucoes,
        "portal_url": settings.PORTAL_URL or "#",
    })


@router.get('/api/parceiros')
async def list_parceiros():
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            payload = [
                {"id": int(p["id"]), "nome": p["name"], "cnpj": p["cnpj"], "razao_social": p["razaoSocial"]}
                for p in demo_list_parceiros()
            ]
        else:
            from infrastructure.db.parceiros_repository import ParceirosRepositorySql
            repo = ParceirosRepositorySql()
            parceiros = repo.list_parceiros()
            payload = [
                {
                    "id": p.id,
                    "nome": p.nome,
                    "cnpj": p.cnpj,
                    "razao_social": p.razao_social,
                }
                for p in parceiros
            ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"ok": True, "parceiros": payload}


@router.put('/api/parceiros/kanban-status')
async def update_parceiro_kanban_status(payload: ParceiroKanbanStatusPayload):
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            updated = demo_update_parceiro_kanban_status(payload.id_comercial, payload.id_solucao, payload.id_status_kanban)
        else:
            from infrastructure.db.parceiros_repository import ParceirosRepositorySql
            repo = ParceirosRepositorySql()
            updated = repo.update_parceiro_kanban_status(
                id_comercial=payload.id_comercial,
                id_solucao=payload.id_solucao,
                id_status_kanban=payload.id_status_kanban,
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if updated == 0:
        raise HTTPException(status_code=404, detail="Parceiro/solucao nao encontrado")
    return {"ok": True, "updated": updated}


@router.put('/api/parceiros/responsaveis')
async def update_parceiro_responsaveis(payload: ParceiroResponsaveisPayload):
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            result = demo_update_parceiro_responsaveis(payload.id_comercial, payload.id_colab_comercial)
        else:
            from infrastructure.db.parceiros_repository import ParceirosRepositorySql
            repo = ParceirosRepositorySql()
            result = repo.update_parceiro_responsaveis(
                id_comercial=payload.id_comercial,
                id_colab_comercial=payload.id_colab_comercial,
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"ok": True, "result": result}


@router.post('/parceiros/{parceiro_id}/indicacao/ativar')
async def ativar_indicacao(parceiro_id: int):
    try:
        result = demo_activate_indicacao(parceiro_id) if settings.PORTFOLIO_DEMO_MODE else __import__("infrastructure.db.parceiros_repository", fromlist=["ParceirosRepositorySql"]).ParceirosRepositorySql().activate_indicacao(parceiro_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True, "result": result}


@router.get('/parceiros/solucoes-ativas')
async def solucoes_ativas():
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            solucoes = get_solucoes_for_frontend()
        else:
            from infrastructure.db.solucoes_repository import SolucoesRepositorySql
            repo = SolucoesRepositorySql()
            solucoes = [sol.model_dump() for sol in repo.list_solucoes_ativas()]
        solucoes = _sort_solucoes_gd_first(solucoes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True, "solucoes": solucoes}


@router.post('/parceiros/{parceiro_id}/solucoes/ativar')
async def ativar_comercial(parceiro_id: int, payload: ComercialActivatePayload):
    try:
        result = demo_activate_comercial(parceiro_id, payload.solution_ids) if settings.PORTFOLIO_DEMO_MODE else __import__("infrastructure.db.parceiros_repository", fromlist=["ParceirosRepositorySql"]).ParceirosRepositorySql().activate_comercial(parceiro_id, payload.solution_ids)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True, "result": result}


@router.put('/api/parceiros/{parceiro_id}')
async def update_parceiro(parceiro_id: int, payload: ParceiroUpdatePayload):
    try:
        updated = demo_update_parceiro(parceiro_id, payload.nome, payload.cnpj, payload.razao_social) if settings.PORTFOLIO_DEMO_MODE else __import__("infrastructure.db.parceiros_repository", fromlist=["ParceirosRepositorySql"]).ParceirosRepositorySql().update_parceiro(
            id_comercial=parceiro_id,
            nome=payload.nome,
            cnpj=payload.cnpj,
            razao_social=payload.razao_social,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if updated == 0:
        raise HTTPException(status_code=404, detail="Parceiro nao encontrado")
    return {"ok": True, "updated": updated}


@router.delete('/api/parceiros/{parceiro_id}')
async def delete_parceiro(parceiro_id: int):
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            if parceiro_has_leads(parceiro_id):
                raise HTTPException(
                    status_code=409,
                    detail="Parceiro possui leads vinculados e nao pode ser excluido.",
                )
            deleted = demo_delete_parceiro(parceiro_id)
        else:
            from infrastructure.db.parceiros_repository import ParceirosRepositorySql
            repo = ParceirosRepositorySql()
            if repo.has_leads(parceiro_id):
                raise HTTPException(
                    status_code=409,
                    detail="Parceiro possui leads vinculados e nao pode ser excluido.",
                )
            deleted = repo.delete_parceiro(parceiro_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Parceiro nao encontrado")
    return {"ok": True, "deleted": deleted}
