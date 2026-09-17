"""Leitura dos arquivos JSON locais."""

import json
from pathlib import Path


def carregar_json(caminho: Path) -> list[dict]:
    with caminho.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    if not isinstance(dados, list):
        raise ValueError(f"O arquivo {caminho} deve conter uma lista JSON.")
    return dados