"""Configurações compartilhadas da pipeline."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEFAULT_COLLECTIONS = {
    "clientes": "05_Feira_Clientes",
    "produtos": "06_Feira_Produtos",
    "pedidos": "07_Feira_Pedidos",
    "concorrentes": "concorrentes",
}

DEFAULT_FILIAL_ID = 1
DEFAULT_FILIAL_NOME = "Feira Online"
DEFAULT_FILIAL_CIDADE = "Não informado"
