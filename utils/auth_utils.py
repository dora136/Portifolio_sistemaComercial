"""
Sistema de autenticacao do usuario.
Integra com um portal externo de login.
"""

import httpx
from fastapi import Request
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, Any
from config.config import settings


# Função auxiliar para buscar dados do usuário do sistema de login
async def get_current_user(access_token: str = None) -> Optional[Dict[str, Any]]:
    """
    Busca os dados do usuário autenticado no sistema de login.

    Args:
        access_token: Token de acesso do usuário

    Returns:
        Dicionário com os dados do usuário ou None se não autenticado
    """
    if not access_token:
        return None

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                "https://demo.local/api/user/me",
                # "http://localhost:8000/api/user/me",
                cookies={"access_token": access_token}
            )
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Erro ao buscar dados do usuário: {e}")

    return None


# Dependência do FastAPI para extrair o usuário da requisição
async def get_authenticated_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Dependência do FastAPI que extrai e valida o usuário autenticado da requisição.

    Busca o access_token nos cookies da requisição e retorna os dados do usuário.
    Retorna None se não houver token ou se a autenticação falhar.

    Usage:
        @app.get("/rota")
        async def minha_rota(user: dict = Depends(get_authenticated_user)):
            if user:
                print(f"Usuário logado: {user.get('name')}")
            else:
                print("Usuário não autenticado")
    """
    # DEV ONLY: force a dev admin user when running on localhost
    host = request.url.hostname or ""
    if host in ("localhost", "127.0.0.1"):
        return {
            "id": 101,
            "username": "dev_admin",
            "email": "dev_admin@local",
            "nome_completo": "Dev Admin",
            "roles": ["admin", "parceria_admin"],
        }

    # Tenta obter o access_token dos cookies
    access_token = request.cookies.get("access_token")
    
    # Se não encontrou nos cookies, tenta pegar do header Cookie (para quando vem do proxy)
    if not access_token:
        cookie_header = request.headers.get("cookie", "")
        # Parse manual do header Cookie para extrair access_token
        for cookie in cookie_header.split("; "):
            if cookie.startswith("access_token="):
                access_token = cookie.split("=", 1)[1]
                break

    if not access_token:
        return None

    # Busca os dados do usuário
    user_data = await get_current_user(access_token)

    return user_data


# Dependência do FastAPI que EXIGE autenticação
async def require_authenticated_user(request: Request) -> Dict[str, Any]:
    """
    Dependência do FastAPI que EXIGE que o usuário esteja autenticado.

    Redireciona para a pagina de login externa se o usuario nao estiver autenticado.

    Usage:
        @app.get("/rota-protegida")
        async def rota_protegida(user: dict = Depends(require_authenticated_user)):
            # user sempre estará presente aqui
            return {"message": f"Olá, {user.get('name')}"}
    """
    user = await get_authenticated_user(request)

    if not user:
        return RedirectResponse(url="https://demo.local/login", status_code=302)

    return user


# Função helper para obter informações específicas do usuário
def get_user_info(user: Optional[Dict[str, Any]], field: str, default: Any = None) -> Any:
    """
    Extrai uma informação específica do objeto de usuário.

    Args:
        user: Dicionário com dados do usuário
        field: Campo a ser extraído (ex: 'name', 'email', 'id')
        default: Valor padrão se o campo não existir

    Returns:
        O valor do campo ou o valor padrão
    """
    if not user:
        return default
    return user.get(field, default)


def has_role(user: Optional[Dict[str, Any]], role: str) -> bool:
    """Verifica se o usuário possui uma role específica."""
    if not user:
        return False
    roles = user.get("roles") or []
    return role in roles


def has_any_role(user: Optional[Dict[str, Any]], allowed_roles: list[str]) -> bool:
    """Verifica se o usuário possui ao menos uma das roles permitidas."""
    if not user:
        return False
    roles = user.get("roles") or []
    return any(r in roles for r in allowed_roles)


# Roles que dão acesso a Financeiro e Administração
ADMIN_ROLES = ["admin", "parceria_admin"]


def check_admin(user: Optional[Dict[str, Any]]):
    """
    Verifica se o usuário tem role admin ou parceria_admin.
    Retorna None se OK, ou RedirectResponse se não autorizado.
    """
    if settings.PORTFOLIO_DEMO_MODE:
        return None
    if not user:
        return RedirectResponse(url="https://demo.local/login", status_code=302)
    if not has_any_role(user, ADMIN_ROLES):
        return RedirectResponse(url="/portfolio/home", status_code=302)
    return None
