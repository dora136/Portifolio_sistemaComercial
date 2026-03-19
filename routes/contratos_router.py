from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List

from config.config import settings
from demo_data import list_comerciais, list_contratos_financeiro, save_contrato_financeiro as demo_save_contrato_financeiro
from domain.models import ContratoFinanceiroModel, ParcelaFinanceiroModel
from utils.auth_utils import get_authenticated_user, check_admin

router = APIRouter(prefix="/portfolio", tags=["contratos"])

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


def _to_number(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    txt = str(value).strip().replace("R$", "").replace(" ", "")
    if not txt:
        return 0.0
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except Exception:
        return 0.0


@router.get("/contratos", response_class=HTMLResponse)
async def contratos_page(request: Request, auth_user=Depends(get_authenticated_user)):
    redirect = check_admin(auth_user)
    if redirect:
        return redirect
    user = _build_user(auth_user)

    entradas = []
    saidas = []
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            entradas = list_contratos_financeiro("entradas")
            saidas = list_contratos_financeiro("saidas")
            colab_cache = {c["id_col"]: c["nome"] for c in list_comerciais()}
            for contrato in entradas + saidas:
                rid = contrato.get("id_responsavel")
                contrato["responsavel_nome"] = colab_cache.get(rid) if rid else None
        else:
            from infrastructure.db.financeiro_repository import FinanceiroRepositorySql
            from infrastructure.db.colaboradores_repository import ColaboradoresRepositorySql
            fin_repo = FinanceiroRepositorySql()
            colab_repo = ColaboradoresRepositorySql()
            entradas = fin_repo.list_contratos_financeiro("entradas")
            saidas = fin_repo.list_contratos_financeiro("saidas")

            colab_cache = {}
            for contrato in entradas + saidas:
                rid = contrato.get("id_responsavel")
                if rid and rid not in colab_cache:
                    colab_cache[rid] = colab_repo.get_nome_by_id_col(rid)
                contrato["responsavel_nome"] = colab_cache.get(rid) if rid else None
    except Exception:
        pass

    todos_contratos = entradas + saidas
    for contrato in todos_contratos:
        campos = contrato.get("campos") or {}
        if isinstance(campos, dict):
            for key in ("receita", "custo", "coluna_fixa_1", "coluna_fixa_2"):
                if key in campos:
                    campos[key] = _to_number(campos.get(key))
        infos_json = contrato.get("infos_json") or {}
        info_campos = infos_json.get("campos") if isinstance(infos_json, dict) else None
        if isinstance(info_campos, dict):
            for key in ("receita", "custo", "coluna_fixa_1", "coluna_fixa_2"):
                if key in info_campos:
                    info_campos[key] = _to_number(info_campos.get(key))

    # KPIs
    total_contratos = len(todos_contratos)
    total_entradas = len(entradas)
    total_saidas = len(saidas)

    receita_total = 0
    custo_total = 0
    for c in entradas:
        receita_total += _to_number(c.get("campos", {}).get("receita", 0) or 0)
    for c in saidas:
        custo_total += _to_number(c.get("campos", {}).get("receita", 0) or 0)

    status_counts = {"Quitado": 0, "Em dia": 0, "Atrasado": 0, "Pendente": 0}
    solucoes_set = set()
    for c in todos_contratos:
        s = c.get("status", "")
        if s in status_counts:
            status_counts[s] += 1
        nome_sol = c.get("nome_solucao")
        if nome_sol:
            solucoes_set.add(nome_sol)

    solucoes_lista = sorted(solucoes_set)

    return templates.TemplateResponse("page_contratos.html", {
        "request": request,
        "user": user,
        "kpis": [],
        "portal_url": settings.PORTAL_URL or "#",
        "contratos": todos_contratos,
        "total_contratos": total_contratos,
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
        "receita_total": receita_total,
        "custo_total": custo_total,
        "status_counts": status_counts,
        "solucoes_lista": solucoes_lista,
    })


class ParcelaPayload(BaseModel):
    referencia_esperado: Optional[str] = None
    referencia_real: Optional[str] = None
    valor_esperado: Optional[float] = None
    valor_real: Optional[float] = None


class ContratoUpdatePayload(BaseModel):
    id_contrato: int
    id_comercial_lead: int
    id_solucao: int
    id_comercial_parceiro: int = 0
    id_responsavel: Optional[int] = None
    infos_json: dict = Field(default_factory=dict)
    parcelas: List[ParcelaPayload] = Field(default_factory=list)


@router.put("/api/contratos")
async def update_contrato(payload: ContratoUpdatePayload, auth_user=Depends(get_authenticated_user)):
    redirect = check_admin(auth_user)
    if redirect:
        raise HTTPException(status_code=403, detail="Sem permissão")

    model = ContratoFinanceiroModel(
        id_contrato=payload.id_contrato,
        id_comercial_lead=payload.id_comercial_lead,
        id_solucao=payload.id_solucao,
        id_comercial_parceiro=payload.id_comercial_parceiro,
        id_responsavel=payload.id_responsavel,
        infos_json=payload.infos_json,
        parcelas=[
            ParcelaFinanceiroModel(
                referencia_esperado=p.referencia_esperado,
                referencia_real=p.referencia_real,
                valor_esperado=p.valor_esperado,
                valor_real=p.valor_real,
            )
            for p in payload.parcelas
        ],
    )

    try:
        result = demo_save_contrato_financeiro(model.model_dump()) if settings.PORTFOLIO_DEMO_MODE else __import__("infrastructure.db.financeiro_repository", fromlist=["FinanceiroRepositorySql"]).FinanceiroRepositorySql().save_contrato_financeiro(model)
        return {"ok": True, **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
