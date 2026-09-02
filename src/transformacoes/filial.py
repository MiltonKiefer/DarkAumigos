"""Geração da dimensão de filial padrão."""

from src.config import DEFAULT_FILIAL_CIDADE, DEFAULT_FILIAL_ID, DEFAULT_FILIAL_NOME
from src.utilitarios import sql_string


def criar_dim_filial() -> list[str]:
    return [
        "-- DIM_FILIAL",
        "INSERT INTO DIM_FILIAL (ID_FILIAL, NOME, CIDADE) VALUES "
        f"({DEFAULT_FILIAL_ID}, {sql_string(DEFAULT_FILIAL_NOME)}, "
        f"{sql_string(DEFAULT_FILIAL_CIDADE)});",
    ]