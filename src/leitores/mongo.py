"""Leitura das coleções do MongoDB Atlas."""

from pymongo import MongoClient

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