"""Geração da dimensão de tempo."""

from datetime import datetime

from src.utilitarios import data_id, quadrimestre


def criar_dim_tempo(
    pedidos: list[dict], concorrentes: list[dict] | None = None
) -> list[str]:
    datas = {
        p["data_pedido"] for p in pedidos if p.get("data_pedido")
    }
    datas.update(
        concorrente["data"]
        for concorrente in concorrentes or []
        if concorrente.get("data")
    )
    inserts = ["-- DIM_TEMPO"]
    for data in sorted(datas):
        inserts.append(
            "INSERT INTO DIM_TEMPO (ID_DATA, ANO, QUADRIMESTRE) VALUES "
            f"({data_id(data)}, {datetime.strptime(data, '%Y-%m-%d').year}, "
            f"{quadrimestre(data)});"
        )
    return inserts