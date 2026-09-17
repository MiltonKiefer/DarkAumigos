"""Geração da dimensão de clientes."""

from src.utilitarios import sql_number
from src.transformacoes.mapas import normalizar_estado_civil


def criar_dim_cliente(clientes: list[dict], mapa_estado_civil: dict[str, int]) -> list[str]:
    inserts = ["-- DIM_CLIENTE"]
    codigos_estado = {
        mapa_estado_civil[normalizar_estado_civil(cliente.get("estado_civil"))]
        for cliente in clientes
    }
    for codigo_estado in sorted(codigos_estado):
        inserts.append(
            "INSERT INTO DIM_CLIENTE (ID_CLIENTE, ESTADO_CIVIL) VALUES "
            f"({int(codigo_estado)}, {sql_number(codigo_estado)});"
        )
    return inserts