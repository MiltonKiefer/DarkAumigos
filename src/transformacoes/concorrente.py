"""Geração da tabela fato de concorrentes."""

from datetime import datetime

from src.utilitarios import data_id


def criar_fato_concorrente(concorrentes: list[dict], pedidos: list[dict]) -> list[str]:
    if not concorrentes:
        return [
            "-- FATO_Concorrente",
            "-- Nenhuma coleção/documento de concorrentes foi encontrado.",
            "-- Nenhum INSERT foi gerado para FATO_Concorrente.",
        ]
    inserts = ["-- FATO_Concorrente"]
    for indice, concorrente in enumerate(concorrentes, 1):
        data = concorrente.get("data") or concorrente.get("data_pedido")
        if not data:
            raise ValueError("Documento de concorrente sem campo de data.")
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        inserts.append(
            "INSERT INTO FATO_Concorrente (ID_Concorrente, ID_Data, Ano, Mes) VALUES "
            f"({indice}, {data_id(data)}, {data_obj.year}, {data_obj.month});"
        )
    return inserts