from typing import List, Optional
from .client import CrmClient
from .models import CrmLead, CnpjSearchResult


class CrmRepository:
    """Repository para operações com leads do ExternalCRM."""

    def __init__(self, client: CrmClient):
        self.client = client

    async def list_leads(self, query: Optional[str] = None) -> List[CrmLead]:
        """Lista leads, opcionalmente filtrando por título."""
        return await self.client.list_leads(query)

    async def get_lead(self, lead_id: int) -> Optional[CrmLead]:
        """Obtém um lead específico pelo ID."""
        return await self.client.get_lead(lead_id)

    async def search_by_cnpj(self, cnpj: str) -> CnpjSearchResult:
        """Busca empresa por CNPJ e seus leads associados."""
        company = await self.client.search_company_by_cnpj(cnpj)
        if not company:
            return CnpjSearchResult()

        leads = await self.client.list_leads_by_company(company.id)
        return CnpjSearchResult(company=company, leads=leads)

    async def create_company(self, payload: dict) -> Optional[int]:
        """Cria empresa no ExternalCRM."""
        return await self.client.create_company(payload)
