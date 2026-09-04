"""Geração da dimensão de clientes."""

from src.utilitarios import sql_number


def criar_dim_cliente(clientes: list[dict], mapa_estado_civil: dict[str, int]) -> list[str]:
    inserts = ["-- DIM_CLIENTE"]
    for cliente in sorted(clientes, key=lambda x: x["id_cliente"]):
        estado = cliente.get("estado_civil")
        if estado is None or (isinstance(estado, str) and not estado.strip()):
            estado = "Inexistente"
        codigo_estado = mapa_estado_civil.get(str(estado))
        inserts.append(
            "INSERT INTO DIM_CLIENTE (ID_CLIENTE, ESTADO_CIVIL) VALUES "
            f"({int(cliente['id_cliente'])}, {sql_number(codigo_estado)});"
        )
    return inserts