from __future__ import annotations

import json
from typing import Optional
from sqlalchemy import text

from database.db_provider import get_db_engine
from database.queries import parceria_queries
from infrastructure.db.colaboradores_repository import ColaboradoresRepositorySql
from domain.contracts import ParceriasRepository
from domain.models import ParceriaModel, ComercialSolutionModel, IndicacaoStatsModel


class ParceirosRepositorySql(ParceriasRepository):
    def list_parceiros(self) -> list[ParceriaModel]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(text(parceria_queries.SQL_LIST_PARCEIROS)).mappings().all()

        return [
            ParceriaModel.model_validate(
                {
                    "id": row["id"],
                    "nome": row["nome"],
                    "cnpj": row.get("cnpj"),
                    "razao_social": row.get("razao_social"),
                    "estado": row.get("estado"),
                    "id_crm_lead": row.get("id_crm_lead"),
                    "id_colab_comercial": row.get("id_colab_comercial"),
                    "fol_path": row.get("fol_path"),
                    "data_criacao": row.get("data_criacao"),
                    "modulo_comercial": row.get("modulo_comercial"),
                    "status_comercial": row.get("status_comercial"),
                    "modulo_indicacao": row.get("modulo_indicacao"),
                    "status_indicacao": row.get("status_indicacao"),
                }
            )
            for row in rows
        ]

    def activate_indicacao(self, parceiro_id: int, solucao_id: int = 1) -> dict[str, int]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result_parceria = conn.execute(
                text(parceria_queries.SQL_UPSERT_MODULO_INDICACAO),
                {"id_comercial": parceiro_id},
            )
            result_m2m = conn.execute(
                text(parceria_queries.SQL_UPSERT_M2M_INDICACAO),
                {"id_comercial": parceiro_id, "id_solucao": solucao_id},
            )
        return {
            "parceria_rows": result_parceria.rowcount or 0,
            "m2m_rows": result_m2m.rowcount or 0,
        }

    def activate_comercial(self, parceiro_id: int, solution_ids: list[int]) -> dict[str, int]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result_parceria = conn.execute(
                text(parceria_queries.SQL_UPSERT_MODULO_COMERCIAL),
                {"id_comercial": parceiro_id},
            )
            m2m_rows = 0
            for solucao_id in solution_ids:
                result_m2m = conn.execute(
                    text(parceria_queries.SQL_UPSERT_M2M_SOLUCAO),
                    {"id_comercial": parceiro_id, "id_solucao": solucao_id},
                )
                m2m_rows += result_m2m.rowcount or 0
        return {
            "parceria_rows": result_parceria.rowcount or 0,
            "m2m_rows": m2m_rows,
        }

    def update_colab_comercial(self, parceiro_id: int, id_colab_comercial: str) -> int:
        try:
            id_colab_comercial_int = int(str(id_colab_comercial).strip())
        except (TypeError, ValueError):
            return 0

        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                text(parceria_queries.SQL_UPDATE_ID_COLAB_COMERCIAL),
                {"id_comercial": parceiro_id, "id_colab_comercial": id_colab_comercial_int},
            )
        return result.rowcount or 0

    def get_comercial_solutions(self, parceiro_id: int) -> list[ComercialSolutionModel]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(
                text(parceria_queries.SQL_GET_COMERCIAL_SOLUTIONS),
                {"id_comercial": parceiro_id},
            ).mappings().all()

            lead_counts_rows = conn.execute(
                text(parceria_queries.SQL_COUNT_LEADS_BY_PARCEIRO),
                {"id_comercial": parceiro_id},
            ).mappings().all()

        # Agrupa contagens: { solucao_id: { id_etapa_kanban: total } }
        lead_counts = {}
        for lc in lead_counts_rows:
            sol_id = lc["id_solucao"]
            fase = lc["id_etapa_kanban"]
            total = lc["total"]
            lead_counts.setdefault(sol_id, {})[fase] = total

        default_max_etapa = 4

        result: list[ComercialSolutionModel] = []
        for row in rows:
            sol_id = row["id_solucao"]

            # Determina a última etapa do kanban (= "fechado")
            max_etapa = default_max_etapa
            kanban_raw = row.get("kanban_json")
            if kanban_raw:
                try:
                    parsed = json.loads(kanban_raw) if isinstance(kanban_raw, str) else kanban_raw
                    etapas = parsed.get("etapas", []) if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
                    etapa_ids = [int(e.get("id", 0)) for e in etapas if isinstance(e, dict)]
                    if etapa_ids:
                        max_etapa = max(etapa_ids)
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

            fases = lead_counts.get(sol_id, {})
            leads_gerados = sum(fases.values())
            leads_fechados = fases.get(max_etapa, 0)
            leads_negociacao = leads_gerados - leads_fechados

            result.append(ComercialSolutionModel(
                id=sol_id,
                name=row["nome_solucao"],
                icon=row.get("icon_id") or "layers",
                color=row.get("color_id") or "primary",
                status="active",
                startDate=None,
                endDate=None,
                closedLeads=leads_fechados,
                leadsGenerated=leads_gerados,
                leadsNegotiation=leads_negociacao,
            ))

        return result

    def get_indicacao_stats(self, parceiro_id: int) -> IndicacaoStatsModel:
        """Retorna KPIs do módulo indicação (solucao_id=1) para um parceiro."""
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(
                text(parceria_queries.SQL_COUNT_LEADS_BY_PARCEIRO),
                {"id_comercial": parceiro_id},
            ).mappings().all()

        # Filtra apenas solucao_id = 1 (indicação)
        fases = {}
        for row in rows:
            if row["id_solucao"] == 1:
                fases[row["id_etapa_kanban"]] = row["total"]

        # Indicação usa kanban padrão (max etapa = 4)
        max_etapa = 4
        leads_gerados = sum(fases.values())
        leads_fechados = fases.get(max_etapa, 0)
        leads_negociacao = leads_gerados - leads_fechados
        taxa = round((leads_fechados / leads_gerados) * 100) if leads_gerados > 0 else 0

        return IndicacaoStatsModel(
            leadsGenerated=leads_gerados,
            leadsNegotiation=leads_negociacao,
            leadsClosed=leads_fechados,
            conversionRate=taxa,
        )

    def list_parceiros_kanban(self) -> list[dict]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(text(parceria_queries.SQL_LIST_PARCEIROS_KANBAN)).mappings().all()

        colab_repo = ColaboradoresRepositorySql()
        cache_nome = {}

        def nome_by_crm(crm_id):
            if not crm_id:
                return None
            key = f"b:{crm_id}"
            if key not in cache_nome:
                cache_nome[key] = colab_repo.get_nome_by_crm_id(str(crm_id))
            return cache_nome[key]

        def nome_by_col(id_col):
            if not id_col:
                return None
            key = f"c:{id_col}"
            if key not in cache_nome:
                cache_nome[key] = colab_repo.get_nome_by_id_col(id_col)
            return cache_nome[key]

        return [
            {
                "id": f"{row.get('id_comercial')}-{row.get('id_solucao')}",
                "id_comercial": row.get("id_comercial"),
                "id_solucao": row.get("id_solucao"),
                "id_status_kanban": row.get("id_status_kanban"),
                "name": row.get("nome") or "",
                "razao_social": row.get("razao_social") or "",
                "cnpj": row.get("cnpj") or "",
                "id_colab_comercial": row.get("id_colab_comercial"),
                "colab_comercial_nome": nome_by_crm(row.get("id_colab_comercial")),
                "id_colab_comercial": row.get("id_colab_comercial"),
                "colab_comercial_nome": nome_by_col(row.get("id_colab_comercial")),
            }
            for row in rows
        ]

    def update_parceiro_kanban_status(self, id_comercial: int, id_solucao: int, id_status_kanban: int) -> int:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                text(parceria_queries.SQL_UPDATE_PARCEIRO_KANBAN_STATUS),
                {
                    "id_comercial": id_comercial,
                    "id_solucao": id_solucao,
                    "id_status_kanban": id_status_kanban,
                },
            )
        return result.rowcount or 0

    def update_parceiro_responsaveis(
        self,
        id_comercial: int,
        id_colab_comercial: Optional[int],
    ) -> dict[str, int]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            res_comercial = conn.execute(
                text(parceria_queries.SQL_UPSERT_PARCERIA_COLAB_COMERCIAL),
                {
                    "id_comercial": id_comercial,
                    "id_colab_comercial": str(id_colab_comercial) if id_colab_comercial not in (None, "") else None,
                },
            )
            res_comercial = conn.execute(
                text(parceria_queries.SQL_UPDATE_PARCEIRO_ID_COLAB_COMERCIAL),
                {
                    "id_comercial": id_comercial,
                    "id_colab_comercial": id_colab_comercial,
                },
            )
        return {
            "comercial_rows": res_comercial.rowcount or 0,
            "comercial_rows": res_comercial.rowcount or 0,
        }

    def update_parceiro(self, id_comercial: int, nome: str, cnpj: Optional[str], razao_social: Optional[str]) -> int:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                text(parceria_queries.SQL_UPDATE_PARCEIRO),
                {
                    "id_comercial": id_comercial,
                    "nome": nome,
                    "cnpj": cnpj,
                    "razao_social": razao_social,
                },
            )
        return result.rowcount or 0

    def has_leads(self, id_comercial: int) -> bool:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            row = conn.execute(
                text(parceria_queries.SQL_CHECK_PARCEIRO_HAS_LEADS),
                {"id_comercial": id_comercial},
            ).first()
        return row is not None

    def delete_parceiro(self, id_comercial: int) -> int:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            conn.execute(
                text(parceria_queries.SQL_DELETE_PARCEIRO_M2M),
                {"id_comercial": id_comercial},
            )
            conn.execute(
                text(parceria_queries.SQL_DELETE_PARCEIRO_PARCERIA),
                {"id_comercial": id_comercial},
            )
            result = conn.execute(
                text(parceria_queries.SQL_DELETE_PARCEIRO),
                {"id_comercial": id_comercial},
            )
        return result.rowcount or 0
