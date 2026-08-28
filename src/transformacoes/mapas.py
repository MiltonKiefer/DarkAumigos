"""Mapeamentos dos atributos textuais para códigos numéricos."""


def criar_mapa_categorias(produtos: list[dict]) -> dict[str, int]:
    categorias = sorted({str(p.get("categoria")) for p in produtos if p.get("categoria") is not None})
    return {categoria: indice for indice, categoria in enumerate(categorias, 1)}


def criar_mapa_estado_civil(clientes: list[dict]) -> dict[str, int]:
    estados = sorted({str(c.get("estado_civil")) for c in clientes if c.get("estado_civil") is not None})
    return {estado: indice for indice, estado in enumerate(estados, 1)}