"""Orquestra a geração da carga SQL."""

from src.transformacoes.cliente import criar_dim_cliente
from src.transformacoes.concorrente import criar_fato_concorrente
from src.transformacoes.filial import criar_dim_filial
from src.transformacoes.mapas import criar_mapa_categorias, criar_mapa_estado_civil
from src.transformacoes.produto import criar_dim_produto
from src.transformacoes.tempo import criar_dim_tempo
from src.transformacoes.venda import criar_fato_venda
from src.validacao.chaves import validar_chaves


def gerar_sql(dados: dict[str, list[dict]]) -> str:
    clientes = dados["clientes"]
    produtos = dados["produtos"]
    pedidos = dados["pedidos"]
    concorrentes = dados.get("concorrentes", [])
    validar_chaves(clientes, produtos, pedidos)
    mapa_categorias = criar_mapa_categorias(produtos)
    mapa_estado_civil = criar_mapa_estado_civil(clientes)
    linhas = [
        "-- ============================================================",
        "-- CARGA DE DADOS - MONGODB ATLAS -> ORACLE OLAP",
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