"""Geração da dimensão de produtos."""

from src.utilitarios import sql_number


def criar_dim_produto(produtos: list[dict], mapa_categorias: dict[str, int]) -> list[str]:
    inserts = ["-- DIM_PRODUTO"]
    for produto in sorted(produtos, key=lambda x: x["id_produto"]):
        categoria = produto.get("categoria")
        inserts.append(
            "INSERT INTO DIM_PRODUTO (ID_PRODUTO, CATEGORIA, VALOR) VALUES "
            f"({int(produto['id_produto'])}, "
            f"{mapa_categorias.get(str(categoria), 'NULL')}, "
            f"{sql_number(produto.get('preco'))});"
        )
    return inserts