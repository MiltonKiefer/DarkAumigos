"""
Migração de dados Oracle -> Oracle (Salvador -> modelo OLAP)

Origem:
    01_salvador_ddl.sql

Destino:
    DDL Banco Oracle(1).sql

Dependência:
    pip install oracledb

Configuração:
    Defina as variáveis de ambiente:

    ORACLE_ORIGEM_USER
    ORACLE_ORIGEM_PASSWORD
    ORACLE_ORIGEM_DSN

    ORACLE_DESTINO_USER       (opcional, usado apenas para validação)
    ORACLE_DESTINO_PASSWORD   (opcional)
    ORACLE_DESTINO_DSN        (opcional)

Exemplo de DSN:
    localhost:1521/XEPDB1
    ou
    meu-host:1521/ORCL

Uso:
    python migrar_oracle.py

O programa NÃO insere diretamente no banco destino.
Ele consulta o banco de origem e gera:
    migracao_salvador.sql

O arquivo gerado pode ser executado no Oracle destino.
"""

import os
import sys
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path

import oracledb
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


# ============================================================
# CONFIGURAÇÕES
# ============================================================

OUTPUT_FILE = "migracao_salvador.sql"

# A filial Salvador será representada no DW por este ID.
ID_FILIAL_SALVADOR = 1
NOME_FILIAL = "Salvador"
CIDADE_FILIAL = "Salvador"

# Mapeamento do estado civil da origem (VARCHAR2) para o destino (NUMBER).
#
# Ajuste estes valores caso o padrão utilizado no seu projeto seja outro.
ESTADO_CIVIL_MAP = {
    "S": 1,  # Solteiro(a)
    "C": 2,  # Casado(a)
    "D": 3,  # Divorciado(a)
    "V": 4,  # Viúvo(a)
    "O": 5,  # Outro
    "U": 6,  # União estável
}

# Caso o campo estado_civil contenha textos em vez de siglas.
ESTADO_CIVIL_TEXT_MAP = {
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


# ============================================================
# CONEXÃO
# ============================================================

def obter_configuracao_origem():
    user = os.getenv("ORACLE_ORIGEM_USER")
    password = os.getenv("ORACLE_ORIGEM_PASSWORD")
    dsn = os.getenv("ORACLE_ORIGEM_DSN")

    if not user or not password or not dsn:
        raise RuntimeError(
            "Defina ORACLE_ORIGEM_USER, ORACLE_ORIGEM_PASSWORD "
            "e ORACLE_ORIGEM_DSN."
        )

    return user, password, dsn


def conectar_origem():
    user, password, dsn = obter_configuracao_origem()

    print(f"Conectando ao Oracle de origem: {dsn}")
    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn
    )

    print("Conexão com a origem realizada com sucesso.")
    return connection


# ============================================================
# FUNÇÕES DE FORMATAÇÃO SQL
# ============================================================

def sql_string(value):
    """Converte texto Python para literal SQL Oracle."""
    if value is None:
        return "NULL"

    value = str(value).replace("'", "''")
    return f"'{value}'"


def sql_number(value):
    """Converte número para SQL usando ponto decimal."""
    if value is None:
        return "NULL"

    if isinstance(value, Decimal):
        value = str(value)
    else:
        value = str(value)

    return value.replace(",", ".")


def sql_date(value):
    """
    Converte datetime/date para TO_DATE(...).
    O formato é explícito para evitar problemas de NLS_DATE_FORMAT.
    """
    if value is None:
        return "NULL"

    if isinstance(value, datetime):
        texto = value.strftime("%Y-%m-%d %H:%M:%S")
        return f"TO_DATE('{texto}', 'YYYY-MM-DD HH24:MI:SS')"

    if isinstance(value, date):
        texto = value.strftime("%Y-%m-%d")
        return f"TO_DATE('{texto}', 'YYYY-MM-DD')"

    return "NULL"


def escape_comment(text):
    return str(text).replace("\n", " ").replace("\r", " ")


# ============================================================
# MAPEAMENTOS
# ============================================================

def map_estado_civil(valor):
    if valor is None:
        return None

    texto = str(valor).strip().upper()

    if texto in ESTADO_CIVIL_MAP:
        return ESTADO_CIVIL_MAP[texto]

    if texto in ESTADO_CIVIL_TEXT_MAP:
        return ESTADO_CIVIL_TEXT_MAP[texto]

    # Se já for numérico, preserva.
    try:
        return int(texto)
    except ValueError:
        return None


def id_data(data_venda):
    """
    Gera a chave da DIM_Tempo no formato YYYYMMDD.
    Exemplo:
        15/08/2026 -> 20260815
    """
    if data_venda is None:
        return None

    return int(data_venda.strftime("%Y%m%d"))


def quadrimestre(data_venda):
    """
    1 = janeiro a abril
    2 = maio a agosto
    3 = setembro a dezembro
    """
    if data_venda is None:
        return None

    return ((data_venda.month - 1) // 4) + 1


# ============================================================
# CONSULTAS NA ORIGEM
# ============================================================

def buscar_dados(connection):
    cursor = connection.cursor()

    print("Extraindo categorias...")
    cursor.execute("""
        SELECT
            id_categoria,
            nome_categoria
        FROM categorias
        ORDER BY id_categoria
    """)
    categorias = cursor.fetchall()

    print("Extraindo produtos...")
    cursor.execute("""
        SELECT
            id_produto,
            nome,
            preco,
            id_categoria
        FROM produtos
        ORDER BY id_produto
    """)
    produtos = cursor.fetchall()

    print("Extraindo clientes...")
    cursor.execute("""
        SELECT
            id_cliente,
            estado_civil
        FROM clientes
        ORDER BY id_cliente
    """)
    clientes = cursor.fetchall()

    print("Extraindo vendas e itens...")
    cursor.execute("""
        SELECT
            v.id_venda,
            v.id_cliente,
            v.data_venda,
            i.id_produto,
            i.quantidade,
            i.valor_unitario
        FROM vendas v
        INNER JOIN itens_venda i
            ON i.id_venda = v.id_venda
        ORDER BY v.id_venda, i.id_item
    """)
    vendas_itens = cursor.fetchall()

    cursor.close()

    return {
        "categorias": categorias,
        "produtos": produtos,
        "clientes": clientes,
        "vendas_itens": vendas_itens,
    }


# ============================================================
# GERAÇÃO DOS INSERTS
# ============================================================

def gerar_dim_produto(dados, arquivo):
    arquivo.write("\n-- ====================================================\n")
    arquivo.write("-- DIM_PRODUTO\n")
    arquivo.write("-- ====================================================\n")

    for id_produto, nome, preco, id_categoria in dados["produtos"]:
        arquivo.write(
            "INSERT INTO DIM_Produto "
            "(ID_Produto, Categoria, Valor) VALUES "
            f"({sql_number(id_produto)}, "
            f"{sql_number(id_categoria)}, "
            f"{sql_number(preco)});\n"
        )


def gerar_dim_cliente(dados, arquivo):
    arquivo.write("\n-- ====================================================\n")
    arquivo.write("-- DIM_CLIENTE\n")
    arquivo.write("-- ====================================================\n")

    for id_cliente, estado_civil in dados["clientes"]:
        estado = map_estado_civil(estado_civil)

        arquivo.write(
            "INSERT INTO DIM_Cliente "
            "(ID_Cliente, Estado_Civil) VALUES "
            f"({sql_number(id_cliente)}, "
            f"{sql_number(estado)});\n"
        )


def gerar_dim_filial(arquivo):
    arquivo.write("\n-- ====================================================\n")
    arquivo.write("-- DIM_FILIAL\n")
    arquivo.write("-- ====================================================\n")

    arquivo.write(
        "INSERT INTO DIM_Filial "
        "(ID_Filial, Nome, Cidade) VALUES "
        f"({ID_FILIAL_SALVADOR}, "
        f"{sql_string(NOME_FILIAL)}, "
        f"{sql_string(CIDADE_FILIAL)});\n"
    )


def gerar_dim_tempo(dados, arquivo):
    arquivo.write("\n-- ====================================================\n")
    arquivo.write("-- DIM_TEMPO\n")
    arquivo.write("-- ====================================================\n")

    datas = {}

    for row in dados["vendas_itens"]:
        _, _, data_venda, _, _, _ = row

        if data_venda is not None:
            chave = id_data(data_venda)
            datas[chave] = (
                data_venda.year,
                quadrimestre(data_venda)
            )

    for id_data_value in sorted(datas):
        ano, quad = datas[id_data_value]

        arquivo.write(
            "INSERT INTO DIM_Tempo "
            "(ID_Data, Ano, Quadrimestre) VALUES "
            f"({id_data_value}, {ano}, {quad});\n"
        )


def gerar_fato_venda(dados, arquivo):
    """
    O modelo de origem possui uma venda com vários itens.

    Como FATO_Venda possui ID_Venda como PRIMARY KEY e não possui
    ID_Item, não é possível inserir cada item separadamente.

    Portanto, os itens da mesma venda são agregados:
        Quantidade = SUM(quantidade)
        Valor      = SUM(quantidade * valor_unitario)

    Para não duplicar ID_Venda, cada venda gera exatamente uma linha.
    """

    arquivo.write("\n-- ====================================================\n")
    arquivo.write("-- FATO_VENDA\n")
    arquivo.write("-- ====================================================\n")

    vendas = {}

    for row in dados["vendas_itens"]:
        (
            id_venda,
            id_cliente,
            data_venda,
            id_produto,
            quantidade,
            valor_unitario
        ) = row

        if id_venda not in vendas:
            vendas[id_venda] = {
                "id_cliente": id_cliente,
                "data_venda": data_venda,
                "id_produto": id_produto,
                "quantidade": 0,
                "valor": Decimal("0")
            }

        if quantidade is not None:
            vendas[id_venda]["quantidade"] += quantidade

        if quantidade is not None and valor_unitario is not None:
            vendas[id_venda]["valor"] += (
                Decimal(str(quantidade)) *
                Decimal(str(valor_unitario))
            )

    for id_venda in sorted(vendas):
        venda = vendas[id_venda]

        data_venda = venda["data_venda"]
        id_data_value = id_data(data_venda)

        arquivo.write(
            "INSERT INTO FATO_Venda "
            "(ID_Venda, ID_Produto, ID_Data, ID_Cliente, "
            "ID_Filial, Quantidade, Valor) VALUES "
            f"({sql_number(id_venda)}, "
            f"{sql_number(venda['id_produto'])}, "
            f"{sql_number(id_data_value)}, "
            f"{sql_number(venda['id_cliente'])}, "
            f"{ID_FILIAL_SALVADOR}, "
            f"{sql_number(venda['quantidade'])}, "
            f"{sql_number(venda['valor'])});\n"
        )


def gerar_script(dados, output_file):
    caminho = Path(output_file)

    with caminho.open("w", encoding="utf-8") as arquivo:
        arquivo.write("-- ====================================================\n")
        arquivo.write("-- MIGRAÇÃO ORACLE -> ORACLE\n")
        arquivo.write("-- Origem: Loja Salvador\n")
        arquivo.write("-- Destino: Modelo OLAP\n")
        arquivo.write("-- ====================================================\n\n")

        arquivo.write("SET DEFINE OFF;\n")
        arquivo.write("ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD';\n")

        gerar_dim_produto(dados, arquivo)
        gerar_dim_tempo(dados, arquivo)
        gerar_dim_cliente(dados, arquivo)
        gerar_dim_filial(arquivo)
        gerar_fato_venda(dados, arquivo)

        arquivo.write("\n-- ====================================================\n")
        arquivo.write("-- FATO_CONCORRENTE\n")
        arquivo.write("-- ====================================================\n")
        arquivo.write(
            "-- Não há tabela equivalente no DDL de origem; "
            "nenhum INSERT foi gerado.\n"
        )

        arquivo.write("\nCOMMIT;\n")
        arquivo.write("SET DEFINE ON;\n")

    return caminho


# ============================================================
# VALIDAÇÕES
# ============================================================

def validar_dados(dados):
    print("\nResumo da extração:")
    print(f"  Categorias : {len(dados['categorias'])}")
    print(f"  Produtos   : {len(dados['produtos'])}")
    print(f"  Clientes   : {len(dados['clientes'])}")
    print(f"  Itens/vendas: {len(dados['vendas_itens'])}")

    vendas_unicas = len({
        row[0] for row in dados["vendas_itens"]
    })

    print(f"  Vendas únicas: {vendas_unicas}")


# ============================================================
# MAIN
# ============================================================

def main():
    try:
        connection = conectar_origem()

        try:
            dados = buscar_dados(connection)
        finally:
            connection.close()

        validar_dados(dados)

        caminho = gerar_script(dados, OUTPUT_FILE)

        print("\nMigração concluída.")
        print(f"Arquivo SQL gerado: {caminho.resolve()}")

    except oracledb.Error as exc:
        print("\nERRO ORACLE:")
        print(exc)
        sys.exit(1)

    except Exception as exc:
        print("\nERRO:")
        print(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
