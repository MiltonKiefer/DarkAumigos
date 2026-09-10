"""Geração da dimensão de filial padrão."""

from src.config import (
    DEFAULT_FILIAL_CIDADE,
    DEFAULT_FILIAL_ID,
    DEFAULT_FILIAL_NOME,
    FILIAL_ITABUNA_CIDADE,
    FILIAL_ITABUNA_ID,
    FILIAL_ITABUNA_NOME,
    FILIAL_SALVADOR_CIDADE,
    FILIAL_SALVADOR_ID,
    FILIAL_SALVADOR_NOME,
)
from src.utilitarios import sql_string


FILIAIS_CONHECIDAS = {
    FILIAL_SALVADOR_ID: (FILIAL_SALVADOR_NOME, FILIAL_SALVADOR_CIDADE),
    FILIAL_ITABUNA_ID: (FILIAL_ITABUNA_NOME, FILIAL_ITABUNA_CIDADE),
    DEFAULT_FILIAL_ID: (DEFAULT_FILIAL_NOME, DEFAULT_FILIAL_CIDADE),
}


def criar_dim_filial(ids_filiais: set[int] | None = None) -> list[str]:
    ids_filiais = ids_filiais or {DEFAULT_FILIAL_ID}
    inserts = ["-- DIM_FILIAL"]
    for id_filial in sorted(ids_filiais):
        nome, cidade = FILIAIS_CONHECIDAS.get(
            id_filial,
            (f"Filial {id_filial}", "Não informado"),
        )
        inserts.append(
            "INSERT INTO DIM_FILIAL (ID_FILIAL, NOME, CIDADE) VALUES "
            f"({id_filial}, {sql_string(nome)}, {sql_string(cidade)});"
        )
    return inserts