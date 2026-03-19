"""
Database Provider Module

Gerencia conexoes ODBC com multiplas bases de dados,
suportando diferentes perfis de acesso (reader, writer, ddl).
"""

import json
import os
from typing import Optional, Literal
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# Importar apenas settings (variáveis) do config.py
try:
    from config.config import settings
except ImportError:
    from config.config import settings


# -------------------------------------------------------------------------
# TYPE HINTS (CONSTANTES - não variam por projeto)
# -------------------------------------------------------------------------

ProfileType = Literal["reader", "writer", "ddl"]
ConnectionType = Literal["sqlalchemy", "pyodbc"]


# -------------------------------------------------------------------------
# EXCEÇÕES CUSTOMIZADAS
# -------------------------------------------------------------------------

class DatabaseConfigError(Exception):
    """Erro de configuração do banco de dados."""
    pass


class MissingCredentialsError(DatabaseConfigError):
    """Credenciais do banco de dados não encontradas."""
    pass


class InvalidProfileError(DatabaseConfigError):
    """Perfil de acesso inválido ou não suportado."""
    pass


# -------------------------------------------------------------------------
# GERAÇÃO DINÂMICA DE MAPAS (LÓGICA CONSTANTE)
# -------------------------------------------------------------------------

def _generate_db_name_map() -> dict[str, str]:
    """
    Gera DB_NAME_MAP dinamicamente baseado no que está configurado.
    
    Retorna apenas bancos que têm valor não-None no settings.
    """
    all_mappings = {
        "core_data": ("DB_DATABASE_CORE", getattr(settings, "DB_DATABASE_CORE", None)),
        "admin_data": ("DB_DATABASE_ADM", getattr(settings, "DB_DATABASE_ADM", None)),
        "app_data": ("DB_DATABASE_GESTAO", getattr(settings, "DB_DATABASE_GESTAO", None)),
        "dev": ("DB_DATABASE_DEV", getattr(settings, "DB_DATABASE_DEV", None)),
        "people_data": ("DB_DATABASE_SECURE", getattr(settings, "DB_DATABASE_SECURE", None)),
        # Compatibilidade com chaves legadas
        "core": ("DB_DATABASE_CORE", getattr(settings, "DB_DATABASE_CORE", None)),
        "adm": ("DB_DATABASE_ADM", getattr(settings, "DB_DATABASE_ADM", None)),
        "gestao": ("DB_DATABASE_GESTAO", getattr(settings, "DB_DATABASE_GESTAO", None)),
        "secure": ("DB_DATABASE_SECURE", getattr(settings, "DB_DATABASE_SECURE", None)),
    }
    
    return {
        db_key: env_var
        for db_key, (env_var, value) in all_mappings.items()
        if value is not None
    }


def _generate_credentials_map() -> dict[tuple[str, str], tuple[str, str]]:
    """
    Gera DB_CREDENTIALS_MAP dinamicamente baseado no que está configurado.
    
    Retorna apenas perfis que têm AMBOS UID e PWD configurados (não-None).
    """
    all_possible_credentials = [
        (("dev", "reader"), "DB_DEV_READER_UID", "DB_DEV_READER_PWD"),
        (("dev", "writer"), "DB_DEV_WRITER_UID", "DB_DEV_WRITER_PWD"),
        (("dev", "ddl"), "DB_DEV_DDL_UID", "DB_DEV_DDL_PWD"),
        (("core_data", "reader"), "DB_CORE_READER_UID", "DB_CORE_READER_PWD"),
        (("core_data", "writer"), "DB_CORE_WRITER_UID", "DB_CORE_WRITER_PWD"),
        (("core_data", "ddl"), "DB_CORE_DDL_UID", "DB_CORE_DDL_PWD"),
        (("admin_data", "reader"), "DB_ADM_READER_UID", "DB_ADM_READER_PWD"),
        (("admin_data", "writer"), "DB_ADM_WRITER_UID", "DB_ADM_WRITER_PWD"),
        (("admin_data", "ddl"), "DB_ADM_DDL_UID", "DB_ADM_DDL_PWD"),
        (("app_data", "reader"), "DB_GST_READER_UID", "DB_GST_READER_PWD"),
        (("app_data", "writer"), "DB_GST_WRITER_UID", "DB_GST_WRITER_PWD"),
        (("app_data", "ddl"), "DB_GST_DDL_UID", "DB_GST_DDL_PWD"),
        (("people_data", "reader"), "DB_SECURE_READER_UID", "DB_SECURE_READER_PWD"),
        (("people_data", "writer"), "DB_SECURE_WRITER_UID", "DB_SECURE_WRITER_PWD"),
        # Compatibilidade com chaves legadas
        (("core", "reader"), "DB_CORE_READER_UID", "DB_CORE_READER_PWD"),
        (("core", "writer"), "DB_CORE_WRITER_UID", "DB_CORE_WRITER_PWD"),
        (("core", "ddl"), "DB_CORE_DDL_UID", "DB_CORE_DDL_PWD"),
        (("adm", "reader"), "DB_ADM_READER_UID", "DB_ADM_READER_PWD"),
        (("adm", "writer"), "DB_ADM_WRITER_UID", "DB_ADM_WRITER_PWD"),
        (("adm", "ddl"), "DB_ADM_DDL_UID", "DB_ADM_DDL_PWD"),
        (("gestao", "reader"), "DB_GST_READER_UID", "DB_GST_READER_PWD"),
        (("gestao", "writer"), "DB_GST_WRITER_UID", "DB_GST_WRITER_PWD"),
        (("gestao", "ddl"), "DB_GST_DDL_UID", "DB_GST_DDL_PWD"),
        # Compatibilidade com chave legada "secure"
        (("secure", "reader"), "DB_SECURE_READER_UID", "DB_SECURE_READER_PWD"),
        (("secure", "writer"), "DB_SECURE_WRITER_UID", "DB_SECURE_WRITER_PWD"),
    ]
    
    result = {}
    for key, uid_var, pwd_var in all_possible_credentials:
        uid = getattr(settings, uid_var, None)
        pwd = getattr(settings, pwd_var, None)
        
        # Só adiciona se AMBOS estiverem configurados
        if uid is not None and pwd is not None:
            result[key] = (uid_var, pwd_var)
    
    return result


# Gerar mapas dinamicamente na importação
DB_NAME_MAP = _generate_db_name_map()
DB_CREDENTIALS_MAP = _generate_credentials_map()


# -------------------------------------------------------------------------
# LÓGICA DE MONTAGEM DA URI
# -------------------------------------------------------------------------

def _build_connection_string(
    db_key: str,
    profile: ProfileType = "reader",
    connection_type: ConnectionType = "sqlalchemy"
) -> str:
    """
    Monta a string de conexão completa com o perfil de acesso especificado.
    
    Args:
        db_key: Identificador do banco (core_data, admin_data, app_data, dev, people_data)
        profile: Perfil de acesso (reader, writer, ddl). Default: "reader"
        connection_type: Tipo de conexão (sqlalchemy ou pyodbc). Default: "sqlalchemy"
    
    Returns:
        String de conexão formatada
        
    Raises:
        DatabaseConfigError: Se os mapas de configuração forem inválidos
        InvalidProfileError: Se o perfil não for suportado para o banco
        MissingCredentialsError: Se as credenciais não estiverem no .env
        
    Examples:
        >>> conn_str = _build_connection_string("core_data", "reader")
        >>> conn_str = _build_connection_string("dev", "writer", "pyodbc")
    """
    # 1. Validação do perfil
    valid_profiles = ["reader", "writer", "ddl"]
    if profile not in valid_profiles:
        raise InvalidProfileError(
            f"Perfil '{profile}' inválido. Perfis válidos: {', '.join(valid_profiles)}"
        )
    
    # 2. Validação do db_key
    if db_key not in DB_NAME_MAP:
        raise ValueError(
            f"Banco '{db_key}' não reconhecido. "
            f"Bancos disponíveis: {', '.join(DB_NAME_MAP.keys())}"
        )
    
    # 3. Buscar credenciais no mapeamento
    credential_key = (db_key, profile)
    if credential_key not in DB_CREDENTIALS_MAP:
        available_profiles = get_available_profiles(db_key)
        raise InvalidProfileError(
            f"Perfil '{profile}' não está configurado para o banco '{db_key}'.\n"
            f"Perfis disponíveis para '{db_key}': {', '.join(available_profiles)}\n\n"
            f"Para adicionar este perfil, defina as seguintes variáveis no .env:\n"
            f"  - DB_{db_key.upper()}_{profile.upper()}_UID\n"
            f"  - DB_{db_key.upper()}_{profile.upper()}_PWD"
        )
    
    uid_var, pwd_var = DB_CREDENTIALS_MAP[credential_key]
    
    # 4. Buscar valores das credenciais através do settings (centralizado)
    db_uid = getattr(settings, uid_var, None)
    db_pwd = getattr(settings, pwd_var, None)
    
    # 5. Validação de credenciais
    missing_vars = []
    if not db_uid:
        missing_vars.append(uid_var)
    if not db_pwd:
        missing_vars.append(pwd_var)
    
    if missing_vars:
        raise MissingCredentialsError(
            f"❌ Credenciais faltantes no arquivo .env\n\n"
            f"  Banco: {db_key}\n"
            f"  Perfil: {profile}\n"
            f"  Variáveis não definidas: {', '.join(missing_vars)}\n\n"
            f"Por favor, adicione estas variáveis ao arquivo .env e tente novamente.\n"
            f"Exemplo:\n"
            f"  {uid_var}=seu_usuario\n"
            f"  {pwd_var}=sua_senha"
        )
    
    # 6. Buscar configurações do servidor e driver através do settings
    try:
        db_server = settings.DB_SERVER  # Property com validação obrigatória
    except ValueError as e:
        raise MissingCredentialsError(str(e))
    
    # 7. Buscar nome do banco e driver através do settings
    db_database = get_database_name(db_key)  # Função local, não settings.
    db_driver = settings.DB_DRIVER3
    
    # 9. Construir a string de conexão ODBC
    odbc_conn_str = (
        f"Driver={{{db_driver}}};"
        f"Server={db_server};"
        f"Database={db_database};"
        f"UID={db_uid};"
        f"PWD={db_pwd};"
        "TrustServerCertificate=yes;"
    )
    
    # 10. Retornar conforme o tipo de conexão
    if connection_type == "pyodbc":
        return odbc_conn_str
    elif connection_type == "sqlalchemy":
        encoded_conn_str = quote_plus(odbc_conn_str)
        return f"mssql+pyodbc:///?odbc_connect={encoded_conn_str}"
    else:
        raise ValueError(
            f"Tipo de conexão '{connection_type}' não suportado. "
            f"Use 'sqlalchemy' ou 'pyodbc'."
        )


# -------------------------------------------------------------------------
# GESTÃO DA ENGINE (SINGLETON)
# -------------------------------------------------------------------------

_engine: Optional[Engine] = None
_current_db_key: Optional[str] = None
_current_profile: Optional[str] = None


def get_db_engine(
    db_key: str = "dev",
    profile: ProfileType = "reader"
) -> Engine:
    """
    Função Factory Singleton: Retorna a Engine para o banco e perfil solicitados.
    
    IMPORTANTE: A engine é compartilhada (singleton). Se você mudar de banco ou perfil,
    a engine anterior será substituída. Use dispose_db_engine() se precisar limpar.
    
    Args:
        db_key: Identificador do banco de dados. Default: "dev"
        profile: Perfil de acesso (reader, writer, ddl). Default: "reader"
    
    Returns:
        Engine do SQLAlchemy configurada
        
    Raises:
        DatabaseConfigError: Se houver problemas de configuração
        InvalidProfileError: Se o perfil não for válido
        MissingCredentialsError: Se as credenciais não estiverem definidas
        
    Examples:
        >>> # Conexão de leitura
        >>> engine = get_db_engine("core_data", "reader")
        >>> 
        >>> # Conexão de escrita
        >>> engine = get_db_engine("dev", "writer")
        >>> 
        >>> # Conexão com permissões DDL
        >>> engine = get_db_engine("app_data", "ddl")
    """
    if not db_key:
        raise ValueError("Parâmetro 'db_key' é obrigatório.")
    
    global _engine, _current_db_key, _current_profile
    
    # Se a Engine já existe e atende ao banco/perfil solicitado, retorna ela
    if (
        _engine is not None 
        and _current_db_key == db_key 
        and _current_profile == profile
    ):
        return _engine
    
    # Se mudou de banco/perfil, dispose da engine anterior
    if _engine is not None:
        _engine.dispose()
    
    # 1. Geração da URI
    conn_str = _build_connection_string(db_key=db_key, profile=profile)
    
    # 2. Criação da Engine
    engine = create_engine(
        conn_str,
        future=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
    
    # 3. Armazenamento da Engine (Singleton)
    _engine = engine
    _current_db_key = db_key
    _current_profile = profile
    
    return engine


def dispose_db_engine():
    """
    Fecha todas as conexões da pool e limpa a engine singleton.
    
    Use esta função quando terminar de usar o banco de dados ou
    quando precisar trocar de banco/perfil.
    """
    global _engine, _current_db_key, _current_profile
    if _engine:
        _engine.dispose()
        _engine = None
        _current_db_key = None
        _current_profile = None


def get_current_connection_info() -> dict:
    """
    Retorna informações sobre a conexão atual.
    
    Returns:
        Dicionário com db_key, profile e status da conexão
        
    Examples:
        >>> info = get_current_connection_info()
        >>> print(info)
        {'db_key': 'core_data', 'profile': 'reader', 'connected': True}
    """
    return {
        "db_key": _current_db_key,
        "profile": _current_profile,
        "connected": _engine is not None
    }


# -------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# -------------------------------------------------------------------------

def get_available_profiles(db_key: str) -> list[str]:
    """
    Retorna lista de perfis disponíveis para um banco específico.
    
    Args:
        db_key: Identificador do banco de dados
        
    Returns:
        Lista de perfis disponíveis (ex: ['reader', 'writer', 'ddl'])
        
    Examples:
        >>> profiles = get_available_profiles("core_data")
        >>> print(profiles)
        ['ddl', 'reader', 'writer']
    """
    profiles = [
        profile 
        for (db, profile) in DB_CREDENTIALS_MAP.keys() 
        if db == db_key
    ]
    return sorted(profiles)


def list_all_databases() -> dict[str, list[str]]:
    """
    Lista todos os bancos de dados e seus perfis disponíveis.
    
    Returns:
        Dicionário mapeando banco -> lista de perfis
        
    Examples:
        >>> all_dbs = list_all_databases()
        >>> for db, profiles in all_dbs.items():
        ...     print(f"{db}: {profiles}")
        dev: ['ddl', 'reader', 'writer']
        core_data: ['ddl', 'reader', 'writer']
        ...
    """
    result = {}
    for db_key in DB_NAME_MAP.keys():
        result[db_key] = get_available_profiles(db_key)
    return result


def get_database_name(db_key: str) -> str:
    """
    Retorna o nome do banco para uma chave.
    
    Args:
        db_key: Chave do banco (ex: 'core_data', 'dev')
        
    Returns:
        Nome do banco configurado
        
    Raises:
        KeyError: Se db_key não estiver configurado
        
    Examples:
        >>> get_database_name('core_data')
        'core_data'
    """
    if db_key not in DB_NAME_MAP:
        available = list(DB_NAME_MAP.keys())
        raise KeyError(
            f"Banco '{db_key}' não está configurado!\n"
            f"Bancos disponíveis: {', '.join(available) if available else 'nenhum'}\n\n"
            f"Para configurar, adicione no config.py e .env:\n"
            f"  DB_DATABASE_{db_key.upper()}: Optional[str] = Field(default='{db_key}')"
        )
    
    env_var = DB_NAME_MAP[db_key]
    return getattr(settings, env_var)


def get_credentials(db_key: str, profile: ProfileType) -> tuple[Optional[str], Optional[str]]:
    """
    Retorna (username, password) para banco/perfil.
    
    Args:
        db_key: Chave do banco
        profile: Perfil de acesso
        
    Returns:
        Tupla (username, password)
        
    Raises:
        KeyError: Se combinação banco/perfil não estiver configurada
        
    Examples:
        >>> uid, pwd = get_credentials('core_data', 'reader')
    """
    key = (db_key, profile)
    if key not in DB_CREDENTIALS_MAP:
        available_profiles = get_available_profiles(db_key)
        raise KeyError(
            f"Perfil '{profile}' não configurado para banco '{db_key}'!\n"
            f"Perfis disponíveis para '{db_key}': {', '.join(available_profiles) if available_profiles else 'nenhum'}\n\n"
            f"Para configurar, adicione no .env:\n"
            f"  DB_{db_key.upper()}_{profile.upper()}_UID=seu_usuario\n"
            f"  DB_{db_key.upper()}_{profile.upper()}_PWD=sua_senha"
        )
    
    uid_var, pwd_var = DB_CREDENTIALS_MAP[key]
    return (getattr(settings, uid_var, None), getattr(settings, pwd_var, None))


def is_configured(db_key: str, profile: Optional[ProfileType] = None) -> bool:
    """
    Verifica se banco/perfil está configurado.
    
    Args:
        db_key: Chave do banco
        profile: Perfil opcional. Se None, verifica apenas banco
        
    Returns:
        True se configurado, False caso contrário
        
    Examples:
        >>> is_configured('core_data')
        True
        >>> is_configured('core_data', 'reader')
        True
        >>> is_configured('xyz', 'reader')
        False
    """
    if profile is None:
        return db_key in DB_NAME_MAP
    else:
        return (db_key, profile) in DB_CREDENTIALS_MAP


def validate_environment() -> dict[str, list[str]]:
    """
    Valida se todas as variáveis de ambiente necessárias estão configuradas.
    
    IMPORTANTE: Agora valida através do config.settings ao invés de os.getenv direto.
    
    Returns:
        Dicionário com 'missing' (variáveis faltantes) e 'ok' (variáveis presentes)
        
    Examples:
        >>> status = validate_environment()
        >>> if status['missing']:
        ...     print("Variáveis faltantes:", status['missing'])
    """
    missing = []
    ok = []
    
    # Validar DB_SERVER através do settings
    try:
        if settings.DB_SERVER:
            ok.append("DB_SERVER")
    except ValueError:
        missing.append("DB_SERVER")
    
    # Validar credenciais de todos os perfis através do settings
    for (db_key, profile), (uid_var, pwd_var) in DB_CREDENTIALS_MAP.items():
        # Validar UID
        uid_value = getattr(settings, uid_var, None)
        if not uid_value:
            missing.append(uid_var)
        else:
            ok.append(uid_var)
        
        # Validar PWD
        pwd_value = getattr(settings, pwd_var, None)
        if not pwd_value:
            missing.append(pwd_var)
        else:
            ok.append(pwd_var)
    
    # Validar nomes de bancos através do settings
    for env_var in DB_NAME_MAP.values():
        db_name = getattr(settings, env_var, None)
        if not db_name:
            missing.append(env_var)
        else:
            ok.append(env_var)
    
    return {
        "missing": sorted(set(missing)),
        "ok": sorted(set(ok))
    }
