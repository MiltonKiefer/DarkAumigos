import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO DOS CAMINHOS
# ============================================================

# Estrutura:
#
# DarkAumigos/
# ├── Dados/
# ├── Output/
# └── src/
#     └── leitores/
#         └── concorrente.py

# Caminho da raiz do projeto
RAIZ_PROJETO = Path(__file__).resolve().parent.parent.parent

# Pasta onde estão os arquivos Excel
PASTA_DADOS = RAIZ_PROJETO / "Dados"

# Pasta onde serão gerados os arquivos SQL
PASTA_OUTPUT = RAIZ_PROJETO / "Output"

# Nome do arquivo SQL de saída
ARQUIVO_SAIDA = PASTA_OUTPUT / "insert_fato_concorrente.sql"

# Tabela Oracle
TABELA = "FATO_CONCORRENTE"


# ============================================================
# CONVERSÃO DOS MESES
# ============================================================

MESES = {
    "Jan": 1,
    "Fev": 2,
    "Mar": 3,
    "Abr": 4,
    "Mai": 5,
    "Jun": 6,
    "Jul": 7,
    "Ago": 8,
    "Set": 9,
    "Out": 10,
    "Nov": 11,
    "Dez": 12,

    "Janeiro": 1,
    "Fevereiro": 2,
    "Março": 3,
    "Marco": 3,
    "Abril": 4,
    "Maio": 5,
    "Junho": 6,
    "Julho": 7,
    "Agosto": 8,
    "Setembro": 9,
    "Outubro": 10,
    "Novembro": 11,
    "Dezembro": 12
}


# ============================================================
# LOCALIZAR ARQUIVO EXCEL
# ============================================================

def localizar_excel():

    if not PASTA_DADOS.exists():
        raise FileNotFoundError(
            f"A pasta Dados não foi encontrada:\n"
            f"{PASTA_DADOS}"
        )

    arquivos_excel = list(
        PASTA_DADOS.glob("*.xlsx")
    )

    if not arquivos_excel:
        raise FileNotFoundError(
            f"Nenhum arquivo Excel (.xlsx) foi encontrado em:\n"
            f"{PASTA_DADOS}"
        )

    # Se houver mais de um Excel
    if len(arquivos_excel) > 1:

        print("\nForam encontrados vários arquivos Excel:")

        for i, arquivo in enumerate(
            arquivos_excel,
            start=1
        ):
            print(
                f"{i} - {arquivo.name}"
            )

        escolha = int(
            input(
                "\nDigite o número do arquivo "
                "que deseja utilizar: "
            )
        )

        if escolha < 1 or escolha > len(arquivos_excel):
            raise ValueError(
                "Opção inválida."
            )

        arquivo_excel = arquivos_excel[
            escolha - 1
        ]

    else:

        arquivo_excel = arquivos_excel[0]

    print(
        f"\nArquivo Excel encontrado:"
    )

    print(arquivo_excel)

    return arquivo_excel


# ============================================================
# CONVERSÃO DE NÚMEROS
# ============================================================

def converter_numero(valor):

    if pd.isna(valor):
        return "NULL"

    try:

        valor = float(valor)

        # Evita valores como 1000.0
        if valor.is_integer():
            return str(int(valor))

        return f"{valor:.2f}"

    except (ValueError, TypeError):

        return "NULL"


# ============================================================
# LEITURA DO EXCEL
# ============================================================

def ler_excel(arquivo_excel):

    df = pd.read_excel(
        arquivo_excel
    )

    print("\nColunas encontradas:")

    for coluna in df.columns:
        print(f"- {coluna}")

    # Colunas obrigatórias
    colunas_obrigatorias = [
        "Ano",
        "Mês",
        "Vendas (R$)"
    ]

    for coluna in colunas_obrigatorias:

        if coluna not in df.columns:

            raise ValueError(
                f"\nA coluna obrigatória "
                f"'{coluna}' não foi encontrada "
                f"no Excel."
            )

    return df


# ============================================================
# GERAÇÃO DOS INSERTS
# ============================================================

def gerar_inserts(df):

    inserts = []

    # Cabeçalho do SQL
    inserts.append(
        "-- ===================================================="
    )

    inserts.append(
        "-- INSERTS - FATO_CONCORRENTE"
    )

    inserts.append(
        "-- Arquivo gerado automaticamente pelo Python"
    )

    inserts.append(
        "-- ===================================================="
    )

    inserts.append("")

    for indice, linha in df.iterrows():

        # ----------------------------------------------------
        # ID_CONCORRENTE
        # ----------------------------------------------------

        id_concorrente = indice + 1

        # ----------------------------------------------------
        # ID_DATA
        #
        # ATENÇÃO:
        # Deve corresponder aos IDs existentes na DIM_TEMPO.
        # ----------------------------------------------------

        id_data = indice + 1

        # ----------------------------------------------------
        # ANO
        # ----------------------------------------------------

        ano = int(
            linha["Ano"]
        )

        # ----------------------------------------------------
        # MÊS
        # ----------------------------------------------------

        mes_texto = str(
            linha["Mês"]
        ).strip()

        if mes_texto not in MESES:

            raise ValueError(
                f"Mês inválido na linha "
                f"{indice + 2}: "
                f"{mes_texto}"
            )

        mes = MESES[
            mes_texto
        ]

        # ----------------------------------------------------
        # VENDAS
        # ----------------------------------------------------

        vendas = converter_numero(
            linha["Vendas (R$)"]
        )

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        sql = (
            f"INSERT INTO {TABELA} "
            f"(ID_CONCORRENTE, ID_DATA, ANO, MES, DESCRICAO) "
            f"VALUES "
            f"({id_concorrente}, "
            f"{id_data}, "
            f"{ano}, "
            f"{mes}, "
            f"{vendas});"
        )

        inserts.append(sql)

    return inserts


# ============================================================
# SALVAR ARQUIVO SQL
# ============================================================

def salvar_sql(inserts):

    # Cria a pasta Output caso ela ainda não exista
    PASTA_OUTPUT.mkdir(
        parents=True,
        exist_ok=True
    )

    # Cria o arquivo SQL
    with open(
        ARQUIVO_SAIDA,
        "w",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(
            "\n".join(inserts)
        )

    print("\n==============================================")
    print("      ARQUIVO SQL GERADO COM SUCESSO")
    print("==============================================")

    print(
        f"\nArquivo gerado em:"
    )

    print(
        ARQUIVO_SAIDA
    )

    print(
        f"\nQuantidade de INSERTs: "
        f"{len(inserts) - 5}"
    )


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    try:

        print("==============================================")
        print("   GERADOR DE INSERTS - CONCORRENTE")
        print("==============================================")

        # ----------------------------------------------------
        # Localiza o Excel
        # ----------------------------------------------------

        arquivo_excel = localizar_excel()

        # ----------------------------------------------------
        # Lê o Excel
        # ----------------------------------------------------

        print(
            "\nLendo arquivo Excel..."
        )

        df = ler_excel(
            arquivo_excel
        )

        print(
            f"\nRegistros encontrados: "
            f"{len(df)}"
        )

        # ----------------------------------------------------
        # Gera os INSERTs
        # ----------------------------------------------------

        print(
            "\nGerando INSERTs..."
        )

        inserts = gerar_inserts(
            df
        )

        # ----------------------------------------------------
        # Salva na pasta Output
        # ----------------------------------------------------

        salvar_sql(
            inserts
        )

    except Exception as erro:

        print("\n==============================================")
        print("ERRO")
        print("==============================================")

        print(
            erro
        )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()
