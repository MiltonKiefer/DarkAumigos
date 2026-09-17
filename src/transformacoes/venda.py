"""Geração da tabela fato de vendas."""

from decimal import Decimal

from src.config import DEFAULT_FILIAL_ID
from src.utilitarios import periodo_id, sql_number


def criar_fato_venda(
    pedidos: list[dict], mapa_clientes: dict[int, int] | None = None
) -> list[str]:
    inserts = ["-- FATO_VENDA"]
    grupos: dict[tuple[int, int, int, int], tuple[Decimal, Decimal]] = {}

    for pedido in pedidos:
        id_cliente = (
            mapa_clientes.get(int(pedido["id_cliente"]), int(pedido["id_cliente"]))
            if mapa_clientes is not None
            else int(pedido["id_cliente"])
        )
        id_data = periodo_id(pedido["data_pedido"])
        id_filial = int(pedido.get("id_filial", DEFAULT_FILIAL_ID))
        for item in pedido.get("itens", []):
            id_produto = int(item["id_produto"])
            quantidade = Decimal(str(item.get("quantidade", 0)))
            preco = Decimal(str(item.get("preco_unitario", 0)))
            chave = (id_data, id_cliente, id_filial, id_produto)
            quantidade_anterior, valor_anterior = grupos.get(
                chave, (Decimal("0"), Decimal("0"))
            )
            grupos[chave] = (
                quantidade_anterior + quantidade,
                valor_anterior + (preco * quantidade),
            )

    id_venda = 1
    for (id_data, id_cliente, id_filial, id_produto), (quantidade, valor) in sorted(
        grupos.items()
    ):
        inserts.append(
            "INSERT INTO FATO_VENDA (ID_VENDA, ID_PRODUTO, ID_DATA, ID_CLIENTE, "
            "ID_FILIAL, QUANTIDADE, VALOR) VALUES "
            f"({id_venda}, {id_produto}, {id_data}, {id_cliente}, {id_filial}, "
            f"{sql_number(quantidade)}, {sql_number(valor)});"
        )
        id_venda += 1
    return inserts