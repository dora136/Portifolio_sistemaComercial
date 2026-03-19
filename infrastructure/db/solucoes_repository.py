from __future__ import annotations
import json
from typing import Optional, List
from pydantic import ValidationError
from sqlalchemy import text

from database.db_provider import get_db_engine
from database.queries import solucao_queries
from domain.contracts import SolucoesRepository
from domain.models import SolucaoModel, SolucaoAtivaModel, KanbanEtapaModel, RegistroInfoFieldModel, ParceiroResumoModel
from domain.rules import parse_registro_info_json


class SolucoesRepositorySql(SolucoesRepository):
    
    def list_solucoes(self) -> list[SolucaoModel]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(text(solucao_queries.SQL_LIST_SOLUCOES)).mappings().all()

        result = []
        for row in rows:
            try:
                model = SolucaoModel.model_validate(
                    {
                        "id_solucao": row["id_solucao"],
                        "nome_solucao": row["nome_solucao"],
                        "tipo_solucao": row["tipo_solucao"],
                        "descricao": row["descricao"],
                        "aplicacoes_basicas": row["aplicacoes_basicas_json"],
                        "icon_id": row["icon_id"],
                        "color_id": row["color_id"],
                        "kanban_etapas": row["kanban_json"],
                        "n_parceiros": row["n_parceiros"],
                        "registro_info": row.get("registro_info_json"),
                    }
                )
            except ValidationError:
                continue
            result.append(model)

        return result

    def list_solucoes_ativas(self) -> list[SolucaoAtivaModel]:
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(text(solucao_queries.SQL_LIST_SOLUCOES_ATIVAS)).mappings().all()
            partners_rows = []
            try:
                partners_rows = conn.execute(
                    text(solucao_queries.SQL_LIST_PARCEIROS_BY_SOLUCOES)
                ).mappings().all()
            except Exception:
                partners_rows = []

        default_etapas = [
            {"id": 1, "nome_etapa": "Triagem", "color_HEX": "#626D84", "ativo": 1, "ordem_id": 1, "sucesso": 0, "perdido": 0},
            {"id": 2, "nome_etapa": "Reuniao", "color_HEX": "#2964D9", "ativo": 1, "ordem_id": 2, "sucesso": 0, "perdido": 0},
            {"id": 3, "nome_etapa": "Proposta", "color_HEX": "#F59F0A", "ativo": 1, "ordem_id": 3, "sucesso": 0, "perdido": 0},
            {"id": 4, "nome_etapa": "Fechamento", "color_HEX": "#16A249", "ativo": 1, "ordem_id": 4, "sucesso": 0, "perdido": 0},
        ]

        partners_by_solucao: dict[str, list[ParceiroResumoModel]] = {}

        for partner in partners_rows:
            solucao_id = partner.get("id_solucao")
            if not solucao_id:
                continue
            solucao_key = str(solucao_id)
            try:
                partners_by_solucao.setdefault(solucao_key, []).append(
                    ParceiroResumoModel(
                        id=partner.get("id"),
                        nome=partner.get("nome"),
                    )
                )
            except ValidationError:
                continue

        result: list[SolucaoAtivaModel] = []
        for row in rows:
            kanban_raw = row.get("kanban_json")
            etapas = None
            if kanban_raw:
                try:
                    parsed = json.loads(kanban_raw) if isinstance(kanban_raw, str) else kanban_raw
                    if isinstance(parsed, dict):
                        etapas = parsed.get("etapas", default_etapas)
                    elif isinstance(parsed, list):
                        etapas = parsed
                except (json.JSONDecodeError, TypeError):
                    etapas = default_etapas
            else:
                etapas = default_etapas

            etapa_models = []
            for etapa in etapas or []:
                if isinstance(etapa, KanbanEtapaModel):
                    etapa_models.append(etapa)
                elif isinstance(etapa, dict):
                    try:
                        etapa_models.append(KanbanEtapaModel.model_validate(etapa))
                    except ValidationError:
                        continue
            if not etapa_models:
                etapa_models = [
                    KanbanEtapaModel.model_validate(etapa)
                    for etapa in default_etapas
                ]

            registro_info = parse_registro_info_json(row.get("registro_info_json"))
            registro_models = [
                RegistroInfoFieldModel.model_validate(field)
                for field in registro_info
                if isinstance(field, dict)
            ]

            result.append(SolucaoAtivaModel(
                id=row["id_solucao"],
                name=row["nome_solucao"],
                type=row["tipo_solucao"],
                icon=row.get("icon_id") or "layers",
                color=row.get("color_id") or "primary",
                etapas=etapa_models,
                registroInfo=registro_models,
                partners=partners_by_solucao.get(str(row["id_solucao"]), []),
            ))

        return result

    def has_active_parceiros(self, solucao_id: int) -> bool:
        stmt = text(solucao_queries.SQL_CHECK_ACTIVE_PARCEIROS)
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            result = conn.execute(stmt, {"id_solucao": solucao_id}).first()
        return result is not None

    def delete_solucao(self, solucao_id: int) -> int:
        stmt = text(solucao_queries.SQL_DELETE_SOLUCAO)
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(stmt, {"id_solucao": solucao_id})
        return result.rowcount or 0

    def update_solucao(
        self,
        solucao_id: int,
        tipo_solucao: Optional[str],
        descricao: Optional[str],
        aplicacoes_basicas: List[str],
        icon_id: Optional[str] = None,
        color_id: Optional[str] = None,
        kanban_etapas: Optional[List[dict]] = None,
        registro_info: Optional[List[dict]] = None,
    ) -> int:
        payload_json = json.dumps(
            {"aplicacoes_basicas": aplicacoes_basicas},
            ensure_ascii=False,
        )
        kanban_json_str = None
        if kanban_etapas is not None:
            kanban_json_str = json.dumps(
                {"etapas": kanban_etapas},
                ensure_ascii=False,
            )
        registro_info_json_str = None
        if registro_info is not None:
            registro_info_json_str = json.dumps(
                registro_info,
                ensure_ascii=False,
            )
        stmt = text(solucao_queries.SQL_UPDATE_SOLUCAO)
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                stmt,
                {
                    "id_solucao": solucao_id,
                    "tipo_solucao": tipo_solucao,
                    "descricao": descricao,
                    "aplicacoes_basicas_json": payload_json,
                    "icon_id": icon_id or "component",
                    "color_id": color_id or "#5D8AA8",
                    "kanban_json": kanban_json_str,
                    "registro_info_json": registro_info_json_str,
                },
            )
        return result.rowcount or 0

    def create_solucao(
        self,
        nome_solucao: str,
        tipo_solucao: Optional[str],
        descricao: Optional[str],
        aplicacoes_basicas: List[str],
        icon_id: str = "component",
        color_id: str = "#5D8AA8",
        kanban_etapas: Optional[List[dict]] = None,
        registro_info: Optional[List[dict]] = None,
    ) -> int:
        payload_json = json.dumps(
            {"aplicacoes_basicas": aplicacoes_basicas},
            ensure_ascii=False,
        )
        # Kanban padrão se não informado
        if kanban_etapas is None:
            kanban_etapas = [
                {"id": 1, "nome_etapa": "Triagem", "color_HEX": "#626D84", "ativo": 1, "ordem_id": 1, "sucesso": 0, "perdido": 0},
                {"id": 2, "nome_etapa": "Reuniao", "color_HEX": "#2964D9", "ativo": 1, "ordem_id": 2, "sucesso": 0, "perdido": 0},
                {"id": 3, "nome_etapa": "Proposta", "color_HEX": "#F59F0A", "ativo": 1, "ordem_id": 3, "sucesso": 0, "perdido": 0},
                {"id": 4, "nome_etapa": "Fechamento", "color_HEX": "#16A249", "ativo": 1, "ordem_id": 4, "sucesso": 0, "perdido": 0},
            ]
        kanban_json_str = json.dumps(
            {"etapas": kanban_etapas},
            ensure_ascii=False,
        )
        registro_info_json_str = None
        if registro_info is not None:
            registro_info_json_str = json.dumps(
                registro_info,
                ensure_ascii=False,
            )
        stmt = text(solucao_queries.SQL_INSERT_SOLUCAO)
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                stmt,
                {
                    "nome_solucao": nome_solucao,
                    "tipo_solucao": tipo_solucao,
                    "descricao": descricao,
                    "aplicacoes_basicas_json": payload_json,
                    "icon_id": icon_id,
                    "color_id": color_id,
                    "kanban_json": kanban_json_str,
                    "registro_info_json": registro_info_json_str,
                },
            )
            new_id = result.scalar()
        return int(new_id) if new_id is not None else 0

    def update_solucao_kanban(self, solucao_id: int, kanban_etapas: List[dict]) -> int:
        kanban_json_str = json.dumps(
            {"etapas": kanban_etapas or []},
            ensure_ascii=False,
        )
        stmt = text(solucao_queries.SQL_UPDATE_SOLUCAO_KANBAN)
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.begin() as conn:
            result = conn.execute(
                stmt,
                {
                    "id_solucao": solucao_id,
                    "kanban_json": kanban_json_str,
                },
            )
        return result.rowcount or 0

    def get_parceiros_by_solucao(self, id_solucao: int) -> list[str]:
        """Retorna lista com os nomes dos parceiros ativos de uma solucao"""
        stmt = text(solucao_queries.SQL_GET_PARCEIROS_BY_SOLUCAO)
        engine = get_db_engine(db_key="app_data", profile="ddl")
        with engine.connect() as conn:
            rows = conn.execute(stmt, {"id_solucao": id_solucao}).mappings().all()
        return [row["nome"] for row in rows]
