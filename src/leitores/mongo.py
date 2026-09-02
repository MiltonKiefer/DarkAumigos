"""Leitura das coleções do MongoDB Atlas."""

import argparse
import os
import sys
from pathlib import Path

from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import DEFAULT_COLLECTIONS
from src.utilitarios import normalizar_documentos


def carregar_do_mongo(uri: str, database_name: str) -> dict[str, list[dict]]:
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    try:
        client.admin.command("ping")
        db = client[database_name]
        colecoes = set(db.list_collection_names())
        if not colecoes:
            raise RuntimeError(
                f"O banco '{database_name}' não possui coleções. "
                "Verifique MONGODB_DB no .env."
            )
        dados = {}
        for chave, nome_colecao in DEFAULT_COLLECTIONS.items():
            if nome_colecao in colecoes:
                documentos = normalizar_documentos(
                    list(db[nome_colecao].find({}))
                )
                dados[chave] = documentos
                print(
                    f"Coleção '{nome_colecao}' -> {chave}: "
                    f"{len(documentos)} documentos"
                )
            else:
                dados[chave] = []
                print(f"Coleção '{nome_colecao}' não encontrada (ok se opcional).")
        return dados
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrai somente o MongoDB e gera a carga SQL Oracle."
    )
    parser.add_argument(
        "--output",
        default=os.getenv("OUTPUT_SQL", "carga_oracle_mongo.sql"),
        help="Arquivo SQL de saída.",
    )
    args = parser.parse_args()

    uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("MONGODB_DB")
    if not uri or not database_name:
        raise RuntimeError("Defina MONGODB_URI e MONGODB_DB no arquivo .env.")

    from src.sql.gerador import gerar_sql

    dados = carregar_do_mongo(uri, database_name)
    caminho_saida = Path(args.output)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text(gerar_sql(dados), encoding="utf-8")
    print(f"SQL MongoDB gerado: {caminho_saida.resolve()}")


if __name__ == "__main__":
    main()