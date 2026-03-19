import httpx
from typing import List, Optional
from .models import CrmLead, CrmCompany, CrmCompanyLead


class CrmClient:
    """Cliente HTTP para API do ExternalCRM."""

    def __init__(self, webhook_url: str, company_webhook_url: str = None, lead_webhook_url: str = None):
        self.webhook_url = webhook_url.rstrip("/")
        self.company_webhook_url = company_webhook_url.rstrip("/") if company_webhook_url else None
        self.lead_webhook_url = lead_webhook_url.rstrip("/") if lead_webhook_url else None
        self.client = httpx.AsyncClient(timeout=60.0)

    async def list_leads(self, query: Optional[str] = None) -> List[CrmLead]:
        """Lista TODOS os leads do ExternalCRM, buscando todas as páginas."""
        url = f"{self.webhook_url}/crm.lead.list.json"
        all_leads = []
        start = 0

        while True:
            params = {
                "select[]": ["ID", "TITLE", "ASSIGNED_BY_ID"],
                "start": start
            }

            if query:
                params["filter[%TITLE]"] = f"%{query}%"

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            result = data.get("result", [])
            if isinstance(result, dict):
                result = result.get("items", [])

            for item in result:
                lead = CrmLead(
                    id=int(item.get("ID", 0)),
                    title=item.get("TITLE", ""),
                    assigned_by_id=int(item["ASSIGNED_BY_ID"]) if item.get("ASSIGNED_BY_ID") else None
                )
                all_leads.append(lead)

            next_start = data.get("next")
            if next_start is not None:
                start = int(next_start)
                continue

            total = data.get("total")
            if total is not None and len(all_leads) < int(total):
                start = len(all_leads)
                continue

            break

        return all_leads

    async def get_lead(self, lead_id: int) -> Optional[CrmLead]:
        """Busca um lead específico pelo ID."""
        url = f"{self.webhook_url}/crm.lead.get.json"

        params = {"id": lead_id}

        response = await self.client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        result = data.get("result")

        if not result:
            return None

        return CrmLead(
            id=int(result.get("ID", 0)),
            title=result.get("TITLE", ""),
            assigned_by_id=int(result["ASSIGNED_BY_ID"]) if result.get("ASSIGNED_BY_ID") else None
        )

    async def search_company_by_cnpj(self, cnpj: str) -> Optional[CrmCompany]:
        """Busca empresa no ExternalCRM pelo CNPJ."""
        if not self.company_webhook_url:
            return None

        url = f"{self.company_webhook_url}/crm.company.list.json"
        digits = "".join(ch for ch in str(cnpj) if ch.isdigit())
        raiz = digits[:8]

        formatted_full = None
        if len(digits) == 14:
            formatted_full = f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"

        formatted_raiz = None
        if len(raiz) == 8:
            formatted_raiz = f"{raiz[0:2]}.{raiz[2:5]}.{raiz[5:8]}"

        select_fields = ["ID", "TITLE", "CUSTOM_FIELD_RAZAO_SOCIAL", "CUSTOM_FIELD_ID_COMERCIAL", "CUSTOM_FIELD_ENDERECO", "INDUSTRY"]
        filters = []

        if raiz:
            filters.append({"%CUSTOM_FIELD_CNPJ": raiz})
        if formatted_raiz:
            filters.append({"%CUSTOM_FIELD_CNPJ": formatted_raiz})
        if digits:
            filters.append({"=%CUSTOM_FIELD_CNPJ": digits})
        if formatted_full:
            filters.append({"=%CUSTOM_FIELD_CNPJ": formatted_full})

        result = []
        for filter_payload in filters:
            body = {"filter": filter_payload, "select": select_fields}
            response = await self.client.post(url, json=body)
            response.raise_for_status()
            data = response.json()
            result = data.get("result", [])
            if result:
                break

        if not result:
            return None

        item = result[0]
        return CrmCompany(
            id=int(item.get("ID", 0)),
            title=item.get("TITLE", ""),
            razao_social=item.get("CUSTOM_FIELD_RAZAO_SOCIAL"),
            id_comercial=item.get("CUSTOM_FIELD_ID_COMERCIAL"),
            endereco=item.get("CUSTOM_FIELD_ENDERECO"),
            id_segmento=item.get("INDUSTRY"),
            cnpj=cnpj,
        )

    async def list_leads_by_company(self, company_id: int) -> List[CrmCompanyLead]:
        """Lista leads associados a uma empresa pelo COMPANY_ID."""
        if not self.lead_webhook_url:
            return []

        url = f"{self.lead_webhook_url}/crm.lead.list.json"
        body = {
            "filter": {
                "COMPANY_ID": str(company_id)
            },
            "select": ["ID", "TITLE", "COMPANY_ID", "CUSTOM_FIELD_COLAB_COMERCIAL", "CUSTOM_FIELD_COLAB_SDR"]
        }

        response = await self.client.post(url, json=body)
        response.raise_for_status()

        data = response.json()
        result = data.get("result", [])
        if not result:
            return []

        leads = []
        for item in result:
            leads.append(CrmCompanyLead(
                id=int(item.get("ID", 0)),
                title=item.get("TITLE", ""),
                company_id=int(item["COMPANY_ID"]) if item.get("COMPANY_ID") else None,
                id_colab_comercial=item.get("CUSTOM_FIELD_COLAB_COMERCIAL"),
                id_colab_sdr=item.get("CUSTOM_FIELD_COLAB_SDR"),
            ))
        return leads

    async def create_company(self, payload: dict) -> Optional[int]:
        """Cria empresa no ExternalCRM (crm.company.add)."""
        if not self.company_webhook_url:
            return None

        url = f"{self.company_webhook_url}/crm.company.add.json"
        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        if data.get("error"):
            raise RuntimeError(data.get("error_description") or data.get("error"))

        result = data.get("result")
        if result is None:
            return None

        if isinstance(result, dict):
            result = result.get("ID") or result.get("id")

        try:
            return int(result)
        except (TypeError, ValueError):
            return None

    async def close(self):
        """Fecha o cliente HTTP."""
        await self.client.aclose()
