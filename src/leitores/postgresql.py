"""Leitura do PostgreSQL/Supabase e geração de carga Oracle.

Este módulo mantém a origem PostgreSQL separada dos demais leitores da pipeline.
As credenciais são obtidas exclusivamente por variáveis de ambiente.
"""

from __future__ import annotations

import os
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


SQL_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _env(nome: str, padrao: str | None = None) -> str | None:
    valor = os.getenv(nome, padrao)
    return valor.strip() if valor else valor


def conectar_postgresql():
    """Abre uma conexão SSL com PostgreSQL/Supabase usando o ambiente."""
    host = _env("POSTGRES_HOST")
    if not host:
        raise RuntimeError("Defina POSTGRES_HOST no arquivo .env.")

    return psycopg2.connect(
        host=host,
        port=_env("POSTGRES_PORT", "5432"),
        dbname=_env("POSTGRES_DB", "postgres"),
        user=_env("POSTGRES_USER", "postgres"),
        password=_env("POSTGRES_PASSWORD"),
        sslmode=_env("POSTGRES_SSLMODE", "require"),
    )


def _nome_seguro(nome: str) -> str:
    if not SQL_IDENTIFIER.fullmatch(nome):
        raise ValueError(f"Identificador SQL inválido: {nome}")
    return nome


def _valor_sql(valor: Any) -> str:
    """Converte um valor Python para uma expressão SQL compatível com Oracle."""
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, date):
        return f"TO_DATE('{valor:%Y-%m-%d}', 'YYYY-MM-DD')"

    texto = str(valor).replace("'", "''")
    return f"'{texto}'"


def gerar_insert(tabela: str, colunas: list[str], valores: list[Any]) -> str:
    """Monta um INSERT Oracle validando tabela e colunas."""
    if len(colunas) != len(valores):
        raise ValueError("Quantidade de colunas e valores deve ser igual.")

    tabela = _nome_seguro(tabela)
    colunas = [_nome_seguro(coluna) for coluna in colunas]
    valores_sql = [_valor_sql(valor) for valor in valores]

    return (
        f"INSERT INTO {tabela} ({', '.join(colunas)}) "
        f"VALUES ({', '.join(valores_sql)});"
    )


def _consultar(cursor, sql: str):
    cursor.execute(sql)
    return cursor.fetchall()


def _gerar_dim_produto(cursor, inserts: list[str]) -> None:
    produtos = _consultar(
        cursor,
        """
        SELECT id_produto, categoria, preco
        FROM produtos
        ORDER BY id_produto
        """,
    )
    categorias: dict[str, int] = {}

    for produto in produtos:
        categoria = produto["categoria"]
        if categoria is not None:
            categoria = categoria.strip()
            categorias.setdefault(categoria, len(categorias) + 1)

        inserts.append(
            gerar_insert(
                "DIM_Produto",
                ["ID_Produto", "Categoria", "Valor"],
                [
                    produto["id_produto"],
                    categorias.get(categoria) if categoria else None,
                    produto["preco"],
                ],
            )
        )

    print(f"  DIM_Produto: {len(produtos)} registros.")


def _gerar_dim_cliente(cursor, inserts: list[str]) -> None:
    clientes = _consultar(
        cursor,
        """
        SELECT id_cliente, estado_civil
        FROM clientes
        ORDER BY id_cliente
        """,
    )
    estados_civis: dict[str, int] = {}

    for cliente in clientes:
        estado = cliente["estado_civil"]
        if estado is not None:
            estado = estado.strip().upper()
            estados_civis.setdefault(estado, len(estados_civis) + 1)

        inserts.append(
            gerar_insert(
                "DIM_Cliente",
                ["ID_Cliente", "Estado_Civil"],
                [cliente["id_cliente"], estados_civis.get(estado) if estado else None],
            )
        )

    print(f"  DIM_Cliente: {len(clientes)} registros.")


def _gerar_dim_tempo(cursor, inserts: list[str]) -> None:
    datas = _consultar(
        cursor,
        """
        SELECT DISTINCT data_venda
        FROM vendas
        WHERE data_venda IS NOT NULL
        ORDER BY data_venda
        """,
    )

    for registro in datas:
        data_venda = registro["data_venda"]
        inserts.append(
            gerar_insert(
                "DIM_Tempo",
                ["ID_Data", "Ano", "Quadrimestre"],
                [
                    int(data_venda.strftime("%Y%m%d")),
                    data_venda.year,
                    ((data_venda.month - 1) // 4) + 1,
                ],
            )
        )

    print(f"  DIM_Tempo: {len(datas)} registros.")


def _gerar_dim_filial(inserts: list[str]) -> None:
    inserts.append(
        gerar_insert(
            "DIM_Filial",
            ["ID_Filial", "Nome", "Cidade"],
            [1, "Filial Itabuna", "Itabuna"],
        )
    )
    print("  DIM_Filial: 1 registro padrão.")


def _gerar_fato_venda(cursor, inserts: list[str]) -> None:
    vendas = _consultar(
        cursor,
        """
        SELECT
            iv.id_item,
            v.id_cliente,
            v.data_venda,
            iv.id_produto,
            iv.quantidade,
            iv.valor_unitario
        FROM itens_venda iv
        INNER JOIN vendas v ON v.id_venda = iv.id_venda
        ORDER BY iv.id_item
        """,
    )

    for venda in vendas:
        data_venda = venda["data_venda"]
        quantidade = venda["quantidade"]
        valor_unitario = venda["valor_unitario"]
        valor = (
            Decimal(quantidade) * valor_unitario
            if quantidade is not None and valor_unitario is not None
            else None
        )

        inserts.append(
            gerar_insert(
                "FATO_Venda",
                [
                    "ID_Venda", "ID_Produto", "ID_Data", "ID_Cliente",
                    "ID_Filial", "Quantidade", "Valor",
                ],
                [
                    venda["id_item"],
                    venda["id_produto"],
                    int(data_venda.strftime("%Y%m%d")),
                    venda["id_cliente"],
                    1,
                    quantidade,
                    valor,
                ],
            )
        )

    print(f"  FATO_Venda: {len(vendas)} itens.")


def gerar_sql_postgresql() -> str:
    """Extrai o PostgreSQL e devolve o SQL Oracle completo em memória."""
    inserts: list[str] = []
    conexao = None

    try:
        print("Conectando ao PostgreSQL/Supabase...")
        conexao = conectar_postgresql()
        print("Conexão realizada com sucesso!")

        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            _gerar_dim_produto(cursor, inserts)
            _gerar_dim_cliente(cursor, inserts)
            _gerar_dim_tempo(cursor, inserts)
            _gerar_dim_filial(inserts)
            _gerar_fato_venda(cursor, inserts)

        return "\n".join(
            [
                "-- ============================================================",
                "-- CARGA POSTGRESQL/SUPABASE -> ORACLE",
                "-- Banco origem: PostgreSQL",
                "-- Banco destino: Oracle",
                "-- ============================================================",
                "",
                *inserts,
                "",
                "COMMIT;",
            ]
        )
    finally:
        if conexao is not None:
            conexao.close()
            print("Conexão encerrada.")


def salvar_sql_postgresql(caminho: str | Path) -> Path:
    """Gera e salva a carga Oracle em arquivo."""
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(gerar_sql_postgresql(), encoding="utf-8")
    return destino
