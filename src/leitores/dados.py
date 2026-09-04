"""Orquestração das fontes de entrada."""

import argparse
import os
from pathlib import Path

from src.leitores.json_reader import carregar_json
from src.leitores.mongo import carregar_do_mongo
from src.leitores.Excel import PASTA_DADOS, carregar_dados_excel


def _carregar_concorrentes_excel() -> list[dict]:
    if not list(PASTA_DADOS.glob("*.xlsx")):
        return []
    return carregar_dados_excel()


def carregar_dados(args: argparse.Namespace) -> dict[str, list[dict]]:
    if args.json_dir:
        pasta = Path(args.json_dir)
        concorrentes = pasta / "08_Feira_concorrentes.json"
        dados = {
            "clientes": carregar_json(pasta / "05_Feira_Clientes.json"),
            "produtos": carregar_json(pasta / "06_Feira_Produtos.json"),
            "pedidos": carregar_json(pasta / "07_Feira_Pedidos.json"),
            "concorrentes": carregar_json(concorrentes) if concorrentes.exists() else [],
        }
    else:
        uri = os.getenv("MONGODB_URI")
        database_name = os.getenv("MONGODB_DB")
        if not uri:
            raise RuntimeError("Defina a variável de ambiente MONGODB_URI.")
        if not database_name:
            raise RuntimeError("Defina a variável de ambiente MONGODB_DB.")
        dados = carregar_do_mongo(uri, database_name)

    dados["concorrentes"] = _carregar_concorrentes_excel() or dados.get("concorrentes", [])
    return dados