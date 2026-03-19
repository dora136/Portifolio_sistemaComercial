from __future__ import annotations

import json
from datetime import date, datetime

from sqlalchemy import text

from database.db_provider import get_db_engine
from database.queries import contrato_financeiro_queries
from domain.contracts import FinanceiroRepository
from domain.models import ContratoFinanceiroModel


def _to_iso_date(value):
    if value in (None, "", "â€”", "-"):
        return None
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value)


def _parse_date(value):
    if value in (None, "", "Ã¢â‚¬â€", "-"):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return None


def _to_float(value):
    if value in (None, "", "â€”", "-"):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw:
        return None
    # Aceita formatos: 1234.56, 1.234,56, R$ 1.234,56
    normalized = raw.replace("R$", "").replace(" ", "")
    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    normalized = "".join(ch for ch in normalized if ch.isdigit() or ch in ".-")
    if normalized in {"", "-", ".", "-."}:
        return None
    try:
        return float(normalized)
    except (TypeError, ValueError):
        return None


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_json_obj(value):
    if value in (None, ""):
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    return {}


def _is_parcela_paga(parcela: dict) -> bool:
    status = parcela.get("status_parcela")
    if status in (1, "1", True):
        return True
    if parcela.get("referencia_real"):
        return True
    valor_real = parcela.get("valor_real")
    try:
        return float(valor_real or 0) > 0
    except (TypeError, ValueError):
        return False


def _compute_contrato_status(parcelas: list[dict]) -> str:
    if not parcelas:
        return "Pendente"

    paid_flags = [_is_parcela_paga(p) for p in parcelas]
    if paid_flags and all(paid_flags):
        return "Quitado"

    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    previous_month_end = current_month_start

    unpaid_with_due = []
    unpaid_current_month = []
    current_month_paid = []
    for parcela in parcelas:
        due = _parse_date(parcela.get("referencia_esperado"))
        if not due:
            continue
        paid = _is_parcela_paga(parcela)
        if not paid:
            unpaid_with_due.append(due)
            if due.year == today.year and due.month == today.month:
                unpaid_current_month.append(due)
        else:
            if due.year == today.year and due.month == today.month:
                current_month_paid.append(due)

    has_overdue_previous_month = any(d < previous_month_end for d in unpaid_with_due)
    if has_overdue_previous_month:
        return "Atrasado"

    if unpaid_current_month:
        return "Pendente"

    if current_month_paid:
        return "Em dia"

    # Sem parcelas vencidas no mÃªs e sem atraso anterior => em dia.
    return "Em dia"


def _compute_receita_from_parcelas(parcelas: list[dict]) -> float:
    total = 0.0
    for parcela in parcelas or []:
        valor_esperado = _to_float(parcela.get("valor_esperado"))
        valor_real = _to_float(parcela.get("valor_real"))
        if valor_esperado is None:
            total += float(valor_real or 0.0)
        else:
            total += float(valor_esperado)
    return round(total, 2)


class FinanceiroRepositorySql(FinanceiroRepository):
    """
    Repositorio para persistencia de contratos financeiros na base principal.

    Regras aplicadas:
    - Campos comuns (status, id_responsavel e IDs) ficam em colunas dedicadas.
    - Campos especificos de cada modelo sao salvos em infos_json.
    - num_colunas em tb_portfolio_contratos representa a quantidade de linhas gravadas em tb_portfolio_parcelas.
    """

    def save_contrato_financeiro(self, payload: ContratoFinanceiroModel) -> dict[str, int]:
        engine = get_db_engine(db_key="app_data", profile="ddl")

        parcelas_payload = [
            {
                "referencia_esperado": _to_iso_date(parcela.referencia_esperado),
                "referencia_real": _to_iso_date(parcela.referencia_real),
                "valor_esperado": _to_float(parcela.valor_esperado),
                "valor_real": _to_float(parcela.valor_real),
                "status_parcela": 1 if (_to_float(parcela.valor_real) or 0) > 0 or _to_iso_date(parcela.referencia_real) else 0,
            }
            for parcela in (payload.parcelas or [])
        ]
        infos_payload = dict(payload.infos_json or {})
        campos_payload = infos_payload.get("campos") if isinstance(infos_payload.get("campos"), dict) else {}
        receita_total = _compute_receita_from_parcelas(parcelas_payload)
        # Forca receita como soma das parcelas, sobrescrevendo valor digitado.
        campos_payload["receita"] = receita_total
        campos_payload["coluna_fixa_1"] = receita_total
        infos_payload["campos"] = campos_payload
        status_auto = _compute_contrato_status(parcelas_payload)
        num_colunas = len(parcelas_payload)
        infos_json_str = json.dumps(infos_payload, ensure_ascii=False)

        with engine.begin() as conn:
            params = {
                "id_comercial_lead": payload.id_comercial_lead,
                "id_solucao": payload.id_solucao,
                "id_comercial_parceiro": payload.id_comercial_parceiro,
                "id_responsavel": payload.id_responsavel,
                "status": status_auto,
                "infos_json": infos_json_str,
                "num_colunas": num_colunas,
            }

            id_contrato = payload.id_contrato
            if id_contrato:
                result_tipo = conn.execute(
                    text(contrato_financeiro_queries.SQL_UPDATE_COMERCIAL_CONTRATO_BY_ID),
                    {
                        **params,
                        "id_contrato": id_contrato,
                    },
                )
                if (result_tipo.rowcount or 0) == 0:
                    insert_row = conn.execute(
                        text(contrato_financeiro_queries.SQL_INSERT_COMERCIAL_CONTRATO),
                        params,
                    ).mappings().first()
                    id_contrato = int(insert_row["id_contrato"])
            else:
                insert_row = conn.execute(
                    text(contrato_financeiro_queries.SQL_INSERT_COMERCIAL_CONTRATO),
                    params,
                ).mappings().first()
                id_contrato = int(insert_row["id_contrato"])
                result_tipo = None

            # Regrava parcelas do contrato (snapshot atual)
            conn.execute(
                text(contrato_financeiro_queries.SQL_DELETE_PARCELAS_BY_CONTRATO),
                {"id_contrato": id_contrato},
            )

            parcelas_rows = 0
            for parcela in parcelas_payload:
                conn.execute(
                    text(contrato_financeiro_queries.SQL_INSERT_PARCELA),
                    {
                        "id_contrato": id_contrato,
                        "referencia_esperado": parcela["referencia_esperado"],
                        "referencia_real": parcela["referencia_real"],
                        "valor_esperado": parcela["valor_esperado"],
                        "valor_real": parcela["valor_real"],
                        "status_parcela": parcela["status_parcela"],
                    },
                )
                parcelas_rows += 1

        return {
            "id_contrato": id_contrato,
            "status": status_auto,
            "contrato_rows": (result_tipo.rowcount if result_tipo is not None else 1) or 0,
            "parcelas_rows": parcelas_rows,
        }

    def get_contrato_financeiro(
        self,
        id_comercial_lead: int,
        id_solucao: int,
        id_comercial_parceiro: int,
    ) -> dict | None:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            contrato_row = conn.execute(
                text(contrato_financeiro_queries.SQL_SELECT_COMERCIAL_CONTRATO_BY_COMPOSITE),
                {
                    "id_comercial_lead": id_comercial_lead,
                    "id_solucao": id_solucao,
                    "id_comercial_parceiro": id_comercial_parceiro,
                },
            ).mappings().first()

            if not contrato_row:
                return None

            id_contrato = int(contrato_row["id_contrato"])
            parcelas_rows = conn.execute(
                text(contrato_financeiro_queries.SQL_SELECT_PARCELAS_BY_CONTRATO),
                {"id_contrato": id_contrato},
            ).mappings().all()
            parcelas_payload = [
                {
                    "id_financeiro": row.get("id_financeiro"),
                    "referencia_esperado": _to_iso_date(row.get("referencia_esperado")),
                    "referencia_real": _to_iso_date(row.get("referencia_real")),
                    "valor_esperado": _to_float(row.get("valor_esperado")),
                    "valor_real": _to_float(row.get("valor_real")),
                    "status_parcela": 1 if row.get("status_parcela") in (1, "1", True) else 0,
                }
                for row in parcelas_rows
            ]
            receita_total = _compute_receita_from_parcelas(parcelas_payload)
            status_auto = _compute_contrato_status(parcelas_payload)
            if status_auto != (contrato_row.get("status") or ""):
                conn.execute(
                    text(contrato_financeiro_queries.SQL_UPDATE_STATUS_CONTRATO),
                    {"id_contrato": id_contrato, "status": status_auto},
                )

            infos_json = _parse_json_obj(contrato_row.get("infos_json"))
            campos = infos_json.get("campos") if isinstance(infos_json.get("campos"), dict) else {}
            campos["receita"] = receita_total
            campos["coluna_fixa_1"] = receita_total
            infos_json["campos"] = campos

            return {
                "id_contrato": id_contrato,
                "id_comercial_lead": _to_int(contrato_row.get("id_comercial_lead"), 0),
                "id_solucao": _to_int(contrato_row.get("id_solucao"), 0),
                "id_comercial_parceiro": _to_int(contrato_row.get("id_comercial_parceiro"), 0),
                "id_responsavel": _to_int(contrato_row.get("id_responsavel")),
                "status": status_auto,
                "num_colunas": contrato_row.get("num_colunas"),
                "infos_json": infos_json,
                "parcelas": parcelas_payload,
            }

    def list_contratos_financeiro(self, tipo: str) -> list[dict]:
        tipo_norm = (tipo or "").strip().lower()
        if tipo_norm not in {"entradas", "saidas"}:
            raise ValueError("tipo deve ser 'entradas' ou 'saidas'")

        query = (
            contrato_financeiro_queries.SQL_LIST_CONTRATOS_SAIDAS
            if tipo_norm == "saidas"
            else contrato_financeiro_queries.SQL_LIST_CONTRATOS_ENTRADAS
        )

        engine = get_db_engine(db_key="app_data", profile="ddl")
        contratos: list[dict] = []
        with engine.begin() as conn:
            rows = conn.execute(text(query)).mappings().all()
            for row in rows:
                id_contrato = int(row["id_contrato"])
                parcelas_rows = conn.execute(
                    text(contrato_financeiro_queries.SQL_SELECT_PARCELAS_BY_CONTRATO),
                    {"id_contrato": id_contrato},
                ).mappings().all()
                parcelas = [
                    {
                        "id_financeiro": p.get("id_financeiro"),
                        "referencia_esperado": _to_iso_date(p.get("referencia_esperado")),
                        "referencia_real": _to_iso_date(p.get("referencia_real")),
                        "valor_esperado": _to_float(p.get("valor_esperado")),
                        "valor_real": _to_float(p.get("valor_real")),
                        "status_parcela": 1 if p.get("status_parcela") in (1, "1", True) else 0,
                    }
                    for p in parcelas_rows
                ]
                receita_total = _compute_receita_from_parcelas(parcelas)
                status_auto = _compute_contrato_status(parcelas)
                if status_auto != (row.get("status") or ""):
                    conn.execute(
                        text(contrato_financeiro_queries.SQL_UPDATE_STATUS_CONTRATO),
                        {"id_contrato": id_contrato, "status": status_auto},
                    )

                infos_json = _parse_json_obj(row.get("infos_json"))
                campos = infos_json.get("campos") if isinstance(infos_json.get("campos"), dict) else {}
                campos["receita"] = receita_total
                campos["coluna_fixa_1"] = receita_total
                infos_json["campos"] = campos

                contratos.append(
                    {
                        "id_contrato": id_contrato,
                        "id_comercial_lead": _to_int(row.get("id_comercial_lead"), 0),
                        "id_solucao": _to_int(row.get("id_solucao"), 0),
                        "id_comercial_parceiro": _to_int(row.get("id_comercial_parceiro"), 0),
                        "id_responsavel": _to_int(row.get("id_responsavel")),
                        "status": status_auto,
                        "num_colunas": row.get("num_colunas"),
                        "lead_nome": row.get("lead_nome"),
                        "lead_razao_social": row.get("lead_razao_social"),
                        "lead_cnpj": row.get("lead_cnpj"),
                        "lead_email": row.get("lead_email"),
                        "lead_telefone": row.get("lead_telefone"),
                        "parceiro_nome": row.get("parceiro_nome"),
                        "nome_solucao": row.get("nome_solucao"),
                        "modelo_contrato": infos_json.get("modelo_contrato"),
                        "infos_json": infos_json,
                        "campos": campos,
                        "parcelas": parcelas,
                    }
                )

        return contratos

    def update_status_parcela(
        self,
        id_contrato: int,
        id_financeiro: int,
        status_parcela: int,
        referencia_esperado: str | None = None,
        referencia_real: str | None = None,
        valor_esperado: float | None = None,
        valor_real: float | None = None,
    ) -> dict:
        status_int = 1 if int(status_parcela) == 1 else 0
        today_iso = date.today().isoformat()
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            parcela_row = conn.execute(
                text(contrato_financeiro_queries.SQL_SELECT_PARCELA_BY_ID),
                {"id_contrato": id_contrato, "id_financeiro": id_financeiro},
            ).mappings().first()
            if not parcela_row:
                raise ValueError("Parcela nao encontrada")

            curr_ref_esperado = _to_iso_date(parcela_row.get("referencia_esperado"))
            curr_ref_real = _to_iso_date(parcela_row.get("referencia_real"))
            curr_valor_esperado = _to_float(parcela_row.get("valor_esperado"))
            curr_valor_real = _to_float(parcela_row.get("valor_real"))

            ref_esperado_next = _to_iso_date(referencia_esperado) if referencia_esperado is not None else curr_ref_esperado
            val_esperado_next = _to_float(valor_esperado) if valor_esperado is not None else curr_valor_esperado
            ref_real_next = _to_iso_date(referencia_real) if referencia_real is not None else curr_ref_real
            val_real_next = _to_float(valor_real) if valor_real is not None else curr_valor_real

            if status_int == 1:
                if ref_real_next is None:
                    ref_real_next = today_iso
                if val_real_next is None:
                    val_real_next = val_esperado_next
            else:
                # Mantem os valores informados manualmente; se nenhum veio, limpa como comportamento atual.
                if referencia_real is None and valor_real is None:
                    ref_real_next = None
                    val_real_next = None

            conn.execute(
                text(contrato_financeiro_queries.SQL_UPDATE_PARCELA_FULL),
                {
                    "id_contrato": id_contrato,
                    "id_financeiro": id_financeiro,
                    "status_parcela": status_int,
                    "referencia_esperado": ref_esperado_next,
                    "referencia_real": ref_real_next,
                    "valor_esperado": val_esperado_next,
                    "valor_real": val_real_next,
                },
            )

            parcelas_rows = conn.execute(
                text(contrato_financeiro_queries.SQL_SELECT_PARCELAS_BY_CONTRATO),
                {"id_contrato": id_contrato},
            ).mappings().all()
            parcelas = [
                {
                    "id_financeiro": p.get("id_financeiro"),
                    "referencia_esperado": _to_iso_date(p.get("referencia_esperado")),
                    "referencia_real": _to_iso_date(p.get("referencia_real")),
                    "valor_esperado": _to_float(p.get("valor_esperado")),
                    "valor_real": _to_float(p.get("valor_real")),
                    "status_parcela": 1 if p.get("status_parcela") in (1, "1", True) else 0,
                }
                for p in parcelas_rows
            ]
            receita_total = _compute_receita_from_parcelas(parcelas)
            status_auto = _compute_contrato_status(parcelas)
            conn.execute(
                text(contrato_financeiro_queries.SQL_UPDATE_STATUS_CONTRATO),
                {"id_contrato": id_contrato, "status": status_auto},
            )

            info_row = conn.execute(
                text("SELECT infos_json FROM tb_portfolio_contratos WHERE id_contrato = :id_contrato"),
                {"id_contrato": id_contrato},
            ).mappings().first()
            infos_payload = _parse_json_obj(info_row.get("infos_json") if info_row else None)
            campos_payload = infos_payload.get("campos") if isinstance(infos_payload.get("campos"), dict) else {}
            campos_payload["receita"] = receita_total
            campos_payload["coluna_fixa_1"] = receita_total
            infos_payload["campos"] = campos_payload
            conn.execute(
                text("UPDATE tb_portfolio_contratos SET infos_json = :infos_json WHERE id_contrato = :id_contrato"),
                {
                    "id_contrato": id_contrato,
                    "infos_json": json.dumps(infos_payload, ensure_ascii=False),
                },
            )

        return {
            "id_contrato": id_contrato,
            "id_financeiro": id_financeiro,
            "status_parcela": status_int,
            "status_contrato": status_auto,
        }
