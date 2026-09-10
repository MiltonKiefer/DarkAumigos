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

FILIAL_SALVADOR_ID = 1
FILIAL_SALVADOR_NOME = "Filial Salvador"
FILIAL_SALVADOR_CIDADE = "Salvador"

FILIAL_ITABUNA_ID = 2
FILIAL_ITABUNA_NOME = "Filial Itabuna"
FILIAL_ITABUNA_CIDADE = "Itabuna"

DEFAULT_FILIAL_ID = 3
DEFAULT_FILIAL_NOME = "Feira Online"
DEFAULT_FILIAL_CIDADE = "Não informado"

POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE", "require")
