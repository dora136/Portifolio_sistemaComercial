from typing import Optional, List, Literal

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError
from config.config import settings
from demo_data import STORE, get_solucoes_for_frontend
from utils.auth_utils import get_authenticated_user

router = APIRouter(prefix="/portfolio")

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

class KanbanEtapa(BaseModel):
    id: int
    nome_etapa: str
    color_HEX: str = "#626D84"
    ativo: Optional[int] = 1
    ordem_id: Optional[int] = None
    sucesso: Optional[int] = 0
    perdido: Optional[int] = 0

class RegistroField(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    type: Literal["number", "date", "string", "bool"]

class SolucaoUpdatePayload(BaseModel):
    tipo_solucao: Optional[str] = None
    descricao: Optional[str] = None
    icon_id: Optional[str] = None
    color_id: Optional[str] = None
    aplicacoes_basicas: List[str] = Field(default_factory=list)
    kanban_etapas: Optional[List[KanbanEtapa]] = None
    registro_info: Optional[List[RegistroField]] = None

class SolucaoCreatePayload(BaseModel):
    nome_solucao: str = Field(min_length=1, max_length=50)
    tipo_solucao: Optional[str] = None
    descricao: Optional[str] = None
    icon_id: str = "component"
    color_id: str = "#5D8AA8"
    aplicacoes_basicas: List[str] = Field(default_factory=list)
    kanban_etapas: Optional[List[KanbanEtapa]] = None
    registro_info: Optional[List[RegistroField]] = None


class SolucaoKanbanPayload(BaseModel):
    kanban_etapas: List[KanbanEtapa] = Field(default_factory=list)

def _build_user(auth_user):
    if auth_user:
        nome = auth_user.get("nome_completo", "Usuário")
        parts = nome.split()
        initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else nome[:2].upper()
        roles = auth_user.get("roles") or []
        role_label = roles[0] if roles else ""
        return {
            "id": auth_user.get("id"),
            "name": nome,
            "role": role_label,
            "roles": roles,
            "initials": initials
        }
    return {"id": None, "name": "Usuário", "role": "", "roles": [], "initials": "US"}


@router.get('/solucoes', response_class=HTMLResponse)
async def solucoes(request: Request, auth_user=Depends(get_authenticated_user)):
    kpis = []
    user = _build_user(auth_user)
    roles = user.get("roles", []) if user else []
    can_manage_solucoes = any(role in ("admin", "parceria_admin") for role in roles)

    if settings.PORTFOLIO_DEMO_MODE:
        solucoes = get_solucoes_for_frontend()
        return templates.TemplateResponse("page_solucoes.html", {
            "request": request,
            "user": user,
            "kpis": kpis,
            "solucoes": solucoes,
            "can_manage_solucoes": can_manage_solucoes,
            "portal_url": settings.PORTAL_URL or "#",
        })

    solucoes_models = []
    try:
        from infrastructure.db.solucoes_repository import SolucoesRepositorySql
        from infrastructure.db.leads_repository import LeadsRepositorySql
        repo = SolucoesRepositorySql()
        leads_repo = LeadsRepositorySql()
        solucoes_models = repo.list_solucoes()
    except (ValidationError, ValueError):
        solucoes_models = []
        leads_repo = None

    category_icon_map = {
        "tecnologia": "cloud",
        "consultoria": "briefcase",
        "segurança": "shield",
        "análise": "line-chart",
    }

    color_var_map = {
        "cloud": "cloud",
        "cyber": "cyber",
        "consulting": "consulting",
        "analytics": "analytics",
        "indicador": "indicador",
        "comercial": "comercial",
        "primary": "primary",
    }

    solucoes = []
    for model in solucoes_models:
        # Busca os nomes reais dos parceiros do banco de dados
        try:
            partners = repo.get_parceiros_by_solucao(model.id_solucao)
        except Exception:
            partners = []
        partners_count = len(partners) if partners else 0

        leads_list = []
        if leads_repo:
            try:
                leads_list = [lead.model_dump() for lead in leads_repo.get_leads_by_solucao(model.id_solucao)]
            except Exception:
                leads_list = []

        avg_ticket = "-"
        avg_implementation = "-"

        category_key = (model.tipo_solucao or "").strip().lower()
        icon = model.icon_id or category_icon_map.get(category_key, "layers")
        color_key_raw = (model.color_id or "").strip()
        if color_key_raw.startswith("#"):
            accent_var = color_key_raw
        else:
            color_key = color_key_raw.lower()
            accent_var = color_var_map.get(color_key, color_key or "primary")

        # Etapas do Kanban (usa padrao se nao definido)
        kanban_etapas = model.kanban_etapas
        if not kanban_etapas:
            kanban_etapas = [
                {"id": 1, "nome_etapa": "Triagem", "color_HEX": "#626D84", "ativo": 1, "ordem_id": 1, "sucesso": 0, "perdido": 0},
                {"id": 2, "nome_etapa": "Reunião", "color_HEX": "#2964D9", "ativo": 1, "ordem_id": 2, "sucesso": 0, "perdido": 0},
                {"id": 3, "nome_etapa": "Proposta", "color_HEX": "#F59F0A", "ativo": 1, "ordem_id": 3, "sucesso": 0, "perdido": 0},
                {"id": 4, "nome_etapa": "Fechamento", "color_HEX": "#16A249", "ativo": 1, "ordem_id": 4, "sucesso": 0, "perdido": 0},
            ]

        solucoes.append({
            "id": model.id_solucao,
            "name": model.nome_solucao,
            "category": model.tipo_solucao,
            "description": model.descricao,
            "applications": model.aplicacoes_basicas,
            "partnersCount": partners_count,
            "partners": partners,
            "leads": leads_list,
            "avgTicket": avg_ticket,
            "avgImplementation": avg_implementation,
            "icon": icon,
            "accentVar": accent_var,
            "kanbanEtapas": kanban_etapas,
            "registroInfo": model.registro_info,
        })

    return templates.TemplateResponse("page_solucoes.html", {
        "request": request,
        "user": user,
        "kpis": kpis,
        "solucoes": solucoes,
        "can_manage_solucoes": can_manage_solucoes,
        "portal_url": settings.PORTAL_URL or "#",
    })


@router.put('/solucoes/{solucao_id}')
async def update_solucao(solucao_id: int, payload: SolucaoUpdatePayload):
    if settings.PORTFOLIO_DEMO_MODE:
        for item in STORE.solucoes:
            if int(item["id"]) == int(solucao_id):
                if payload.tipo_solucao is not None:
                    item["tipo_solucao"] = payload.tipo_solucao
                    item["category"] = payload.tipo_solucao
                if payload.descricao is not None:
                    item["descricao"] = payload.descricao
                    item["description"] = payload.descricao
                if payload.icon_id is not None:
                    item["icon_id"] = payload.icon_id
                    item["icon"] = payload.icon_id
                if payload.color_id is not None:
                    item["color_id"] = payload.color_id
                    item["color"] = payload.color_id
                    item["accentVar"] = payload.color_id
                item["aplicacoes_basicas"] = payload.aplicacoes_basicas
                item["applications"] = payload.aplicacoes_basicas
                if payload.kanban_etapas is not None:
                    etapas = [e.model_dump() for e in payload.kanban_etapas]
                    item["kanban_etapas"] = etapas
                    item["kanbanEtapas"] = etapas
                if payload.registro_info is not None:
                    infos = [e.model_dump() for e in payload.registro_info]
                    item["registro_info"] = infos
                    item["registroInfo"] = infos
                return {"ok": True}
        raise HTTPException(status_code=404, detail="Solucao nao encontrada")
    try:
        from infrastructure.db.solucoes_repository import SolucoesRepositorySql
        repo = SolucoesRepositorySql()
        # Converte kanban_etapas para lista de dicts se existir
        kanban_etapas_list = None
        if payload.kanban_etapas is not None:
            kanban_etapas_list = [e.model_dump() for e in payload.kanban_etapas]
        registro_info_list = None
        if payload.registro_info is not None:
            registro_info_list = [e.model_dump() for e in payload.registro_info]
        updated = repo.update_solucao(
            solucao_id=solucao_id,
            tipo_solucao=payload.tipo_solucao,
            descricao=payload.descricao,
            icon_id=payload.icon_id,
            color_id=payload.color_id,
            aplicacoes_basicas=payload.aplicacoes_basicas,
            kanban_etapas=kanban_etapas_list,
            registro_info=registro_info_list,
        )
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if updated == 0:
        raise HTTPException(status_code=404, detail="Solucao nao encontrada")
    return {"ok": True}


@router.put('/solucoes/{solucao_id}/kanban')
async def update_solucao_kanban(solucao_id: int, payload: SolucaoKanbanPayload):
    if settings.PORTFOLIO_DEMO_MODE:
        for item in STORE.solucoes:
            if int(item["id"]) == int(solucao_id):
                etapas = [e.model_dump() for e in payload.kanban_etapas]
                item["kanban_etapas"] = etapas
                item["kanbanEtapas"] = etapas
                return {"ok": True}
        raise HTTPException(status_code=404, detail="Solucao nao encontrada")
    try:
        from infrastructure.db.solucoes_repository import SolucoesRepositorySql
        repo = SolucoesRepositorySql()
        kanban_etapas_list = [e.model_dump() for e in payload.kanban_etapas]
        updated = repo.update_solucao_kanban(
            solucao_id=solucao_id,
            kanban_etapas=kanban_etapas_list,
        )
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if updated == 0:
        raise HTTPException(status_code=404, detail="Solucao nao encontrada")
    return {"ok": True}


@router.post('/solucoes')
async def create_solucao(payload: SolucaoCreatePayload):
    if settings.PORTFOLIO_DEMO_MODE:
        new_id = max([int(item["id"]) for item in STORE.solucoes] + [0]) + 1
        etapas = [e.model_dump() for e in payload.kanban_etapas] if payload.kanban_etapas else []
        infos = [e.model_dump() for e in payload.registro_info] if payload.registro_info else []
        STORE.solucoes.append({
            "id": new_id,
            "id_solucao": new_id,
            "name": payload.nome_solucao,
            "nome_solucao": payload.nome_solucao,
            "category": payload.tipo_solucao,
            "tipo_solucao": payload.tipo_solucao,
            "description": payload.descricao,
            "descricao": payload.descricao,
            "applications": payload.aplicacoes_basicas,
            "aplicacoes_basicas": payload.aplicacoes_basicas,
            "partnersCount": 0,
            "n_parceiros": 0,
            "icon": payload.icon_id,
            "icon_id": payload.icon_id,
            "color": payload.color_id,
            "color_id": payload.color_id,
            "accentVar": payload.color_id,
            "avgTicket": 0,
            "avgImplementation": "-",
            "kanbanEtapas": etapas,
            "kanban_etapas": etapas,
            "registroInfo": infos,
            "registro_info": infos,
        })
        return {"ok": True, "id": new_id}
    try:
        from infrastructure.db.solucoes_repository import SolucoesRepositorySql
        repo = SolucoesRepositorySql()
        # Converte kanban_etapas para lista de dicts se existir
        kanban_etapas_list = None
        if payload.kanban_etapas is not None:
            kanban_etapas_list = [e.model_dump() for e in payload.kanban_etapas]
        registro_info_list = None
        if payload.registro_info is not None and len(payload.registro_info) > 0:
            registro_info_list = [e.model_dump() for e in payload.registro_info]
        if not registro_info_list:
            registro_info_list = [
                {"name": "Data Recebimento", "type": "date", "value": None},
                {"name": "Data Agendamento Reunião", "type": "date", "value": None},
                {"name": "Data Primeira Reunião", "type": "date", "value": None},
            ]
        new_id = repo.create_solucao(
            nome_solucao=payload.nome_solucao,
            tipo_solucao=payload.tipo_solucao,
            descricao=payload.descricao,
            aplicacoes_basicas=payload.aplicacoes_basicas,
            icon_id=payload.icon_id,
            color_id=payload.color_id,
            kanban_etapas=kanban_etapas_list,
            registro_info=registro_info_list,
        )
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if new_id == 0:
        raise HTTPException(status_code=500, detail="Falha ao inserir solucao")
    return {"ok": True, "id": new_id}


@router.delete('/solucoes/{solucao_id}')
async def delete_solucao(solucao_id: int):
    if settings.PORTFOLIO_DEMO_MODE:
        before = len(STORE.solucoes)
        STORE.solucoes = [item for item in STORE.solucoes if int(item["id"]) != int(solucao_id)]
        if len(STORE.solucoes) == before:
            raise HTTPException(status_code=404, detail="Solucao nao encontrada")
        return {"ok": True}
    try:
        from infrastructure.db.solucoes_repository import SolucoesRepositorySql
        repo = SolucoesRepositorySql()
        if repo.has_active_parceiros(solucao_id):
            raise HTTPException(status_code=409, detail="Solucao possui parceiros ativos")
        deleted = repo.delete_solucao(solucao_id)
    except HTTPException:
        raise
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Solucao nao encontrada")
    return {"ok": True}
