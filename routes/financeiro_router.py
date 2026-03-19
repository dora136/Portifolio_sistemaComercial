from pathlib import Path
from collections import defaultdict
import unicodedata
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from config.config import settings
from demo_data import get_solucoes, list_contratos_financeiro, list_leads, update_parcela_status as demo_update_parcela_status
from utils.auth_utils import get_authenticated_user, check_admin

router = APIRouter(prefix="/portfolio", tags=["financeiro"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class UpdateParcelaStatusPayload(BaseModel):
    id_contrato: int
    id_financeiro: int
    status_parcela: int
    referencia_esperado: Optional[str] = None
    referencia_real: Optional[str] = None
    valor_esperado: Optional[float] = None
    valor_real: Optional[float] = None


def _build_user(auth_user):
    if auth_user:
        nome = auth_user.get("nome_completo", "Usuario")
        parts = nome.split()
        initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else nome[:2].upper()
        return {
            "id": auth_user.get("id"),
            "name": nome,
            "role": auth_user.get("roles", [""])[0] if auth_user.get("roles") else "",
            "roles": auth_user.get("roles") or [],
            "initials": initials,
        }
    return {"id": None, "name": "Usuario", "role": "", "roles": [], "initials": "US"}


def _render_financeiro_page(request: Request, user: dict, page_id: str, iframe_hash: str):
    iframe_src = f"/portfolio/static/financeiro/index.html?v=20260302-04{iframe_hash}"
    return templates.TemplateResponse(
        "page_financeiro.html",
        {
            "request": request,
            "user": user,
            "kpis": [],
            "portal_url": settings.PORTAL_URL or "#",
            "finance_page_id": page_id,
            "finance_iframe_src": iframe_src,
        },
    )


def _render_financeiro_dashboard_page(request: Request, user: dict):
    return templates.TemplateResponse(
        "page_financeiro_dashboard.html",
        {
            "request": request,
            "user": user,
            "kpis": [],
            "portal_url": settings.PORTAL_URL or "#",
        },
    )


def _norm_text(value: str) -> str:
    raw = (value or "").strip().lower()
    return "".join(ch for ch in unicodedata.normalize("NFD", raw) if unicodedata.category(ch) != "Mn")


def _month_key(value: str):
    raw = (value or "").strip()
    if len(raw) < 7:
        return None
    key = raw[:7]
    if len(key) == 7 and key[4] == "-" and key[:4].isdigit() and key[5:7].isdigit():
        return key
    return None


def _to_number(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    txt = str(value).strip()
    if not txt:
        return 0.0
    txt = txt.replace("R$", "").replace(" ", "")
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except Exception:
        return 0.0


def _extract_receita_custo(contrato: dict) -> tuple[float, float]:
    campos = contrato.get("campos") if isinstance(contrato.get("campos"), dict) else {}
    receita = 0.0
    for parcela in contrato.get("parcelas", []) or []:
        valor_esperado = parcela.get("valor_esperado")
        valor_real = parcela.get("valor_real")
        if valor_esperado is None or str(valor_esperado).strip() == "":
            receita += _to_number(valor_real)
        else:
            receita += _to_number(valor_esperado)
    custo = _to_number(campos.get("custo"))
    if not custo:
        custo = _to_number(campos.get("coluna_fixa_2"))
    return receita, custo


def _contract_month_key(contrato: dict):
    for parcela in contrato.get("parcelas", []) or []:
        key = _month_key(parcela.get("referencia_esperado"))
        if key:
            return key
    return None


def _match_comercial_bucket(solucao_nome: str):
    name = _norm_text(solucao_nome)
    if "cloud" in name:
        return "Cloud Computing"
    if "cyber" in name:
        return "Cybersecurity"
    if "analytics" in name or "analise" in name:
        return "Data Analytics"
    if "consulting" in name or "consultoria" in name:
        return "Consulting"
    if "sistema comercial" in name:
        return "Sistema Comercial"
    return None


def _aggregate_monthly(contracts):
    monthly = defaultdict(float)
    for contrato in contracts:
        for parcela in contrato.get("parcelas", []) or []:
            key = _month_key(parcela.get("referencia_esperado"))
            if not key:
                continue
            value = _to_number(parcela.get("valor_esperado"))
            if value:
                monthly[key] += value
    return monthly


@router.get("/financeiro/dashboard-data")
async def financeiro_dashboard_data(auth_user=Depends(get_authenticated_user)):
    if not auth_user:
        raise HTTPException(status_code=401, detail="Usuario nao autenticado.")
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            entradas = list_contratos_financeiro("entradas")
            saidas = list_contratos_financeiro("saidas")
            solucoes = get_solucoes()
            leads = list_leads()
        else:
            from infrastructure.db.financeiro_repository import FinanceiroRepositorySql
            from infrastructure.db.leads_repository import LeadsRepositorySql
            from infrastructure.db.solucoes_repository import SolucoesRepositorySql

            fin_repo = FinanceiroRepositorySql()
            leads_repo = LeadsRepositorySql()
            solucoes_repo = SolucoesRepositorySql()

            entradas = fin_repo.list_contratos_financeiro("entradas")
            saidas = fin_repo.list_contratos_financeiro("saidas")
            solucoes = solucoes_repo.list_solucoes()
            leads = leads_repo.list_comercial_leads()
        contratos = entradas + saidas

        receita_month = _aggregate_monthly(contratos)
        custo_month = defaultdict(float)
        for contrato in contratos:
            month = _contract_month_key(contrato)
            if not month:
                continue
            _, custo_val = _extract_receita_custo(contrato)
            custo_month[month] += custo_val
        all_months = sorted(set(receita_month.keys()) | set(custo_month.keys()))

        # Leads por soluÃ§Ã£o (pizza)
        solution_name_by_id = {
            (s["id_solucao"] if isinstance(s, dict) else s.id_solucao): (s["nome_solucao"] if isinstance(s, dict) else s.nome_solucao)
            for s in solucoes
        }
        leads_counter = defaultdict(int)
        for lead in leads:
            sid = lead["id_solucao"] if isinstance(lead, dict) else lead.id_solucao
            solution_name = solution_name_by_id.get(sid, f"SoluÃ§Ã£o {sid}")
            leads_counter[solution_name] += 1

        # Data Analytics
        ml_contracts = [
            contrato for contrato in contratos
            if "data analytics" in _norm_text(contrato.get("nome_solucao") or "")
        ]
        ml_receita_month = _aggregate_monthly(ml_contracts)
        ml_custo_month = defaultdict(float)
        for contrato in ml_contracts:
            key = _contract_month_key(contrato)
            if not key:
                continue
            _, custo_val = _extract_receita_custo(contrato)
            ml_custo_month[key] += custo_val
        ml_months = sorted(set(ml_receita_month.keys()) | set(ml_custo_month.keys()))

        # Receita Cloud Computing
        gd_contracts = []
        for contrato in contratos:
            solution = _norm_text(contrato.get("nome_solucao") or "")
            if not (solution == "cloud" or "cloud computing" in solution):
                continue
            gd_contracts.append(contrato)
        gd_receita_month = _aggregate_monthly(gd_contracts)
        gd_months = sorted(gd_receita_month.keys())

        # SoluÃ§Ãµes Comercial (somente as pedidas)
        comercial_receita = defaultdict(float)
        comercial_custo = defaultdict(float)
        for contrato in contratos:
            bucket = _match_comercial_bucket(contrato.get("nome_solucao") or contrato.get("modelo_contrato") or "")
            if not bucket:
                continue
            receita_val, custo_val = _extract_receita_custo(contrato)
            comercial_receita[bucket] += receita_val
            comercial_custo[bucket] += custo_val
        comercial_labels = sorted(set(comercial_receita.keys()) | set(comercial_custo.keys()))

        # KPIs
        total_receita = round(sum(_extract_receita_custo(c)[0] for c in contratos), 2)
        total_custo = round(sum(_extract_receita_custo(c)[1] for c in contratos), 2)
        parceiros_ativos = len(
            {
                (c.get("parceiro_nome") or "").strip()
                for c in contratos
                if (c.get("parceiro_nome") or "").strip()
            }
        )
        contratos_pendentes = sum(
            1
            for c in contratos
            if _norm_text(c.get("status") or "") == "pendente"
        )

        return {
            "ok": True,
            "kpis": {
                "receita_total": total_receita,
                "custo_total": total_custo,
                "parceiros_ativos": parceiros_ativos,
                "contratos_pendentes": contratos_pendentes,
            },
            "receita_custo_mensal": {
                "labels": all_months,
                "receita": [round(receita_month.get(m, 0), 2) for m in all_months],
                "custo": [round(custo_month.get(m, 0), 2) for m in all_months],
            },
            "leads_pizza": {
                "labels": list(leads_counter.keys()),
                "data": list(leads_counter.values()),
            },
            "data_analytics": {
                "labels": ml_months,
                "receita": [round(ml_receita_month.get(m, 0), 2) for m in ml_months],
                "custo": [round(ml_custo_month.get(m, 0), 2) for m in ml_months],
            },
            "receita_cloud": {
                "labels": gd_months,
                "receita": [round(gd_receita_month.get(m, 0), 2) for m in gd_months],
            },
            "solucoes_comercial": {
                "labels": comercial_labels,
                "receita": [round(comercial_receita.get(n, 0), 2) for n in comercial_labels],
                "custo": [round(comercial_custo.get(n, 0), 2) for n in comercial_labels],
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/financeiro/pagamentos", response_class=HTMLResponse)
async def financeiro_pagamentos(request: Request, auth_user=Depends(get_authenticated_user)):
    redirect = check_admin(auth_user)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        "page_pagamentos.html",
        {
            "request": request,
            "user": _build_user(auth_user),
            "kpis": [],
            "portal_url": settings.PORTAL_URL or "#",
        },
    )


@router.get("/financeiro/pagamentos-data")
async def financeiro_pagamentos_data(auth_user=Depends(get_authenticated_user)):
    """Retorna parcelas agrupadas por mes/ano com resumos."""
    if not auth_user:
        raise HTTPException(status_code=401, detail="Usuario nao autenticado.")
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            entradas = list_contratos_financeiro("entradas")
            saidas = list_contratos_financeiro("saidas")
        else:
            from infrastructure.db.financeiro_repository import FinanceiroRepositorySql
            fin_repo = FinanceiroRepositorySql()
            entradas = fin_repo.list_contratos_financeiro("entradas")
            saidas = fin_repo.list_contratos_financeiro("saidas")

        # Agrupa parcelas por mes
        meses: dict[str, dict] = {}

        def _process_contracts(contratos, tipo):
            for contrato in contratos:
                for parcela in contrato.get("parcelas", []) or []:
                    ref = parcela.get("referencia_esperado") or ""
                    if len(ref) < 7:
                        continue
                    mes_key = ref[:7]  # YYYY-MM
                    if mes_key not in meses:
                        meses[mes_key] = {
                            "mes": mes_key,
                            "total_receber": 0.0,
                            "total_pagar": 0.0,
                            "total_parcelas": 0,
                            "parcelas_pagas": 0,
                            "total_leads": set(),
                            "total_contratos": set(),
                            "parcelas": [],
                        }
                    grupo = meses[mes_key]
                    valor_esp = _to_number(parcela.get("valor_esperado"))
                    valor_real = _to_number(parcela.get("valor_real"))
                    is_pago = parcela.get("status_parcela") == 1

                    if tipo == "entradas":
                        grupo["total_receber"] += valor_esp or valor_real
                    else:
                        grupo["total_pagar"] += valor_esp or valor_real

                    grupo["total_parcelas"] += 1
                    if is_pago:
                        grupo["parcelas_pagas"] += 1
                    grupo["total_leads"].add(contrato.get("id_comercial_lead", 0))
                    grupo["total_contratos"].add(contrato.get("id_contrato", 0))

                    grupo["parcelas"].append({
                        "id_financeiro": parcela.get("id_financeiro"),
                        "id_contrato": contrato.get("id_contrato"),
                        "tipo": tipo,
                        "lead_nome": contrato.get("lead_nome") or contrato.get("lead_razao_social") or "—",
                        "parceiro_nome": contrato.get("parceiro_nome") or "—",
                        "nome_solucao": contrato.get("nome_solucao") or "—",
                        "referencia_esperado": parcela.get("referencia_esperado"),
                        "referencia_real": parcela.get("referencia_real"),
                        "valor_esperado": valor_esp,
                        "valor_real": valor_real,
                        "status_parcela": 1 if is_pago else 0,
                        "status_contrato": contrato.get("status") or "—",
                    })

        _process_contracts(entradas, "entradas")
        _process_contracts(saidas, "saidas")

        # Serializa sets
        result = []
        for mes_key in sorted(meses.keys(), reverse=True):
            grupo = meses[mes_key]
            result.append({
                "mes": grupo["mes"],
                "total_receber": round(grupo["total_receber"], 2),
                "total_pagar": round(grupo["total_pagar"], 2),
                "saldo": round(grupo["total_receber"] - grupo["total_pagar"], 2),
                "total_parcelas": grupo["total_parcelas"],
                "parcelas_pagas": grupo["parcelas_pagas"],
                "total_leads": len(grupo["total_leads"]),
                "total_contratos": len(grupo["total_contratos"]),
                "parcelas": sorted(
                    grupo["parcelas"],
                    key=lambda p: (p["referencia_esperado"] or "", p["tipo"]),
                ),
            })

        return {"ok": True, "meses": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/financeiro", response_class=HTMLResponse)
async def financeiro_dashboard(request: Request, auth_user=Depends(get_authenticated_user)):
    redirect = check_admin(auth_user)
    if redirect:
        return redirect
    return _render_financeiro_dashboard_page(request, _build_user(auth_user))


@router.get("/financeiro/saidas", response_class=HTMLResponse)
async def financeiro_saidas(request: Request, auth_user=Depends(get_authenticated_user)):
    redirect = check_admin(auth_user)
    if redirect:
        return redirect
    return _render_financeiro_page(request, _build_user(auth_user), "financeiro-saidas", "#/saidas")


@router.get("/financeiro/entradas", response_class=HTMLResponse)
async def financeiro_entradas(request: Request, auth_user=Depends(get_authenticated_user)):
    redirect = check_admin(auth_user)
    if redirect:
        return redirect
    return _render_financeiro_page(request, _build_user(auth_user), "financeiro-entradas", "#/entradas")


@router.get("/financeiro/contracts")
async def financeiro_contracts(tipo: str, auth_user=Depends(get_authenticated_user)):
    if not auth_user:
        raise HTTPException(status_code=401, detail="Usuario nao autenticado.")
    tipo_norm = (tipo or "").strip().lower()
    if tipo_norm not in {"entradas", "saidas"}:
        raise HTTPException(status_code=400, detail="tipo deve ser 'entradas' ou 'saidas'.")
    try:
        contratos = list_contratos_financeiro(tipo_norm) if settings.PORTFOLIO_DEMO_MODE else __import__("infrastructure.db.financeiro_repository", fromlist=["FinanceiroRepositorySql"]).FinanceiroRepositorySql().list_contratos_financeiro(tipo_norm)
        return {"ok": True, "tipo": tipo_norm, "contratos": contratos}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/financeiro/parcela-status")
async def update_parcela_status(payload: UpdateParcelaStatusPayload, auth_user=Depends(get_authenticated_user)):
    if not auth_user:
        raise HTTPException(status_code=401, detail="Usuario nao autenticado.")
    try:
        if settings.PORTFOLIO_DEMO_MODE:
            result = demo_update_parcela_status(payload.model_dump())
        else:
            from infrastructure.db.financeiro_repository import FinanceiroRepositorySql

            repo = FinanceiroRepositorySql()
            result = repo.update_status_parcela(
                id_contrato=payload.id_contrato,
                id_financeiro=payload.id_financeiro,
                status_parcela=payload.status_parcela,
                referencia_esperado=payload.referencia_esperado,
                referencia_real=payload.referencia_real,
                valor_esperado=payload.valor_esperado,
                valor_real=payload.valor_real,
            )
        return {"ok": True, "result": result}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))





