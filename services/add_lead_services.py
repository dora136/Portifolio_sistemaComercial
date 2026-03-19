"""
Servico de Cadastro e Ativacao de Leads/Parceiros (add_lead_services.py)

Responsavel pelo fluxo completo de cadastro de um novo registro comercial no Comercial.
O processo e dividido em duas fases principais:

  FASE 1 - Verificacao, Criacao e Sincronizacao com CRM
    1.1  Busca o registro comercial no banco pelo CNPJ.
    1.2  Se nao existir, cria o registro comercial no banco local [SQL].
    1.3  Se o registro nao tiver empresa vinculada no CRM, cria a company la.

  FASE 2 - Configuracao no Comercial (ativacao de modulos/solucoes)
    2.1  Se for parceiro: ativa modulos de Indicacao e/ou Comercial.
    2.2  Se for lead: valida duplicatas, resolve kanban e campos, e insere no pipeline.

Camadas utilizadas:
  - domain/models.py      -> ComercialModel (modelo do registro comercial)
  - domain/contracts.py   -> Protocolos dos repositories (LeadsRepository, ParceriasRepository, etc.)
  - infrastructure/db/    -> Implementacoes SQL dos repositories
  - infrastructure/external/crm/ -> Client e Repository para integracao ExternalCRM
  - utils/mapper.py       -> Mapeamento de nomes para IDs do CRM (segmento, etc.)
"""

import json
from typing import Optional

from config.config import settings
from domain.models import ComercialModel
from infrastructure.db.leads_repository import LeadsRepositorySql
from infrastructure.db.parceiros_repository import ParceirosRepositorySql
from infrastructure.db.colaboradores_repository import ColaboradoresRepositorySql
from infrastructure.external.crm import CrmClient, CrmRepository
from utils.mapper import mapper_b


class AddLeadService:
    """
    Orquestra o cadastro/ativacao de leads e parceiros no Comercial.

    Fluxo principal: processo_completo(payload)
      -> Valida/cria registro comercial no banco
      -> Sincroniza empresa com ExternalCRM
      -> Ativa modulos (parceiro) ou insere leads no kanban (lead)
    """

    # ------------------------------------------------------------------ #
    #  Repositorios (infra layer)                                         #
    # ------------------------------------------------------------------ #

    def _get_leads_repo(self) -> LeadsRepositorySql:
        """Retorna instancia do repositorio de leads (infrastructure/db)."""
        return LeadsRepositorySql()

    def _get_parceiros_repo(self) -> ParceirosRepositorySql:
        """Retorna instancia do repositorio de parceiros (infrastructure/db)."""
        return ParceirosRepositorySql()

    def _get_colab_repo(self) -> ColaboradoresRepositorySql:
        """Retorna instancia do repositorio de colaboradores (infrastructure/db)."""
        return ColaboradoresRepositorySql()

    # ------------------------------------------------------------------ #
    #  Resolucao de IDs de Colaboradores                                  #
    # ------------------------------------------------------------------ #

    def _resolve_colab_id(self, id_colab_comercial: Optional[str]) -> Optional[int]:
        """
        Converte o identificador do colaborador (pode ser id_crm ou id_col)
        para o id_col interno do banco.

        Estrategia:
          1. Tenta buscar no banco de colaboradores pelo id_crm.
          2. Se nao encontrar, assume que ja e um id_col numerico.
          3. Retorna None se o valor for vazio ou invalido.
        """
        if id_colab_comercial in (None, ""):
            return None

        # Tenta converter para int (caso ja seja id_col direto)
        try:
            id_col_candidate = int(id_colab_comercial)
        except (TypeError, ValueError):
            id_col_candidate = None

        colab_repo = self._get_colab_repo()

        # Busca no banco de colaboradores pelo id_crm
        try:
            id_col = colab_repo.get_id_col_by_crm_id(str(id_colab_comercial))
        except Exception:
            id_col = None

        # Se nao encontrou por id_crm, tenta resolver por nome
        if id_col is None:
            try:
                id_col = colab_repo.get_id_col_by_nome(str(id_colab_comercial))
            except Exception:
                id_col = None

        # Prioriza o resultado do banco; fallback para o candidato numerico
        return id_col if id_col is not None else id_col_candidate

    def _resolve_crm_colab_id(self, id_colab_comercial: Optional[str]) -> Optional[str]:
        """
        Converte o identificador do colaborador para o id_crm_colab
        necessario para o campo ASSIGNED_BY_ID da CRM.

        Estrategia:
          1. Se for numerico, busca o id_crm pelo id_col no banco.
          2. Se for nome, busca o id_crm pelo nome.
          3. Se nao encontrar, retorna None para evitar gravar valor invalido.
        """
        if id_colab_comercial in (None, ""):
            return None

        colab_repo = self._get_colab_repo()

        # Tenta interpretar como id_col numerico para buscar o crm_id
        try:
            id_col = int(id_colab_comercial)
        except (TypeError, ValueError):
            # Nao e numerico: pode ser nome do colaborador ou id_crm em string
            try:
                crm_id = colab_repo.get_crm_id_by_nome(str(id_colab_comercial))
            except Exception:
                crm_id = None
            return str(crm_id) if crm_id not in (None, "") else None

        # Busca o id_crm_colab correspondente ao id_col
        try:
            crm_id = colab_repo.get_crm_id_by_id_col(id_col)
        except Exception:
            crm_id = None

        # Para manter compatibilidade, se o input numerico ja for o crm_id,
        # usa o proprio numero; caso contrario retorna None.
        if crm_id not in (None, ""):
            return str(crm_id)
        return str(id_colab_comercial) if str(id_colab_comercial).isdigit() else None

    # ------------------------------------------------------------------ #
    #  Construcao do Payload CRM (Company)                             #
    # ------------------------------------------------------------------ #

    def _build_crm_company_payload(self, lead_payload, db_row: Optional[ComercialModel]) -> dict:
        """
        Monta o dicionario de campos para criar uma Company no ExternalCRM.

        Campos mapeados:
          - TITLE            -> nome fantasia
          - COMPANY_TYPE     -> "PARTNER" ou "CUSTOMER" conforme lead_type
          - CUSTOM_FIELD_*    -> campos customizados (razao social, cnpj, id_empresa)
          - ASSIGNED_BY_ID   -> responsavel (colaborador convertido para id_crm)
          - INDUSTRY         -> segmento (convertido via mapper_b)
        """
        # Extrai dados do payload, com fallback para o registro do banco
        nome = self._as_optional_string(getattr(lead_payload, "nome", None)) or self._as_optional_string(getattr(db_row, "nome", None))
        razao_social = getattr(lead_payload, "razao_social", None) or getattr(db_row, "razao_social", None)
        cnpj = getattr(lead_payload, "cnpj", None) or getattr(db_row, "cnpj", None)
        segmento = getattr(lead_payload, "segmento", None)

        # Determina tipo: parceiro vira PARTNER, qualquer outro vira CUSTOMER
        lead_type = getattr(lead_payload, "lead_type", None) or "parceiro"
        lead_type_norm = str(lead_type).strip().lower()
        company_type = "PARTNER" if lead_type_norm in {"parceiro", "partner"} else "CUSTOMER"

        # Resolve o responsavel para o formato esperado pela CRM
        id_colab_comercial = getattr(lead_payload, "id_colab_comercial", None) or getattr(lead_payload, "id_colab_comercial", None)
        assigned_by_id = self._resolve_crm_colab_id(id_colab_comercial)

        # ID interno do registro comercial no nosso banco
        id_empresa = getattr(db_row, "id", None) if db_row else None

        # Converte nome do segmento para o ID do CRM via mapper
        id_segmento = None
        if segmento:
            mapped_segmento = mapper_b.name_to_id(segmento, "segmento")
            id_segmento = mapped_segmento or segmento

        return {
            "fields": {
                "TITLE": nome,                              # Nome fantasia da empresa
                "COMPANY_TYPE": company_type,               # PARTNER ou CUSTOMER
                "CUSTOM_FIELD_RAZAO_SOCIAL": razao_social,       # Campo custom: razao social
                "CUSTOM_FIELD_CNPJ": cnpj,               # Campo custom: CNPJ
                "ASSIGNED_BY_ID": assigned_by_id,           # Responsavel (id_crm)
                "CUSTOM_FIELD_ID_COMERCIAL": id_empresa,         # Campo custom: id no banco Comercial
                "CUSTOM_FIELD_COUNTER_1": 0,                  # Contador inicial (reservado)
                "CUSTOM_FIELD_COUNTER_2": 0,                  # Contador inicial (reservado)
                "INDUSTRY": id_segmento,                    # Segmento/industria
            }
        }

    # ------------------------------------------------------------------ #
    #  Integracao CRM: criacao de Company                              #
    # ------------------------------------------------------------------ #

    async def _create_crm_company(self, payload: dict) -> Optional[int]:
        """
        Cria uma Company no ExternalCRM via API.

        Valida que as URLs de webhook estao configuradas antes de chamar.
        Retorna o ID da company criada ou None se falhar.
        O client HTTP e fechado no finally para evitar leak de conexao.
        """
        # Validacao de configuracao obrigatoria
        if not settings.CRM_COMPANY_WEBHOOK_URL:
            raise ValueError("CRM_COMPANY_WEBHOOK_URL nao configurada")
        if not settings.CRM_WEBHOOK_URL:
            raise ValueError("CRM_WEBHOOK_URL nao configurada")

        # Instancia o client e o repository da CRM (infrastructure/external)
        client = CrmClient(
            webhook_url=settings.CRM_WEBHOOK_URL,
            company_webhook_url=settings.CRM_COMPANY_WEBHOOK_URL,
            lead_webhook_url=settings.CRM_LEAD_WEBHOOK_URL,
        )
        repository = CrmRepository(client)
        try:
            return await repository.create_company(payload)
        finally:
            # Garante fechamento do client HTTPX mesmo em caso de erro
            await client.close()

    # ------------------------------------------------------------------ #
    #  Helpers de resposta                                                #
    # ------------------------------------------------------------------ #

    def _with_crm_context(self, response: dict, crm_context: Optional[dict]) -> dict:
        """
        Anexa informacoes do CRM (ex: company_id) na resposta,
        caso uma company tenha sido criada durante o fluxo.
        """
        if crm_context:
            response["crm_company"] = crm_context
        return response

    # ------------------------------------------------------------------ #
    #  Helpers de Kanban                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_first_kanban_id(kanban_json, default_etapa: int = 1) -> int:
        """
        Extrai o ID da primeira etapa do kanban de uma solucao.

        O kanban_json pode vir como:
          - String JSON com formato {"etapas": [{"id": 1, ...}, ...]}
          - String JSON com formato de lista [{"id": 1, ...}, ...]
          - Objeto dict/list ja parseado

        Retorna default_etapa se nao conseguir extrair.
        """
        if not kanban_json:
            return default_etapa

        # Parse do JSON se necessario
        try:
            parsed = json.loads(kanban_json) if isinstance(kanban_json, str) else kanban_json
        except (TypeError, ValueError):
            return default_etapa

        # Extrai a lista de etapas (pode estar em "etapas" ou ser a propria lista)
        etapas = None
        if isinstance(parsed, dict):
            etapas = parsed.get("etapas")
        elif isinstance(parsed, list):
            etapas = parsed

        if not etapas:
            return default_etapa

        # Pega o ID da primeira etapa
        first = etapas[0]
        if isinstance(first, dict) and first.get("id") is not None:
            try:
                return int(first.get("id"))
            except (TypeError, ValueError):
                return first.get("id")

        return default_etapa

    @staticmethod
    def _parse_registro_fields(registro_raw) -> list[dict]:
        """
        Extrai os campos de registro (informacoes adicionais) de uma solucao.

        O registro_info_json pode vir como:
          - String JSON com formato {"fields": [{"name": ..., "type": ..., "value": ...}]}
          - String JSON com formato de lista direta
          - Objeto dict/list ja parseado

        Retorna lista de dicts com keys: name, type, value.
        """
        if not registro_raw:
            return []

        try:
            parsed = json.loads(registro_raw) if isinstance(registro_raw, str) else registro_raw
        except (TypeError, ValueError):
            return []

        # Se for dict, extrai "fields"; se for lista, usa direto
        if isinstance(parsed, dict):
            parsed = parsed.get("fields", [])

        if not isinstance(parsed, list):
            return []

        # Normaliza cada campo garantindo as 3 chaves esperadas
        fields = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            fields.append({
                "name": item.get("name") or "",
                "type": item.get("type") or "string",
                "value": item.get("value"),
            })

        return fields

    # ------------------------------------------------------------------ #
    #  Normalizacao de solution_ids                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _normalize_solution_ids(raw_ids) -> list[int]:
        """
        Converte a lista de solution_ids do payload em inteiros unicos,
        preservando a ordem original e removendo valores invalidos.
        """
        raw = raw_ids or []
        valid = []
        for value in raw:
            try:
                valid.append(int(value))
            except (TypeError, ValueError):
                continue
        # Remove duplicatas preservando ordem
        return [int(sol_id) for sol_id in dict.fromkeys(valid)]

    # ------------------------------------------------------------------ #
    #  FASE 1 — Verificacao/Criacao do registro comercial + CRM        #
    # ------------------------------------------------------------------ #

    async def _ensure_comercial_and_crm(
        self, payload, leads_repo: LeadsRepositorySql
    ) -> tuple[Optional[ComercialModel], Optional[dict], Optional[dict]]:
        """
        Garante que o registro comercial existe no banco e no CRM.

        Retorna uma tupla com:
          - db_row: ComercialModel do registro (ou None se falhou)
          - db_payload: dict com os dados do registro (para resposta da API)
          - crm_context: dict com company_id do CRM (ou None se ja existia)

        Fluxo:
          1. Busca pelo CNPJ no banco local.
          2. Se nao existe, cria um novo registro comercial.
          3. Se o registro nao tem id_crm_emp, cria a company no CRM.
          4. Atualiza o banco com o id_crm_emp retornado.
        """
        # --- 1. Busca registro comercial pelo CNPJ ---
        cnpj = getattr(payload, "cnpj", None)
        cnpj_digits = "".join(ch for ch in str(cnpj) if ch.isdigit()) if cnpj else ""
        db_row = leads_repo.get_comercial_by_cnpj(cnpj_digits) if cnpj_digits else None
        crm_context = None

        # --- 2. Se nao existe, cria no banco local ---
        if not db_row:
            # Resolve o tipo comercial (PARTNER ou CUSTOMER)
            lead_type = getattr(payload, "lead_type", None) or "parceiro"
            lead_type_norm = str(lead_type).strip().lower()
            tipo_comercial = "PARTNER" if lead_type_norm in {"parceiro", "partner"} else "CUSTOMER"

            # Resolve o id_col do colaborador responsavel
            id_colab_comercial_raw = getattr(payload, "id_colab_comercial", None)
            id_colab_comercial = getattr(payload, "id_colab_comercial", None)
            # Comercial vem do select; se não vier, faz fallback para o representante Comercial
            id_colab_comercial = self._resolve_colab_id(id_colab_comercial_raw or id_colab_comercial)

            # Insere o novo registro comercial
            created_id = leads_repo.create_comercial(
                nome=self._as_optional_string(getattr(payload, "nome", None)),
                tipo_comercial=tipo_comercial,
                cnpj=cnpj_digits or None,
                razao_social=getattr(payload, "razao_social", None),
                segmento=getattr(payload, "segmento", None),
                id_colab_comercial=id_colab_comercial,
                origem="Base_Demo",
            )

            if not created_id:
                return None, None, None

            # Recarrega o registro recem-criado
            db_row = leads_repo.get_comercial_by_id(created_id)
            if not db_row:
                return None, None, None

        # --- 3. Se nao tem empresa vinculada no CRM, cria ---
        has_crm = bool(
            getattr(db_row, "id_crm_emp", None) or getattr(db_row, "id_crm_lead", None)
        )

        if not has_crm:
            crm_payload = self._build_crm_company_payload(payload, db_row)
            crm_company_id = await self._create_crm_company(crm_payload)

            if crm_company_id:
                # Atualiza o banco local com o id da company criada no CRM
                leads_repo.update_crm_company_id(db_row.id, crm_company_id)
                crm_context = {"company_id": crm_company_id}

        db_payload = db_row.model_dump() if db_row else None
        if db_payload and crm_context:
            db_payload["id_crm_emp"] = crm_context["company_id"]

        # Garante persistencia do comercial selecionado mesmo quando o CNPJ ja existe.
        id_colab_comercial_raw = getattr(payload, "id_colab_comercial", None)
        id_colab_comercial = getattr(payload, "id_colab_comercial", None)
        id_colab_comercial = self._resolve_colab_id(id_colab_comercial_raw or id_colab_comercial)
        if id_colab_comercial is not None:
            leads_repo.update_comercial_responsavel(db_row.id, id_colab_comercial)

        return db_row, db_payload, crm_context

    # ------------------------------------------------------------------ #
    #  FASE 2a — Processamento de Parceiro                                #
    # ------------------------------------------------------------------ #

    def _process_parceiro(
        self, db_row: ComercialModel, db_payload: dict,
        unique_solution_ids: list[int], id_colab_comercial: Optional[str],
        crm_context: Optional[dict],
    ) -> dict:
        """
        Ativa modulos de parceria (Indicacao e/ou Comercial) para o registro.

        Regras:
          - solution_id == 1 -> modulo Indicacao (encaminhamento de leads)
          - solution_id >= 2 -> modulos Comercial (solucoes especificas)
          - Se id_colab_comercial informado, atualiza o colaborador responsavel.
        """
        if not unique_solution_ids:
            return self._with_crm_context({
                "phase": "2.0",
                "status": "parceiro_sem_solucao",
                "next_step": "ignorado",
                "db_row": db_payload,
                "updated": 1,
            }, crm_context)

        # Separa IDs de indicacao (solucao 1) dos IDs de Comercial (solucao >= 2)
        indicacao_ids = [sol_id for sol_id in unique_solution_ids if sol_id == 1]
        comercial_ids = [sol_id for sol_id in unique_solution_ids if sol_id >= 2]

        parceria_repo = self._get_parceiros_repo()
        result = {"indicacao": None, "comercial": None}

        # Ativa modulo de Indicacao se solucao 1 foi selecionada
        if indicacao_ids:
            result["indicacao"] = parceria_repo.activate_indicacao(db_row.id, solucao_id=1)

        # Ativa modulo Comercial com as solucoes selecionadas (>= 2)
        if comercial_ids:
            result["comercial"] = parceria_repo.activate_comercial(db_row.id, comercial_ids)

        # Atualiza o colaborador responsavel pela parceria, se informado
        if id_colab_comercial:
            result["colab_comercial"] = parceria_repo.update_colab_comercial(db_row.id, str(id_colab_comercial))

        return self._with_crm_context({
            "phase": "2.0",
            "status": "parceiro_processado",
            "next_step": "2.1",
            "db_row": db_payload,
            "result": result,
            "updated": 1,
        }, crm_context)

    # ------------------------------------------------------------------ #
    #  FASE 2b — Processamento de Lead                                    #
    # ------------------------------------------------------------------ #

    def _process_lead(
        self, db_row: ComercialModel, db_payload: dict,
        unique_solution_ids: list[int], id_colab_comercial: Optional[str],
        crm_context: Optional[dict], leads_repo: LeadsRepositorySql,
    ) -> dict:
        """
        Insere o lead no pipeline Comercial (kanban) para cada solucao selecionada.

        Fluxo:
          1. Verifica quais solucoes ja tem lead cadastrado (duplicatas).
          2. Para cada solucao pendente, resolve a etapa inicial do kanban.
          3. Carrega os campos de registro (informacoes) da solucao.
          4. Cria os registros de lead no kanban via repository.

        Retorna dict com status e detalhes do processamento.
        """
        # --- Validacao: tipo nao suportado ---
        if not unique_solution_ids:
            return self._with_crm_context({
                "phase": "2.0",
                "status": "lead_sem_solucao",
                "next_step": "ignorado",
                "db_row": db_payload,
                "updated": 1,
            }, crm_context)

        # --- Verificacao de duplicatas ---
        # Busca quais solucoes ja possuem lead cadastrado para este comercial
        existing_solution_ids = set()
        try:
            existing_solution_ids = set(leads_repo.get_lead_solution_ids(db_row.id))
        except Exception:
            existing_solution_ids = set()

        duplicate_solution_ids = [
            sol_id for sol_id in unique_solution_ids if sol_id in existing_solution_ids
        ]
        pending_solution_ids = [
            sol_id for sol_id in unique_solution_ids if sol_id not in existing_solution_ids
        ]

        # Se todas as solucoes ja tem lead cadastrado, retorna duplicata
        if not pending_solution_ids:
            return self._with_crm_context({
                "phase": "2.0",
                "status": "lead_duplicado",
                "next_step": "ignorado",
                "db_row": db_payload,
                "duplicate_solution_ids": duplicate_solution_ids,
                "updated": 1,
            }, crm_context)

        # --- Montagem dos registros de lead por solucao ---
        lead_rows = []
        for sol_id in pending_solution_ids:
            # Resolve a etapa inicial do kanban desta solucao
            kanban_json = leads_repo.get_solucao_kanban_json(sol_id)
            id_etapa_kanban = self._get_first_kanban_id(kanban_json, default_etapa=1)

            # Carrega os campos de registro (informacoes adicionais) da solucao
            registro_raw = leads_repo.get_solucao_registro_info_json(sol_id)
            registro_fields = self._parse_registro_fields(registro_raw)
            registro_json = json.dumps(registro_fields, ensure_ascii=False)

            # Monta a linha do lead para inserir no kanban
            lead_rows.append({
                "id_comercial": db_row.id,         # FK para o registro comercial
                "id_solucao": sol_id,               # FK para a solucao
                "id_etapa_kanban": id_etapa_kanban, # Etapa inicial no kanban
                "informacoes_json": registro_json,  # Campos de registro em JSON
                "id_colab_comercial": id_colab_comercial,   # Colaborador responsavel
            })

        # --- Insere os leads no kanban e na tabela M2M ---
        result = leads_repo.create_lead_kanban(db_row.id, lead_rows, pending_solution_ids)

        return self._with_crm_context({
            "phase": "2.0",
            "status": "lead_processado",
            "next_step": "2.1",
            "db_row": db_payload,
            "result": result,
            "duplicate_solution_ids": duplicate_solution_ids,
            "updated": 1,
        }, crm_context)

    # ================================================================== #
    #  FLUXO PRINCIPAL                                                    #
    # ================================================================== #

    async def processo_completo(self, lead_create_payload) -> dict:
        """
        Executa o fluxo completo de cadastro/ativacao.

        Parametros:
          lead_create_payload: objeto com os dados do formulario
            (LeadCreatePayload definido em routes/home_router.py)

        Retorno:
          dict com phase, status, next_step, db_row, updated e detalhes extras.

        Fases:
          FASE 1 -> Garante registro no banco + sincroniza CRM.
          FASE 2 -> Processa como parceiro OU como lead, conforme lead_type.
        """
        leads_repo = self._get_leads_repo()

        # ============================================================== #
        #  FASE 1: Verificacao/Criacao do registro comercial + CRM     #
        # ============================================================== #
        db_row, db_payload, crm_context = await self._ensure_comercial_and_crm(
            lead_create_payload, leads_repo
        )

        # Se nao conseguiu criar/encontrar o registro, retorna erro
        if not db_row:
            return {
                "phase": "1.1",
                "status": "sem_banco",
                "next_step": "1.2",
                "db_row": None,
                "updated": 0,
            }

        # ============================================================== #
        #  FASE 2: Configuracao no Comercial (parceiro ou lead)               #
        # ============================================================== #

        # Extrai dados comuns do payload
        lead_type = getattr(lead_create_payload, "lead_type", None) or "parceiro"
        id_colab_comercial_raw = (
            getattr(lead_create_payload, "id_colab_comercial", None)
            or getattr(lead_create_payload, "id_colab_comercial", None)
        )
        id_colab_comercial = self._resolve_crm_colab_id(id_colab_comercial_raw)

        # Normaliza e deduplica os IDs de solucoes selecionadas
        raw_solution_ids = getattr(lead_create_payload, "solution_ids", [])
        unique_solution_ids = self._normalize_solution_ids(raw_solution_ids)

        # --- PARCEIRO: ativa modulos de Indicacao e/ou Comercial ---
        if lead_type == "parceiro":
            return self._process_parceiro(
                db_row, db_payload, unique_solution_ids,
                id_colab_comercial, crm_context,
            )

        # --- LEAD: insere no pipeline/kanban ---
        if lead_type == "lead":
            return self._process_lead(
                db_row, db_payload, unique_solution_ids,
                id_colab_comercial, crm_context, leads_repo,
            )

        # --- TIPO NAO SUPORTADO ---
        return self._with_crm_context({
            "phase": "2.0",
            "status": "tipo_nao_suportado",
            "next_step": "ignorado",
            "db_row": db_payload,
            "updated": 1,
        }, crm_context)
    @staticmethod
    def _as_optional_string(value: Optional[object]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
