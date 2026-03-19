"""
Configuração do DB Provider usando Pydantic BaseSettings

FLEXÍVEL POR PROJETO:
- Defina apenas as variáveis que seu projeto precisa
- Toda lógica está no db_provider.py (não precisa copiar)
- Basta configurar as variáveis e pronto!
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from config.env import BASE_DIR


def _find_env_file() -> str:
    """
    Retorna o caminho para o arquivo .env usando BASE_DIR do config.env

    Returns:
        Caminho absoluto para o arquivo .env
    """
    return str(BASE_DIR / ".env")


class Settings(BaseSettings):
    """
    Configurações do projeto - APENAS variáveis!
   
    Como usar:
    1. Defina DB_SERVER (obrigatório)
    2. Defina DB_DATABASE_* para bancos que você usa
    3. Defina DB_*_*_UID e DB_*_*_PWD para perfis que você usa
    4. Pronto! O db_provider faz o resto.
    """
   
    # =========================================================================
    # CONFIGURAÇÃO DO PYDANTIC
    # =========================================================================
   
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),  # Busca .env de forma flexível
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )
    
    # =========================================================================
    # SERVIDOR E DRIVER (OBRIGATÓRIO)
    # =========================================================================
    
    DB_SERVER: Optional[str] = Field(default=None, description="Servidor SQL Server")
    DB_DRIVER3: str = Field(default="ODBC Driver 18 for SQL Server")
    PORTFOLIO_DEMO_MODE: bool = Field(default=True, description="Executa a aplicacao em modo demo sem conexao com banco")
    
    # =========================================================================
    # NOMES DOS BANCOS
    # Defina apenas os que seu projeto usa! Delete os que não usa.
    # =========================================================================
    
    DB_DATABASE_CORE: Optional[str] = Field(default=None)
    DB_DATABASE_ADM: Optional[str] = Field(default=None)
    DB_DATABASE_GESTAO: Optional[str] = Field(default=None)
    DB_DATABASE_SECURE: Optional[str] = Field(default=None)
    DB_DATABASE_DEV: Optional[str] = Field(default=None)
    
    
    # =========================================================================
    # CREDENCIAIS - ADM
    # =========================================================================
    
    DB_ADM_READER_UID: Optional[str] = Field(default=None)
    DB_ADM_READER_PWD: Optional[str] = Field(default=None)
    
    # =========================================================================
    # CREDENCIAIS - GESTAO
    # =========================================================================
    
    DB_GST_DDL_UID: Optional[str] = Field(default=None)
    DB_GST_DDL_PWD: Optional[str] = Field(default=None)
    DB_GST_WRITER_UID: Optional[str] = Field(default=None)
    DB_GST_WRITER_PWD: Optional[str] = Field(default=None)

    # =========================================================================
    # CREDENCIAIS - SECURE
    # =========================================================================

    DB_SECURE_READER_UID: Optional[str] = Field(default=None)
    DB_SECURE_READER_PWD: Optional[str] = Field(default=None)
    DB_SECURE_DDL_UID: Optional[str] = Field(default=None)
    DB_SECURE_DDL_PWD: Optional[str] = Field(default=None)

    # =========================================================================
    # CREDENCIAIS - DEV
    # =========================================================================

    DB_DEV_READER_UID: Optional[str] = Field(default=None)
    DB_DEV_READER_PWD: Optional[str] = Field(default=None)
    DB_DEV_WRITER_UID: Optional[str] = Field(default=None)
    DB_DEV_WRITER_PWD: Optional[str] = Field(default=None)
    DB_DEV_DDL_UID: Optional[str] = Field(default=None)
    DB_DEV_DDL_PWD: Optional[str] = Field(default=None)

    # =========================================================================
    # CRM EXTERNO API
    # =========================================================================

    CRM_WEBHOOK_URL: Optional[str] = Field(default=None, description="URL do webhook do CRM externo")
    CRM_COMPANY_WEBHOOK_URL: Optional[str] = Field(default=None, description="URL do webhook do CRM externo para empresas")
    CRM_LEAD_WEBHOOK_URL: Optional[str] = Field(default=None, description="URL do webhook do CRM externo para leads")

    # =========================================================================
    # PORTAL PRINCIPAL
    # =========================================================================

    PORTAL_URL: Optional[str] = Field(default=None, description="URL do portal principal")

    # =========================================================================
    # E-MAIL (SMTP)
    # =========================================================================

    SMTP_HOST: Optional[str] = Field(default=None, description="Servidor SMTP")
    SMTP_PORT: int = Field(default=587, description="Porta SMTP")
    SMTP_USER: Optional[str] = Field(default=None, description="Usuario SMTP")
    SMTP_PASS: Optional[str] = Field(default=None, description="Senha SMTP")
    SMTP_FROM: Optional[str] = Field(default=None, description="Remetente padrao")
    SMTP_USE_TLS: bool = Field(default=True, description="Usar STARTTLS")
    FINANCE_EMAIL_TO: Optional[str] = Field(default="financeiro@demo.local", description="Destinatario padrao financeiro")
    SMTP_CRED_TARGET: Optional[str] = Field(default="APP_SMTP", description="Target da credencial SMTP no Windows Credential Manager")
    MAIL_LOGIN: Optional[str] = Field(default=None, description="Alias de SMTP_USER")
    MAIL_PWD: Optional[str] = Field(default=None, description="Alias de SMTP_PASS")

    # Compatibilidade com typo comum em .env (SMPT_*)
    SMPT_HOST: Optional[str] = Field(default=None)
    SMPT_PORT: Optional[int] = Field(default=None)
    SMPT_USER: Optional[str] = Field(default=None)
    SMPT_PASS: Optional[str] = Field(default=None)
    SMPT_FROM: Optional[str] = Field(default=None)
    SMPT_USE_TLS: Optional[bool] = Field(default=None)

    # =========================================================================
    # E-MAIL (MICROSOFT GRAPH API)
    # =========================================================================

    MAIL_TENANT_ID: Optional[str] = Field(default=None, description="Tenant ID do Azure AD para Graph")
    MAIL_CLIENT_ID: Optional[str] = Field(default=None, description="Client ID da aplicacao Graph")
    MAIL_CLIENT_SECRET: Optional[str] = Field(default=None, description="Client Secret da aplicacao Graph")
    MAIL_SENDER_ADDRESS: Optional[str] = Field(default=None, description="Endereco do remetente no Graph")
    TARGET_TEST_MAIL: Optional[str] = Field(default=None, description="Endereco de teste para ambiente dev")

    # Compatibilidade com convencao usada em outro sistema
    GRAPH_TENANT_ID: Optional[str] = Field(default=None, description="Alias de MAIL_TENANT_ID")
    GRAPH_CLIENT_ID: Optional[str] = Field(default=None, description="Alias de MAIL_CLIENT_ID")
    GRAPH_CLIENT_SECRET: Optional[str] = Field(default=None, description="Alias de MAIL_CLIENT_SECRET")
    GRAPH_SENDER_EMAIL: Optional[str] = Field(default=None, description="Alias de MAIL_SENDER_ADDRESS")
    GRAPHAPI_URL: Optional[str] = Field(default=None, description="URL completa de envio do Graph")
    GRAPHAPI_TENANT_ID: Optional[str] = Field(default=None, description="Alias de MAIL_TENANT_ID")
    GRAPHAPI_CLIENT_ID: Optional[str] = Field(default=None, description="Alias de MAIL_CLIENT_ID")
    GRAPHAPI_CLIENT_SECRET: Optional[str] = Field(default=None, description="Alias de MAIL_CLIENT_SECRET")
    GRAPHAPI_SENDER_EMAIL: Optional[str] = Field(default=None, description="Alias de MAIL_SENDER_ADDRESS")


# Instância singleton
settings = Settings()
