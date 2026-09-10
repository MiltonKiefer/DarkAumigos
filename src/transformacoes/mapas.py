"""Mapeamentos dos atributos textuais para códigos numéricos."""


ESTADOS_CIVIS = {
    "S": 1,
    "C": 2,
    "D": 3,
    "V": 4,
    "O": 5,
    "U": 6,
}

ESTADOS_CIVIS_TEXTO = {
    "SOLTEIRO": 1,
    "SOLTEIRA": 1,
    "CASADO": 2,
    "CASADA": 2,
    "DIVORCIADO": 3,
    "DIVORCIADA": 3,
    "VIUVO": 4,
    "VIUVA": 4,
    "VIÚVO": 4,
    "VIÚVA": 4,
    "OUTRO": 5,
    "OUTROS": 5,
    "UNIAO ESTAVEL": 6,
    "UNIÃO ESTÁVEL": 6,
}


def normalizar_estado_civil(valor: object) -> str:
    if valor is None:
        return "INEXISTENTE"
    texto = str(valor).strip().upper()
    return texto or "INEXISTENTE"


def mapear_estado_civil(valor: object) -> int | None:
    texto = normalizar_estado_civil(valor)
    mapa = {**ESTADOS_CIVIS, **ESTADOS_CIVIS_TEXTO}
    if texto in mapa:
        return mapa[texto]
    try:
        return int(texto)
    except ValueError:
        return None


def criar_mapa_categorias(produtos: list[dict]) -> dict[str, int]:
    categorias = sorted({str(p.get("categoria")) for p in produtos if p.get("categoria") is not None})
    return {categoria: indice for indice, categoria in enumerate(categorias, 1)}


def criar_mapa_estado_civil(clientes: list[dict]) -> dict[str, int]:
    mapa = {**ESTADOS_CIVIS, **ESTADOS_CIVIS_TEXTO, "INEXISTENTE": 7}
    proximo_id = max(mapa.values()) + 1

    for cliente in clientes:
        estado = normalizar_estado_civil(cliente.get("estado_civil"))
        if estado not in mapa:
            codigo = mapear_estado_civil(estado)
            if codigo is None:
                codigo = proximo_id
                proximo_id += 1
            mapa[estado] = codigo

    return mapa