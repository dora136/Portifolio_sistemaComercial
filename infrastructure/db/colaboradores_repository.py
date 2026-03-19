from __future__ import annotations

from typing import Optional, List
from sqlalchemy import text
from database.db_provider import get_db_engine
from database.queries import colaborador_queries
from domain.contracts import ColaboradoresRepository
from domain.models import ColaboradorModel


class ColaboradoresRepositorySql(ColaboradoresRepository):
    """Repository para consultas de usuarios na base auxiliar."""

    def get_nome_by_crm_id(self, id_crm_colab: str) -> Optional[str]:
        """Busca o nome do colaborador pelo id_crm_colab."""
        engine = get_db_engine(db_key="people_data", profile="reader")

        with engine.begin() as conn:
            result = conn.execute(
                text(colaborador_queries.SQL_GET_COLABORADOR_BY_CRM_ID),
                {"id_crm_colab": id_crm_colab},
            )
            row = result.fetchone()
            if row:
                return row[1]  # coluna 'nome'
            return None

    def get_nome_by_id_col(self, id_col) -> Optional[str]:
        """Busca o nome do colaborador pelo id_col."""
        engine = get_db_engine(db_key="people_data", profile="reader")

        with engine.begin() as conn:
            result = conn.execute(
                text(colaborador_queries.SQL_GET_COLABORADOR_BY_ID_COL),
                {"id_col": int(id_col)},
            )
            row = result.fetchone()
            if row:
                return row[1]  # coluna 'nome'
            return None

    def get_id_col_by_crm_id(self, id_crm_colab: str) -> Optional[int]:
        """Busca o id_col pelo id_crm_colab."""
        engine = get_db_engine(db_key="people_data", profile="reader")

        with engine.begin() as conn:
            result = conn.execute(
                text(colaborador_queries.SQL_GET_COLABORADOR_BY_CRM_ID),
                {"id_crm_colab": id_crm_colab},
            )
            row = result.fetchone()
            if row and row[0] is not None:
                try:
                    return int(row[0])
                except (TypeError, ValueError):
                    return None
            return None

    def get_crm_id_by_id_col(self, id_col) -> Optional[str]:
        """Busca o id_crm_colab pelo id_col."""
        engine = get_db_engine(db_key="people_data", profile="reader")

        with engine.begin() as conn:
            result = conn.execute(
                text(colaborador_queries.SQL_GET_COLABORADOR_BY_ID_COL),
                {"id_col": int(id_col)},
            )
            row = result.fetchone()
            if row:
                return str(row[2]) if row[2] is not None else None
            return None

    def get_id_col_by_nome(self, nome: str) -> Optional[int]:
        """Busca o id_col pelo nome do colaborador."""
        nome = (nome or "").strip()
        if not nome:
            return None

        engine = get_db_engine(db_key="people_data", profile="reader")
        with engine.begin() as conn:
            result = conn.execute(
                text(colaborador_queries.SQL_GET_COLABORADOR_BY_NOME),
                {"nome": nome},
            )
            row = result.fetchone()
            if row and row[0] is not None:
                try:
                    return int(row[0])
                except (TypeError, ValueError):
                    return None
            return None

    def get_crm_id_by_nome(self, nome: str) -> Optional[str]:
        """Busca o id_crm_colab pelo nome do colaborador."""
        nome = (nome or "").strip()
        if not nome:
            return None

        engine = get_db_engine(db_key="people_data", profile="reader")
        with engine.begin() as conn:
            result = conn.execute(
                text(colaborador_queries.SQL_GET_COLABORADOR_BY_NOME),
                {"nome": nome},
            )
            row = result.fetchone()
            if row:
                return str(row[2]) if row[2] is not None else None
            return None

    def list_comerciais_ativos(self) -> List[ColaboradorModel]:
        """Lista colaboradores ativos da area Comercial."""
        engine = get_db_engine(db_key="people_data", profile="reader")

        with engine.begin() as conn:
            result = conn.execute(text(colaborador_queries.SQL_LIST_COMERCIAIS_ATIVOS))
            rows = result.fetchall()
            return [
                ColaboradorModel(id_col=row[0], nome=row[1], id_crm_colab=str(row[2]) if row[2] is not None else None)
                for row in rows
            ]

    def list_comerciais_exceto_ia(self) -> List[ColaboradorModel]:
        """Lista colaboradores comerciais (ativos + inativos), excluindo status IA."""
        engine = get_db_engine(db_key="people_data", profile="reader")

        with engine.begin() as conn:
            result = conn.execute(text(colaborador_queries.SQL_LIST_COMERCIAIS_EXCETO_IA))
            rows = result.fetchall()
            return [
                ColaboradorModel(
                    id_col=row[0],
                    nome=row[1],
                    id_crm_colab=str(row[2]) if row[2] is not None else None,
                    status=row[3] if len(row) > 3 else None,
                )
                for row in rows
            ]
