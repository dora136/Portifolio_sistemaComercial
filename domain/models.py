from __future__ import annotations

from typing import Optional, Any

from pydantic import BaseModel, Field, field_validator

from .rules import normalize_cnpj, normalize_date, parse_aplicacoes_json, parse_bool, parse_kanban_json, parse_registro_info_json


class ParceriaModel(BaseModel):
    id: int
    nome: str
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    estado: Optional[str] = None
    id_crm_lead: Optional[int] = None
    id_colab_comercial: Optional[int] = None
    fol_path: Optional[str] = None
    data_criacao: Optional[str] = None
    modulo_comercial: Optional[bool] = None
    status_comercial: Optional[str] = None
    modulo_indicacao: Optional[bool] = None
    status_indicacao: Optional[str] = None

    @field_validator("modulo_comercial", "modulo_indicacao", mode="before")
    @classmethod
    def validate_modulos(cls, value):
        return parse_bool(value)

    @field_validator("data_criacao", mode="before")
    @classmethod
    def validate_data_criacao(cls, value):
        return normalize_date(value)

    @field_validator("cnpj", mode="before")
    @classmethod
    def validate_cnpj(cls, value):
        return normalize_cnpj(value)


class SolucaoModel(BaseModel):
    id_solucao: int
    nome_solucao: str
    tipo_solucao: Optional[str] = None
    descricao: Optional[str] = None
    icon_id: Optional[str] = None
    color_id: Optional[str] = None
    n_parceiros: Optional[int] = None
    aplicacoes_basicas: list[str] = Field(default_factory=list)
    kanban_etapas: Optional[list[dict]] = None
    registro_info: list[dict] = Field(default_factory=list)

    @field_validator("aplicacoes_basicas", mode="before")
    @classmethod
    def validate_aplicacoes_basicas(cls, value):
        return parse_aplicacoes_json(value)

    @field_validator("kanban_etapas", mode="before")
    @classmethod
    def validate_kanban_etapas(cls, value):
        return parse_kanban_json(value)

    @field_validator("registro_info", mode="before")
    @classmethod
    def validate_registro_info(cls, value):
        return parse_registro_info_json(value)


class LeadInfoFieldModel(BaseModel):
    name: str = ""
    type: str = "string"
    value: Optional[Any] = None


class LeadModel(BaseModel):
    id: str
    id_comercial: int
    id_solucao: int
    id_etapa: int = 1
    name: str
    company: Optional[str] = None
    nome_fantasia: Optional[str] = None
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None
    id_colab_comercial: Optional[int] = None
    colab_comercial_nome: Optional[str] = None
    comercial_nome: Optional[str] = None
    id_comercial_parceiro: Optional[int] = None
    representante_parceiro_nome: Optional[str] = None
    informacoes: list[LeadInfoFieldModel] = Field(default_factory=list)
    lastAction: Optional[str] = None
    createdAt: Optional[str] = None
    email: Optional[str] = None


class LeadSummaryModel(BaseModel):
    id_comercial: int
    name: str


class ComercialModel(BaseModel):
    id: int
    nome: str
    id_crm_lead: Optional[int] = None
    id_crm_emp: Optional[int] = None
    cnpj: Optional[str] = None


class KanbanEtapaModel(BaseModel):
    id: int
    nome_etapa: str
    color_HEX: str = "#626D84"
    ativo: Optional[bool] = True
    ordem_id: Optional[int] = None
    sucesso: Optional[bool] = False
    perdido: Optional[bool] = False

    @field_validator("ativo", "sucesso", "perdido", mode="before")
    @classmethod
    def validate_flags(cls, value):
        parsed = parse_bool(value)
        if parsed is None:
            return None
        return parsed


class RegistroInfoFieldModel(BaseModel):
    name: str = ""
    type: str = "string"
    value: Optional[Any] = None


class ParceiroResumoModel(BaseModel):
    id: int
    nome: str


class SolucaoAtivaModel(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    icon: str = "layers"
    color: str = "primary"
    etapas: list[KanbanEtapaModel] = Field(default_factory=list)
    registroInfo: list[RegistroInfoFieldModel] = Field(default_factory=list)
    partners: list[ParceiroResumoModel] = Field(default_factory=list)


class ComercialSolutionModel(BaseModel):
    id: int
    name: str
    icon: str = "layers"
    color: str = "primary"
    status: str = "active"
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    closedLeads: int = 0
    leadsGenerated: int = 0
    leadsNegotiation: int = 0


class IndicacaoStatsModel(BaseModel):
    leadsGenerated: int = 0
    leadsNegotiation: int = 0
    leadsClosed: int = 0
    conversionRate: int = 0


class ColaboradorModel(BaseModel):
    id_col: int
    nome: str
    id_crm_colab: Optional[str] = None
    status: Optional[str] = None


class ParcelaFinanceiroModel(BaseModel):
    referencia_esperado: Optional[str] = None
    referencia_real: Optional[str] = None
    valor_esperado: Optional[float] = None
    valor_real: Optional[float] = None


class ContratoFinanceiroModel(BaseModel):
    id_contrato: Optional[int] = None
    id_comercial_lead: int
    id_solucao: int
    id_comercial_parceiro: int
    id_responsavel: Optional[int] = None
    status: Optional[str] = None
    num_parcelas: Optional[int] = None
    infos_json: dict[str, Any] = Field(default_factory=dict)
    parcelas: list[ParcelaFinanceiroModel] = Field(default_factory=list)
