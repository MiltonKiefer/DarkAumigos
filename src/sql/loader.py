"""Execução de scripts SQL no banco Oracle.

Fornece funções para executar SQL gerado pela pipeline diretamente em um
banco Oracle. As credenciais são lidas do arquivo `.env` (variáveis de
ambiente): `ORACLE_USER`, `ORACLE_PASSWORD` e `ORACLE_DSN` ou `ORACLE_HOST`,
`ORACLE_PORT` e `ORACLE_SERVICE`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import oracledb


def _env(nome: str, padrao: Optional[str] = None) -> Optional[str]:
    valor = os.getenv(nome, padrao)
    return valor.strip() if valor else valor


def _build_dsn() -> str:
    dsn = _env("ORACLE_DSN")
    if dsn:
        return dsn
    host = _env("ORACLE_HOST")
    port = _env("ORACLE_PORT", "1521")
    service = _env("ORACLE_SERVICE")
    if not host or not service:
        raise RuntimeError(
            "Defina ORACLE_DSN ou (ORACLE_HOST e ORACLE_SERVICE) no arquivo .env."
        )
    return f"{host}:{port}/{service}"


def _connect():
    user = _env("ORACLE_USER")
    password = _env("ORACLE_PASSWORD")
    if not user or not password:
        raise RuntimeError("Defina ORACLE_USER e ORACLE_PASSWORD no arquivo .env.")
    dsn = _build_dsn()
    return oracledb.connect(user=user, password=password, dsn=dsn)


def _split_statements(script: str) -> list[str]:
    parts = [p.strip() for p in script.split(";")]
    return [p for p in parts if p]


def execute_sql(script: str) -> None:
    """Executa um script SQL (texto) no Oracle.

    O script pode conter vários comandos separados por `;`.
    """
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        for stmt in _split_statements(script):
            cur.execute(stmt)
        conn.commit()
    finally:
        if conn is not None:
            conn.close()


def execute_file(path: Path) -> None:
    """Lê um arquivo SQL e executa seu conteúdo no Oracle."""
    script = path.read_text(encoding="utf-8")
    execute_sql(script)
