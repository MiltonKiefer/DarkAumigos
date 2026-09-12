"""Geração da tabela fato de vendas."""

from decimal import Decimal

from src.config import DEFAULT_FILIAL_ID
from src.utilitarios import periodo_id, sql_number


def criar_fato_venda(
    pedidos: list[dict], mapa_clientes: dict[int, int] | None = None
) -> list[str]:
    inserts = ["-- FATO_VENDA"]
    id_venda = 1
    for pedido in sorted(pedidos, key=lambda x: x["id_pedido"]):
        for item in pedido.get("itens", []):
            quantidade = item.get("quantidade", 0)
            preco = item.get("preco_unitario", 0)
            valor = Decimal(str(preco)) * Decimal(str(quantidade))
            id_cliente = (
                mapa_clientes.get(int(pedido["id_cliente"]), int(pedido["id_cliente"]))
                if mapa_clientes is not None
                else int(pedido["id_cliente"])
            )
            inserts.append(
                "INSERT INTO FATO_VENDA (ID_VENDA, ID_PRODUTO, ID_DATA, ID_CLIENTE, "
                "ID_FILIAL, QUANTIDADE, VALOR) VALUES "
                f"({id_venda}, {int(item['id_produto'])}, "
                f"{periodo_id(pedido['data_pedido'])}, {id_cliente}, "
                f"{int(pedido.get('id_filial', DEFAULT_FILIAL_ID))}, "
                f"{sql_number(quantidade)}, {sql_number(valor)});"
            )
            id_venda += 1
    return inserts