"""Interface de linha de comando da pipeline."""

import argparse
import os
from pathlib import Path

from src.leitores.dados import carregar_dados
from src.sql.gerador import gerar_sql
from src.transformacoes.mapas import criar_mapa_categorias, criar_mapa_estado_civil


def main() -> None:
    parser = argparse.ArgumentParser(description="Converte dados MongoDB Atlas em INSERTs Oracle.")
    parser.add_argument(
        "--json-dir",
        help="Diretório contendo os 3 JSONs de exemplo. Se omitido, conecta ao MongoDB Atlas.",
    )
    parser.add_argument(
        "--output",
        default=os.getenv("OUTPUT_SQL", "carga_oracle.sql"),
        help="Arquivo SQL de saída.",
    )
    parser.add_argument(
        "--postgresql",
        action="store_true",
        help="Extrai do PostgreSQL/Supabase em vez do MongoDB/JSON.",
    )
    parser.add_argument(
        "--load-oracle",
        action="store_true",
        help="Após gerar o SQL, executar o script no banco Oracle usando vars ORACLE_*.",
    )
    args = parser.parse_args()

    if args.postgresql:
        from src.leitores.postgresql import salvar_sql_postgresql
        from src.sql.loader import execute_file

        caminho = salvar_sql_postgresql(args.output)
        print(f"Conversão PostgreSQL concluída! SQL gerado: {caminho.resolve()}")
        if args.load_oracle:
            print("Executando carga no Oracle...")
            execute_file(caminho)
            print("Carga no Oracle concluída.")
        return

    dados = carregar_dados(args)
    sql = gerar_sql(dados)
    caminho_saida = Path(args.output)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text(sql, encoding="utf-8")
    quantidade_itens = sum(len(pedido.get("itens", [])) for pedido in dados["pedidos"])
    print("Conversão concluída!")
    print(f"Clientes:     {len(dados['clientes'])}")
    print(f"Produtos:     {len(dados['produtos'])}")
    print(f"Pedidos:      {len(dados['pedidos'])}")
    print(f"Itens/vendas: {quantidade_itens}")
    print(f"SQL gerado:   {caminho_saida.resolve()}")
    mapa_categorias = criar_mapa_categorias(dados["produtos"])
    mapa_estado_civil = criar_mapa_estado_civil(dados["clientes"])
    if mapa_categorias:
        print("\nMapa Categoria (texto -> número):")
        for texto, codigo in mapa_categorias.items():
            print(f"  {codigo}: {texto}")
    if mapa_estado_civil:
        print("\nMapa Estado_Civil (texto -> número):")
        for texto, codigo in mapa_estado_civil.items():
            print(f"  {codigo}: {texto}")
    if args.load_oracle:
        from src.sql.loader import execute_file

        print("Executando carga no Oracle...")
        execute_file(caminho_saida)
        print("Carga no Oracle concluída.")