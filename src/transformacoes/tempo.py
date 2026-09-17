"""Geração da dimensão de tempo."""

from datetime import datetime

from src.utilitarios import periodo_id, quadrimestre


def criar_dim_tempo(
    pedidos: list[dict], concorrentes: list[dict] | None = None
) -> list[str]:
    periodos = {
        (datetime.strptime(p["data_pedido"], "%Y-%m-%d").year, quadrimestre(p["data_pedido"]))
        for p in pedidos
        if p.get("data_pedido")
    }
    periodos.update(
        (datetime.strptime(concorrente["data"], "%Y-%m-%d").year, quadrimestre(concorrente["data"]))
        for concorrente in concorrentes or []
        if concorrente.get("data")
    )
    inserts = ["-- DIM_TEMPO"]
    for ano, quad in sorted(periodos):
        inserts.append(
            "INSERT INTO DIM_TEMPO (ID_DATA, ANO, QUADRIMESTRE) VALUES "
            f"({ano * 10 + quad}, {ano}, {quad});"
        )
    return inserts