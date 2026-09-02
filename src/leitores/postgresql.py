import os
import re
import hashlib
from decimal import Decimal
from datetime import date
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from pathlib import Path



BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# ============================================================
# CONFIGURAÇÕES
# ============================================================

# Dados de conexão do PostgreSQL/Supabase
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Arquivo SQL de saída
ARQUIVO_SAIDA = "insert_oracle_itabuna.sql"


# ============================================================
# CONEXÃO
# ============================================================

def conectar_postgresql():
    print("Conectando ao PostgreSQL/Supabase...")

    conexao = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require"
    )

    print("Conexão realizada com sucesso!")

    return conexao


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def escapar_string(valor):
    """
    Escapa strings para utilização em SQL Oracle.
    """
    if valor is None:
        return "NULL"

    valor = str(valor)

    # Oracle utiliza duas aspas simples para representar
    # uma aspa simples dentro de uma string.
    valor = valor.replace("'", "''")

    return f"'{valor}'"


def valor_sql(valor):
    """
    Converte valores Python para valores SQL Oracle.
    """

    if valor is None:
        return "NULL"

    if isinstance(valor, bool):
        return "1" if valor else "0"

    if isinstance(valor, Decimal):
        return str(valor)

    if isinstance(valor, (int, float)):
        return str(valor)

    if isinstance(valor, date):
        return f"TO_DATE('{valor.strftime('%Y-%m-%d')}', 'YYYY-MM-DD')"

    return escapar_string(valor)


def nome_seguro(nome):
    """
    Garante que o nome da tabela/coluna utilizado
    no SQL seja seguro.
    """

    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", nome):
        raise ValueError(f"Nome SQL inválido: {nome}")

    return nome


def gerar_insert(tabela, colunas, valores):
    """
    Gera um INSERT Oracle.
    """

    tabela = nome_seguro(tabela)

    colunas = [
        nome_seguro(coluna)
        for coluna in colunas
    ]

    valores_convertidos = [
        valor_sql(valor)
        for valor in valores
    ]

    return (
        f"INSERT INTO {tabela} "
        f"({', '.join(colunas)}) "
        f"VALUES ({', '.join(valores_convertidos)});"
    )


# ============================================================
# CONSULTA GENÉRICA
# ============================================================

def consultar(cursor, sql):
    cursor.execute(sql)

    return cursor.fetchall()


# ============================================================
# DIM_PRODUTO
# ============================================================

def gerar_dim_produto(cursor, inserts):
    print("Gerando DIM_Produto...")

    produtos = consultar(
        cursor,
        """
        SELECT
            id_produto,
            categoria,
            preco
        FROM produtos
        ORDER BY id_produto
        """
    )

    # Mapeamento:
    # categoria textual -> código numérico
    categorias = {}

    proximo_id_categoria = 1

    for produto in produtos:

        categoria = produto["categoria"]

        if categoria is None:
            categoria_id = None

        else:
            categoria = categoria.strip()

            if categoria not in categorias:
                categorias[categoria] = proximo_id_categoria
                proximo_id_categoria += 1

            categoria_id = categorias[categoria]

        inserts.append(
            gerar_insert(
                "DIM_Produto",
                [
                    "ID_Produto",
                    "Categoria",
                    "Valor"
                ],
                [
                    produto["id_produto"],
                    categoria_id,
                    produto["preco"]
                ]
            )
        )

    print(f"  {len(produtos)} produtos processados.")

    return categorias


# ============================================================
# DIM_CLIENTE
# ============================================================

def gerar_dim_cliente(cursor, inserts):
    print("Gerando DIM_Cliente...")

    clientes = consultar(
        cursor,
        """
        SELECT
            id_cliente,
            estado_civil
        FROM clientes
        ORDER BY id_cliente
        """
    )

    estados_civis = {}

    proximo_id = 1

    for cliente in clientes:

        estado = cliente["estado_civil"]

        if estado is None:
            estado_id = None

        else:
            estado = estado.strip().upper()

            if estado not in estados_civis:
                estados_civis[estado] = proximo_id
                proximo_id += 1

            estado_id = estados_civis[estado]

        inserts.append(
            gerar_insert(
                "DIM_Cliente",
                [
                    "ID_Cliente",
                    "Estado_Civil"
                ],
                [
                    cliente["id_cliente"],
                    estado_id
                ]
            )
        )

    print(f"  {len(clientes)} clientes processados.")

    return estados_civis


# ============================================================
# DIM_TEMPO
# ============================================================

def gerar_dim_tempo(cursor, inserts):
    print("Gerando DIM_Tempo...")

    datas = consultar(
        cursor,
        """
        SELECT DISTINCT
            data_venda
        FROM vendas
        WHERE data_venda IS NOT NULL
        ORDER BY data_venda
        """
    )

    for registro in datas:

        data_venda = registro["data_venda"]

        # ID no formato YYYYMMDD
        id_data = int(data_venda.strftime("%Y%m%d"))

        ano = data_venda.year

        # Quadrimestre:
        # Janeiro-Abril = 1
        # Maio-Agosto = 2
        # Setembro-Dezembro = 3
        quadrimestre = ((data_venda.month - 1) // 4) + 1

        inserts.append(
            gerar_insert(
                "DIM_Tempo",
                [
                    "ID_Data",
                    "Ano",
                    "Quadrimestre"
                ],
                [
                    id_data,
                    ano,
                    quadrimestre
                ]
            )
        )

    print(f"  {len(datas)} datas processadas.")


# ============================================================
# DIM_FILIAL
# ============================================================

def gerar_dim_filial(inserts):
    print("Gerando DIM_Filial...")

    # O banco PostgreSQL fornecido não possui uma tabela
    # de filiais.
    #
    # Portanto, todos os registros serão associados
    # à filial padrão Itabuna.

    inserts.append(
        gerar_insert(
            "DIM_Filial",
            [
                "ID_Filial",
                "Nome",
                "Cidade"
            ],
            [
                1,
                "Filial Itabuna",
                "Itabuna"
            ]
        )
    )

    print("  Filial padrão 'Itabuna' criada.")


# ============================================================
# FATO_VENDA
# ============================================================

def gerar_fato_venda(cursor, inserts):
    print("Gerando FATO_Venda...")

    vendas = consultar(
        cursor,
        """
        SELECT
            iv.id_item,
            iv.id_venda,
            v.id_cliente,
            v.data_venda,
            iv.id_produto,
            iv.quantidade,
            iv.valor_unitario
        FROM itens_venda iv
        INNER JOIN vendas v
            ON v.id_venda = iv.id_venda
        ORDER BY iv.id_item
        """
    )

    for venda in vendas:

        id_item = venda["id_item"]

        id_cliente = venda["id_cliente"]

        data_venda = venda["data_venda"]

        id_data = int(
            data_venda.strftime("%Y%m%d")
        )

        id_produto = venda["id_produto"]

        quantidade = venda["quantidade"]

        valor_unitario = venda["valor_unitario"]

        # Valor total do item
        if quantidade is not None and valor_unitario is not None:
            valor = Decimal(quantidade) * valor_unitario
        else:
            valor = None

        # ----------------------------------------------------
        # IMPORTANTE
        # ----------------------------------------------------
        # No modelo Oracle, FATO_Venda possui ID_Venda como
        # chave primária.
        #
        # Porém, no PostgreSQL uma venda pode possuir vários
        # itens.
        #
        # Portanto utilizamos ID_ITEM como ID_Venda no fato,
        # fazendo com que cada registro represente um item
        # vendido.
        # ----------------------------------------------------

        inserts.append(
            gerar_insert(
                "FATO_Venda",
                [
                    "ID_Venda",
                    "ID_Produto",
                    "ID_Data",
                    "ID_Cliente",
                    "ID_Filial",
                    "Quantidade",
                    "Valor"
                ],
                [
                    id_item,
                    id_produto,
                    id_data,
                    id_cliente,
                    1,
                    quantidade,
                    valor
                ]
            )
        )

    print(f"  {len(vendas)} itens de venda processados.")


# ============================================================
# FATO_CONCORRENTE
# ============================================================

def gerar_fato_concorrente(inserts):
    print("Gerando FATO_Concorrente...")

    # Não existe tabela de concorrentes no DDL PostgreSQL.
    #
    # Portanto não existem dados de origem para preencher
    # esta tabela.

    inserts.append(
        "-- FATO_Concorrente: sem dados disponíveis no PostgreSQL."
    )

    print("  Nenhum registro criado.")


# ============================================================
# CRIAÇÃO DO ARQUIVO
# ============================================================

def salvar_sql(inserts):
    print()
    print(f"Salvando arquivo: {ARQUIVO_SAIDA}")

    with open(
        ARQUIVO_SAIDA,
        "w",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(
            "-- =====================================================\n"
        )
        arquivo.write(
            "-- INSERTS GERADOS A PARTIR DO POSTGRESQL/SUPABASE\n"
        )
        arquivo.write(
            "-- Banco origem: Itabuna\n"
        )
        arquivo.write(
            "-- Banco destino: Oracle\n"
        )
        arquivo.write(
            "-- =====================================================\n\n"
        )

        # ----------------------------------------------------
        # DIMENSÕES
        # ----------------------------------------------------

        arquivo.write(
            "-- =====================================================\n"
        )
        arquivo.write(
            "-- DIMENSÕES\n"
        )
        arquivo.write(
            "-- =====================================================\n\n"
        )

        for insert in inserts:

            # Coloca os INSERTs diretamente na ordem em que
            # foram gerados.
            arquivo.write(insert)
            arquivo.write("\n")

        arquivo.write("\nCOMMIT;\n")

    print("Arquivo SQL criado com sucesso!")


# ============================================================
# MAIN
# ============================================================

def main():

    conexao = None

    try:

        conexao = conectar_postgresql()

        cursor = conexao.cursor(
            cursor_factory=RealDictCursor
        )

        inserts = []

        # ----------------------------------------------------
        # 1. DIMENSÕES
        # ----------------------------------------------------

        gerar_dim_produto(
            cursor,
            inserts
        )

        gerar_dim_cliente(
            cursor,
            inserts
        )

        gerar_dim_tempo(
            cursor,
            inserts
        )

        gerar_dim_filial(
            inserts
        )

        # ----------------------------------------------------
        # 2. FATOS
        # ----------------------------------------------------

        gerar_fato_venda(
            cursor,
            inserts
        )

        gerar_fato_concorrente(
            inserts
        )

        # ----------------------------------------------------
        # 3. SALVAR ARQUIVO
        # ----------------------------------------------------

        salvar_sql(inserts)

        cursor.close()

    except Exception as erro:

        print()
        print("ERRO:")
        print(erro)

        raise

    finally:

        if conexao is not None:
            conexao.close()
            print("Conexão encerrada.")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()
