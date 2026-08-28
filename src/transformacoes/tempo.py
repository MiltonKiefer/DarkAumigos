"""Geração da dimensão de tempo."""

from datetime import datetime

from src.utilitarios import data_id, quadrimestre


def criar_dim_tempo(pedidos: list[dict]) -> list[str]:
    datas = sorted({p["data_pedido"] for p in pedidos if p.get("data_pedido")})
    inserts = ["-- DIM_Tempo"]
    for data in datas:
        inserts.append(
            "INSERT INTO DIM_Tempo (ID_Data, Ano, Quadrimestre) VALUES "
            f"({data_id(data)}, {datetime.strptime(data, '%Y-%m-%d').year}, "
            f"{quadrimestre(data)});"
        )
    return inserts