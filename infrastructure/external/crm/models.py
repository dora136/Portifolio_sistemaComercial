from pydantic import BaseModel
from typing import Optional, List


class CrmLead(BaseModel):
    """Modelo para Lead do ExternalCRM."""
    id: int
    title: str
    assigned_by_id: Optional[int] = None


class CrmCompany(BaseModel):
    """Modelo para Company do ExternalCRM."""
    id: int
    title: str
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    id_comercial: Optional[str] = None
    endereco: Optional[str] = None
    id_segmento: Optional[str] = None


class CrmCompanyLead(BaseModel):
    """Modelo para Lead associado a uma Company."""
    id: int
    title: str
    company_id: Optional[int] = None
    id_colab_comercial: Optional[str] = None
    id_colab_sdr: Optional[str] = None


class CnpjSearchResult(BaseModel):
    """Resultado da pesquisa de CNPJ."""
    company: Optional[CrmCompany] = None
    leads: List[CrmCompanyLead] = []
