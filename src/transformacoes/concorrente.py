"""Geração da tabela fato de concorrentes."""

from datetime import datetime

from src.utilitarios import data_id, sql_number


def criar_fato_concorrente(concorrentes: list[dict], pedidos: list[dict]) -> list[str]:
    if not concorrentes:
        return [
            "-- FATO_CONCORRENTE",
            "-- Nenhuma coleção/documento de concorrentes foi encontrado.",
            "-- Nenhum INSERT foi gerado para FATO_Concorrente.",
        ]
    inserts = ["-- FATO_CONCORRENTE"]
    for indice, concorrente in enumerate(concorrentes, 1):
        data = concorrente.get("data") or concorrente.get("data_pedido")
        if not data:
            raise ValueError("Documento de concorrente sem campo de data.")
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        inserts.append(
            "INSERT INTO FATO_CONCORRENTE "
            "(ID_CONCORRENTE, ID_DATA, ANO, MES, DESCRICAO) VALUES "
            f"({indice}, {data_id(data)}, {data_obj.year}, {data_obj.month}, "
            f"{sql_number(concorrente.get('vendas'))});"
        )
    return inserts