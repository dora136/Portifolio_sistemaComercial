# NovaCRM - Sistema de Gestão Comercial (Demo)
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

# Routers
from routes import lead_router, solucoes_router, parceiros_router, home_router, financeiro_router, admin_router, contratos_router
# Importa Sistema de Autenticacao
# from utils.auth_utils import get_authenticated_user, require_authenticated_user, get_user_info

# Roda API Automatico
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=7000,
        reload=False,  # ou True se for ambiente de dev
        proxy_headers=True,
        forwarded_allow_ips="*"
    )


# Inicializacao da API
app = FastAPI()

# Configuracao de arquivos estaticos (dupla montagem para funcionar com e sem prefixo)
BASE_DIR = Path(__file__).resolve().parent
app.mount("/portfolio/static", StaticFiles(directory=str(BASE_DIR / "static")), name="comercial_static")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Rota para o Menu de Leads
app.include_router(lead_router.router)

# Rota para o Menu de Parceiros
app.include_router(parceiros_router.router)

# Rota para o Menu de Solucoes
app.include_router(solucoes_router.router)

# Rota para Home/API
app.include_router(home_router.router)

# Rota para Financeiro
app.include_router(financeiro_router.router)

# Rota para Administração
app.include_router(admin_router.router)

# Rota para Contratos
app.include_router(contratos_router.router)
