from __future__ import annotations

from typing import Protocol, Optional

from .models import (
    ParceriaModel,
    SolucaoModel,
    SolucaoAtivaModel,
    LeadModel,
    LeadSummaryModel,
    ComercialModel,
    ComercialSolutionModel,
    IndicacaoStatsModel,
    ColaboradorModel,
    ContratoFinanceiroModel,
)


class ParceriasRepository(Protocol):
    def list_parceiros(self) -> list[ParceriaModel]:
        ...

    def activate_indicacao(self, parceiro_id: int, solucao_id: int = 1) -> dict[str, int]:
        ...

    def activate_comercial(self, parceiro_id: int, solution_ids: list[int]) -> dict[str, int]:
        ...

    def update_colab_comercial(self, parceiro_id: int, id_colab_comercial: str) -> int:
        ...

    def get_comercial_solutions(self, parceiro_id: int) -> list[ComercialSolutionModel]:
        ...

    def get_indicacao_stats(self, parceiro_id: int) -> IndicacaoStatsModel:
        ...

    def update_parceiro(self, id_comercial: int, nome: str, cnpj: Optional[str], razao_social: Optional[str]) -> int:
        ...

    def has_leads(self, id_comercial: int) -> bool:
        ...

    def delete_parceiro(self, id_comercial: int) -> int:
        ...


class SolucoesRepository(Protocol):
    def list_solucoes(self) -> list[SolucaoModel]:
        ...

    def list_solucoes_ativas(self) -> list[SolucaoAtivaModel]:
        ...

    def get_parceiros_by_solucao(self, id_solucao: int) -> list[str]:
        ...


class LeadsRepository(Protocol):
    def list_comercial_leads(self) -> list[LeadModel]:
        ...

    def list_comercial_leads_by_parceiro(self, id_comercial_parceiro: int) -> list[LeadModel]:
        ...

    def list_comercial_leads_by_comercial(self, id_comercial: int) -> list[LeadModel]:
        ...

    def get_leads_by_solucao(self, solucao_id: int) -> list[LeadSummaryModel]:
        ...

    def get_comercial_by_cnpj(self, cnpj_digits: str) -> Optional[ComercialModel]:
        ...

    def get_solucao_kanban_json(self, solucao_id: int) -> Optional[str]:
        ...

    def get_solucao_registro_info_json(self, solucao_id: int) -> Optional[str]:
        ...


class ColaboradoresRepository(Protocol):
    def get_nome_by_crm_id(self, id_crm_colab: str) -> Optional[str]:
        ...

    def get_nome_by_id_col(self, id_col: int) -> Optional[str]:
        ...

    def list_comerciais_ativos(self) -> list[ColaboradorModel]:
        ...


class FinanceiroRepository(Protocol):
    def save_contrato_financeiro(self, payload: ContratoFinanceiroModel) -> dict[str, int]:
        ...
