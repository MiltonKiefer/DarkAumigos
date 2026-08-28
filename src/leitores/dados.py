"""Orquestração das fontes de entrada."""

import argparse
import os
from pathlib import Path

from src.leitores.json import carregar_json
from src.leitores.mongo import carregar_do_mongo


def carregar_dados(args: argparse.Namespace) -> dict[str, list[dict]]:
    if args.json_dir:
        pasta = Path(args.json_dir)
        concorrentes = pasta / "08_Feira_concorrentes.json"
        return {
            "clientes": carregar_json(pasta / "05_Feira_Clientes.json"),
            "produtos": carregar_json(pasta / "06_Feira_Produtos.json"),
            "pedidos": carregar_json(pasta / "07_Feira_Pedidos.json"),
            "concorrentes": carregar_json(concorrentes) if concorrentes.exists() else [],
        }
    uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("MONGODB_DB")
    if not uri:
        raise RuntimeError("Defina a variável de ambiente MONGODB_URI.")
    if not database_name:
        raise RuntimeError("Defina a variável de ambiente MONGODB_DB.")
    return carregar_do_mongo(uri, database_name)