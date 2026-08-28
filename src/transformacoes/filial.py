"""Geração da dimensão de filial padrão."""

from src.config import DEFAULT_FILIAL_CIDADE, DEFAULT_FILIAL_ID, DEFAULT_FILIAL_NOME
from src.utilitarios import sql_string


def criar_dim_filial() -> list[str]:
    return [
        "-- DIM_Filial",
        "INSERT INTO DIM_Filial (ID_Filial, Nome, Cidade) VALUES "
        f"({DEFAULT_FILIAL_ID}, {sql_string(DEFAULT_FILIAL_NOME)}, "
        f"{sql_string(DEFAULT_FILIAL_CIDADE)});",
    ]