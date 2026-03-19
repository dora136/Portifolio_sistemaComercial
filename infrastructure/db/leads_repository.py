from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import text

from database.db_provider import get_db_engine
import json

from database.queries import lead_queries, solucao_queries
from infrastructure.db.colaboradores_repository import ColaboradoresRepositorySql
from domain.contracts import LeadsRepository
from domain.models import LeadModel, LeadInfoFieldModel, LeadSummaryModel, ComercialModel


class LeadsRepositorySql(LeadsRepository):
    def create_lead(
        self,
        lead_id: int,
        solution_ids: Iterable[int],
        *,
        nome: Optional[str] = None,
        razao_social: Optional[str] = None,
        cnpj: Optional[str] = None,
        id_crm_lead: Optional[int] = None,
    ) -> dict:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        unique_solution_ids = [int(sol_id) for sol_id in dict.fromkeys(solution_ids)]

        with engine.begin() as conn:
            updated = conn.execute(
                text(lead_queries.SQL_UPDATE_LEAD_COMERCIAL),
                {
                    "id_comercial": lead_id,
                    "nome": nome,
                    "razao_social": razao_social,
                    "cnpj": cnpj,
                    "id_crm_lead": id_crm_lead,
                },
            )

            if unique_solution_ids:
                payload = [
                    {"id_comercial": lead_id, "id_solucao": sol_id}
                    for sol_id in unique_solution_ids
                ]
                conn.execute(text(lead_queries.SQL_INSERT_COMERCIAL_LEAD), payload)

        return {
            "updated": updated.rowcount or 0,
            "linkedSolutions": len(unique_solution_ids),
        }

    def get_comercial_by_cnpj(self, cnpj_digits: str) -> Optional[ComercialModel]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            row = conn.execute(
                text(lead_queries.SQL_SELECT_COMERCIAL_BY_CNPJ),
                {"cnpj": cnpj_digits},
            ).mappings().first()

        if not row:
            return None

        return ComercialModel(
            id=row["id"],
            nome=row["nome"],
            id_crm_lead=row.get("id_crm_lead"),
            id_crm_emp=row.get("id_crm_emp"),
            cnpj=row.get("cnpj"),
        )

    def get_comercial_by_id(self, id_comercial: int) -> Optional[ComercialModel]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            row = conn.execute(
                text(lead_queries.SQL_SELECT_COMERCIAL_BY_ID),
                {"id_comercial": id_comercial},
            ).mappings().first()

        if not row:
            return None

        return ComercialModel(
            id=row["id"],
            nome=row["nome"],
            id_crm_lead=row.get("id_crm_lead"),
            id_crm_emp=row.get("id_crm_emp"),
            cnpj=row.get("cnpj"),
        )

    def get_solucao_kanban_json(self, solucao_id: int) -> Optional[str]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            row = conn.execute(
                text(solucao_queries.SQL_GET_SOLUCAO_KANBAN),
                {"id_solucao": solucao_id},
            ).first()

        if not row:
            return None

        return row[0]

    def get_solucao_registro_info_json(self, solucao_id: int) -> Optional[str]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            row = conn.execute(
                text(solucao_queries.SQL_GET_SOLUCAO_REGISTRO_INFO),
                {"id_solucao": solucao_id},
            ).first()

        if not row:
            return None

        return row[0]

    def _process_lead_rows(self, rows) -> list[LeadModel]:
        colab_repo = ColaboradoresRepositorySql()
        colab_cache = {}
        result = []
        for row in rows:
            nome = row.get("nome")
            razao_social = row.get("razao_social")
            display_name = nome or razao_social or "Lead"
            company_name = razao_social if razao_social and razao_social != display_name else None
            id_comercial = int(row["id_comercial"]) if row.get("id_comercial") is not None else 0
            id_solucao = int(row["id_solucao"]) if row.get("id_solucao") is not None else 0
            lead_id = f"{id_comercial}-{id_solucao}"

            etapa_kanban = row.get("id_etapa_kanban") or 1
            try:
                etapa_kanban = int(etapa_kanban)
            except (TypeError, ValueError):
                etapa_kanban = 1

            info_raw = row.get("informacoes_json")
            info_payload = []
            if info_raw:
                try:
                    parsed = json.loads(info_raw) if isinstance(info_raw, str) else info_raw
                    if isinstance(parsed, dict):
                        info_payload = parsed.get("fields", [])
                    elif isinstance(parsed, list):
                        info_payload = parsed
                except (TypeError, ValueError):
                    info_payload = []

            normalized_info = []
            for item in info_payload or []:
                if not isinstance(item, dict):
                    continue
                normalized_info.append(LeadInfoFieldModel(
                    name=item.get("name") or "",
                    type=item.get("type") or "string",
                    value=item.get("value"),
                ))

            id_colab_comercial = row.get("id_colab_comercial")
            id_colab_comercial = row.get("id_colab_comercial")
            id_comercial_parceiro = row.get("id_comercial_parceiro")
            representante_parceiro_nome = row.get("nome_parceiro")

            colab_comercial_nome = None
            if id_colab_comercial:
                cache_key = ("crm", id_colab_comercial)
                if cache_key in colab_cache:
                    colab_comercial_nome = colab_cache[cache_key]
                else:
                    colab_comercial_nome = colab_repo.get_nome_by_crm_id(str(id_colab_comercial))
                    colab_cache[cache_key] = colab_comercial_nome

            comercial_nome = None
            if id_colab_comercial:
                cache_key = ("col", id_colab_comercial)
                if cache_key in colab_cache:
                    comercial_nome = colab_cache[cache_key]
                else:
                    comercial_nome = colab_repo.get_nome_by_id_col(id_colab_comercial)
                    colab_cache[cache_key] = comercial_nome

            result.append(LeadModel(
                id=lead_id,
                id_comercial=id_comercial,
                id_solucao=id_solucao,
                id_etapa=etapa_kanban,
                name=display_name,
                company=company_name,
                nome_fantasia=nome,
                razao_social=razao_social,
                cnpj=row.get("cnpj"),
                id_colab_comercial=id_colab_comercial,
                colab_comercial_nome=colab_comercial_nome,
                comercial_nome=comercial_nome,
                id_comercial_parceiro=id_comercial_parceiro,
                representante_parceiro_nome=representante_parceiro_nome,
                informacoes=normalized_info,
                lastAction=None,
                createdAt=None,
                email=None,
            ))

        return result

    def list_comercial_leads(self) -> list[LeadModel]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(text(lead_queries.SQL_LIST_COMERCIAL_LEADS)).mappings().all()
        return self._process_lead_rows(rows)

    def create_lead_kanban(
        self,
        lead_id: int,
        lead_rows: Iterable[dict],
        solution_ids: Iterable[int],
    ) -> dict:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        unique_solution_ids = [int(sol_id) for sol_id in dict.fromkeys(solution_ids)]
        lead_payload = list(lead_rows)
        m2m_rows = 0

        with engine.begin() as conn:
            if lead_payload:
                conn.execute(
                    text(lead_queries.SQL_INSERT_COMERCIAL_LEAD_WITH_PHASE),
                    lead_payload,
                )

            for sol_id in unique_solution_ids:
                result_m2m = conn.execute(
                    text(lead_queries.SQL_UPSERT_M2M_SOLUCAO),
                    {"id_comercial": lead_id, "id_solucao": sol_id},
                )
                m2m_rows += result_m2m.rowcount or 0

        return {
            "lead_rows": len(lead_payload),
            "m2m_rows": m2m_rows,
        }

    def update_comercial_lead(
        self,
        id_comercial: int,
        id_solucao: int,
        id_etapa_kanban: int,
        id_comercial_parceiro: Optional[int],
        informacoes: list[dict],
        id_colab_comercial: Optional[str | int],
    ) -> int:
        informacoes_json_str = json.dumps(informacoes, ensure_ascii=False) if informacoes else None
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                text(lead_queries.SQL_UPDATE_COMERCIAL_LEAD),
                {
                    "id_comercial": id_comercial,
                    "id_solucao": id_solucao,
                    "id_etapa_kanban": id_etapa_kanban,
                    "id_comercial_parceiro": id_comercial_parceiro,
                    "informacoes_json": informacoes_json_str,
                    "id_colab_comercial": str(id_colab_comercial) if id_colab_comercial not in (None, "") else None,
                },
            )
        return result.rowcount or 0

    def update_comercial_lead_parceiro(
        self,
        id_comercial: int,
        id_solucao: int,
        id_comercial_parceiro: Optional[int],
    ) -> int:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                text(lead_queries.SQL_UPDATE_COMERCIAL_LEAD_PARCEIRO),
                {
                    "id_comercial": id_comercial,
                    "id_solucao": id_solucao,
                    "id_comercial_parceiro": id_comercial_parceiro,
                },
            )
        return result.rowcount or 0

    def delete_comercial_lead(self, id_comercial: int, id_solucao: int) -> int:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                text(lead_queries.SQL_DELETE_COMERCIAL_LEAD),
                {"id_comercial": id_comercial, "id_solucao": id_solucao},
            )
        return result.rowcount or 0

    def get_leads_by_solucao(self, solucao_id: int) -> list[LeadSummaryModel]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(
                text(lead_queries.SQL_GET_LEADS_BY_SOLUCAO),
                {"id_solucao": solucao_id},
            ).mappings().all()

        leads: list[LeadSummaryModel] = []
        seen = set()
        for row in rows:
            id_comercial = row.get("id_comercial")
            name = row.get("nome") or row.get("razao_social") or ""
            if not name or not id_comercial:
                continue
            if id_comercial in seen:
                continue
            seen.add(id_comercial)
            leads.append(LeadSummaryModel(id_comercial=int(id_comercial), name=name))

        return leads

    def list_comercial_leads_by_comercial(self, id_comercial: int) -> list[LeadModel]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(
                text(lead_queries.SQL_LIST_COMERCIAL_LEADS_BY_COMERCIAL),
                {"id_comercial": id_comercial},
            ).mappings().all()
        return self._process_lead_rows(rows)

    def list_comercial_leads_by_parceiro(self, id_comercial_parceiro: int) -> list[LeadModel]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(
                text(lead_queries.SQL_LIST_COMERCIAL_LEADS_BY_PARCEIRO),
                {"id_comercial_parceiro": id_comercial_parceiro},
            ).mappings().all()
        return self._process_lead_rows(rows)

    def get_lead_solution_ids(self, lead_id: int) -> set[int]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(
                text(lead_queries.SQL_LIST_LEAD_SOLUCOES),
                {"id_comercial": lead_id},
            ).fetchall()

        solution_ids: set[int] = set()
        for row in rows or []:
            try:
                sol_id = int(row[0])
            except (TypeError, ValueError, IndexError):
                continue
            solution_ids.add(sol_id)

        return solution_ids

    def update_crm_company_id(self, id_comercial: int, id_crm_emp: Optional[int]) -> int:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                text(lead_queries.SQL_UPDATE_ID_CRM_EMP),
                {"id_comercial": id_comercial, "id_crm_emp": id_crm_emp},
            )
        return result.rowcount or 0

    def update_comercial_responsavel(self, id_comercial: int, id_colab_comercial: int) -> int:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                text(lead_queries.SQL_UPDATE_ID_COLAB_COMERCIAL),
                {
                    "id_comercial": id_comercial,
                    "id_colab_comercial": int(id_colab_comercial),
                },
            )
        return result.rowcount or 0

    def get_lead_etapa(self, id_comercial: int, id_solucao: int) -> Optional[int]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            row = conn.execute(
                text(lead_queries.SQL_GET_COMERCIAL_LEAD_STAGE),
                {"id_comercial": id_comercial, "id_solucao": id_solucao},
            ).first()

        if not row:
            return None

        try:
            return int(row[0])
        except (TypeError, ValueError, IndexError):
            return None

    def create_comercial(
        self,
        *,
        nome: Optional[str],
        tipo_comercial: str,
        cnpj: Optional[str],
        razao_social: Optional[str],
        segmento: Optional[str],
        id_colab_comercial: Optional[int],
        origem: str,
    ) -> Optional[int]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                text(lead_queries.SQL_INSERT_COMERCIAL),
                {
                    "nome": nome,
                    "tipo_comercial": tipo_comercial,
                    "cnpj": cnpj,
                    "razao_social": razao_social,
                    "segmento": segmento,
                    "id_colab_comercial": id_colab_comercial,
                    "origem": origem,
                },
            )
            row = result.fetchone()
            if row:
                try:
                    return int(row[0])
                except (TypeError, ValueError, IndexError):
                    return None
        return None
