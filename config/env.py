import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent


class Env:
    def __init__(self):
        # Caminhos dos arquivos .env
        dotenv_paths = [f'{BASE_DIR}\\.env']
        
        # Carregar variáveis de cada .env
        for path in dotenv_paths:
            load_dotenv(dotenv_path=path, override=True)

    def get(self, key: str, default=None):
        """
        Retorna o valor da variável de ambiente.
        :param key: Nome da variável de ambiente.
        :param default: Valor padrão caso a variável não exista.
        :return: Valor da variável ou default.
        """
        return os.getenv(key, default)
        

# Instanciar uma única vez
env = Env()
