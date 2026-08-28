"""Validação das referências entre pedidos, clientes e produtos."""


def validar_chaves(clientes: list[dict], produtos: list[dict], pedidos: list[dict]) -> None:
    ids_clientes = {int(x["id_cliente"]) for x in clientes}
    ids_produtos = {int(x["id_produto"]) for x in produtos}
    erros = []
    for pedido in pedidos:
        cliente = int(pedido["id_cliente"])
        if cliente not in ids_clientes:
            erros.append(
                f"Pedido {pedido['id_pedido']} referencia cliente inexistente {cliente}."
            )
        for item in pedido.get("itens", []):
            produto = int(item["id_produto"])
            if produto not in ids_produtos:
                erros.append(
                    f"Pedido {pedido['id_pedido']} referencia produto inexistente {produto}."
                )
    if erros:
        raise ValueError("Foram encontradas referências inválidas:\n" + "\n".join(erros[:20]))