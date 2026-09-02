"""Orquestra a geração da carga SQL."""

from datetime import date, datetime
from typing import Any

from src.transformacoes.cliente import criar_dim_cliente
from src.transformacoes.concorrente import criar_fato_concorrente
from src.transformacoes.filial import criar_dim_filial
from src.transformacoes.mapas import criar_mapa_categorias, criar_mapa_estado_civil
from src.transformacoes.produto import criar_dim_produto
from src.transformacoes.tempo import criar_dim_tempo
from src.transformacoes.venda import criar_fato_venda
from src.validacao.chaves import validar_chaves


def _primeiro(documento: dict[str, Any], *nomes: str) -> Any:
    for nome in nomes:
        if nome in documento and documento[nome] is not None:
            return documento[nome]
    return None


def _data_iso(valor: Any, contexto: str) -> str:
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, str):
        texto = valor.strip()
        if "T" in texto:
            texto = texto.split("T", 1)[0]
        if " " in texto:
            texto = texto.split(" ", 1)[0]
        try:
            return date.fromisoformat(texto).isoformat()
        except ValueError:
            pass
    raise ValueError(f"{contexto} deve ser uma data válida (AAAA-MM-DD).")


def _inteiro(valor: Any, campo: str, contexto: str) -> int:
    if valor is None or isinstance(valor, bool):
        raise ValueError(f"{contexto}: campo obrigatório '{campo}' ausente.")
    try:
        return int(valor)
    except (TypeError, ValueError) as erro:
        raise ValueError(f"{contexto}: '{campo}' deve ser inteiro.") from erro


def _normalizar_dados(dados: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Converte JSON, MongoDB e PostgreSQL para o contrato dos transformadores."""
    if not isinstance(dados, dict):
        raise ValueError("A entrada do gerador deve ser um dicionário de coleções.")

    resultado: dict[str, list[dict]] = {
        "clientes": [],
        "produtos": [],
        "pedidos": [],
        "concorrentes": [],
    }

    for indice, cliente in enumerate(dados.get("clientes", []), 1):
        contexto = f"Cliente #{indice}"
        resultado["clientes"].append({
            "id_cliente": _inteiro(
                _primeiro(cliente, "id_cliente", "cliente_id"),
                "id_cliente", contexto,
            ),
            "estado_civil": _primeiro(cliente, "estado_civil", "estadoCivil"),
        })

    for indice, produto in enumerate(dados.get("produtos", []), 1):
        contexto = f"Produto #{indice}"
        resultado["produtos"].append({
            "id_produto": _inteiro(
                _primeiro(produto, "id_produto", "produto_id"),
                "id_produto", contexto,
            ),
            "categoria": _primeiro(produto, "categoria", "nome_categoria", "category"),
            "preco": _primeiro(produto, "preco", "preco_unitario", "valor"),
        })

    for indice, pedido in enumerate(dados.get("pedidos", []), 1):
        contexto = f"Pedido #{indice}"
        data = _primeiro(pedido, "data_pedido", "data_venda", "data")
        itens_origem = _primeiro(pedido, "itens", "itens_venda", "items") or []
        if not isinstance(itens_origem, list):
            raise ValueError(f"{contexto}: 'itens' deve ser uma lista.")
        itens = []
        for item_indice, item in enumerate(itens_origem, 1):
            item_contexto = f"{contexto}, item #{item_indice}"
            itens.append({
                "id_produto": _inteiro(
                    _primeiro(item, "id_produto", "produto_id"),
                    "id_produto", item_contexto,
                ),
                "quantidade": _primeiro(item, "quantidade", "qtd"),
                "preco_unitario": _primeiro(
                    item, "preco_unitario", "valor_unitario", "preco", "valor"
                ),
            })
        resultado["pedidos"].append({
            "id_pedido": _inteiro(
                _primeiro(pedido, "id_pedido", "id_venda", "pedido_id"),
                "id_pedido", contexto,
            ),
            "id_cliente": _inteiro(
                _primeiro(pedido, "id_cliente", "cliente_id"),
                "id_cliente", contexto,
            ),
            "data_pedido": _data_iso(data, f"{contexto}: campo 'data_pedido'"),
            "itens": itens,
        })

    for indice, concorrente in enumerate(dados.get("concorrentes", []), 1):
        data = _primeiro(concorrente, "data", "data_pedido", "data_venda")
        resultado["concorrentes"].append({
            "data": _data_iso(data, f"Concorrente #{indice}: campo 'data'"),
        })

    return resultado


def gerar_sql_oracle(dados: dict[str, list]) -> str:
    """Converte o retorno de ``leitores.oracle.buscar_dados`` em carga OLAP."""
    categorias = {registro[0]: registro[1] for registro in dados.get("categorias", [])}
    produtos = [
        {
            "id_produto": registro[0],
            "categoria": categorias.get(registro[3], registro[3]),
            "preco": registro[2],
        }
        for registro in dados.get("produtos", [])
    ]
    clientes = [
        {"id_cliente": registro[0], "estado_civil": registro[1]}
        for registro in dados.get("clientes", [])
    ]

    pedidos_por_id: dict[Any, dict] = {}
    for registro in dados.get("vendas_itens", []):
        id_pedido, id_cliente, data_venda, id_produto, quantidade, preco = registro
        pedido = pedidos_por_id.setdefault(
            id_pedido,
            {
                "id_pedido": id_pedido,
                "id_cliente": id_cliente,
                "data_pedido": data_venda,
                "itens": [],
            },
        )
        pedido["itens"].append({
            "id_produto": id_produto,
            "quantidade": quantidade,
            "preco_unitario": preco,
        })

    return _gerar_sql_com_mapas(
        {
            "clientes": clientes,
            "produtos": produtos,
            "pedidos": list(pedidos_por_id.values()),
            "concorrentes": [],
        },
        {str(nome): indice for indice, nome in categorias.items()},
        {
            "S": 1,
            "SOLTEIRO": 1,
            "SOLTEIRA": 1,
            "C": 2,
            "CASADO": 2,
            "CASADA": 2,
            "D": 3,
            "DIVORCIADO": 3,
            "DIVORCIADA": 3,
            "V": 4,
            "VIUVO": 4,
            "VIUVA": 4,
            "O": 5,
            "OUTRO": 5,
            "OUTROS": 5,
            "U": 6,
            "UNIAO ESTAVEL": 6,
            "UNIÃO ESTÁVEL": 6,
        },
    )


def _gerar_sql_com_mapas(
    dados: dict[str, list[dict]],
    mapa_categorias: dict[str, int] | None = None,
    mapa_estado_civil: dict[str, int] | None = None,
) -> str:
    dados = _normalizar_dados(dados)
    clientes = dados["clientes"]
    produtos = dados["produtos"]
    pedidos = dados["pedidos"]
    concorrentes = dados.get("concorrentes", [])
    validar_chaves(clientes, produtos, pedidos)
    mapa_categorias = mapa_categorias or criar_mapa_categorias(produtos)
    mapa_estado_civil = mapa_estado_civil or criar_mapa_estado_civil(clientes)
    linhas = [
        "-- ============================================================",
        "-- CARGA DE DADOS - FONTES OPERACIONAIS -> ORACLE OLAP",
        "-- Gerado automaticamente pelo script Python",
        "-- ============================================================", "",
        "-- A ordem abaixo respeita as chaves estrangeiras do DDL.", "",
    ]
    linhas.extend(criar_dim_produto(produtos, mapa_categorias))
    linhas.append("")
    linhas.extend(criar_dim_tempo(pedidos))
    linhas.append("")
    linhas.extend(criar_dim_cliente(clientes, mapa_estado_civil))
    linhas.append("")
    linhas.extend(criar_dim_filial())
    linhas.append("")
    linhas.extend(criar_fato_venda(pedidos))
    linhas.append("")
    linhas.extend(criar_fato_concorrente(concorrentes, pedidos))
    linhas.append("")
    linhas.extend([
        "COMMIT;", "", "-- ============================================================",
        "-- FIM DA CARGA", "-- ============================================================",
    ])
    return "\n".join(linhas)


def salvar_sql(dados: dict[str, list[dict]], caminho_saida: str) -> str:
    """Gera e grava uma carga SQL a partir de dados já extraídos."""
    from pathlib import Path

    caminho = Path(caminho_saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(gerar_sql(dados), encoding="utf-8")
    return str(caminho)


def gerar_sql(dados: dict[str, list[dict]]) -> str:
    return _gerar_sql_com_mapas(dados)