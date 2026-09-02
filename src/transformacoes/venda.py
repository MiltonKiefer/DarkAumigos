"""Geração da tabela fato de vendas."""

from decimal import Decimal

from src.config import DEFAULT_FILIAL_ID
from src.utilitarios import data_id, sql_number


def criar_fato_venda(pedidos: list[dict]) -> list[str]:
    inserts = ["-- FATO_VENDA"]
    id_venda = 1
    for pedido in sorted(pedidos, key=lambda x: x["id_pedido"]):
        for item in pedido.get("itens", []):
            quantidade = item.get("quantidade", 0)
            preco = item.get("preco_unitario", 0)
            valor = Decimal(str(preco)) * Decimal(str(quantidade))
            inserts.append(
                "INSERT INTO FATO_VENDA (ID_VENDA, ID_PRODUTO, ID_DATA, ID_CLIENTE, "
                "ID_FILIAL, QUANTIDADE, VALOR) VALUES "
                f"({id_venda}, {int(item['id_produto'])}, "
                f"{data_id(pedido['data_pedido'])}, {int(pedido['id_cliente'])}, "
                f"{DEFAULT_FILIAL_ID}, {sql_number(quantidade)}, {sql_number(valor)});"
            )
            id_venda += 1
    return inserts