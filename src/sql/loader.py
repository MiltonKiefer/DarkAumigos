"""Execução de scripts SQL no banco Oracle.

Fornece funções para executar SQL gerado pela pipeline diretamente em um
banco Oracle. As credenciais são lidas do arquivo `.env` (variáveis de
ambiente): `ORACLE_USER`, `ORACLE_PASSWORD` e `ORACLE_DSN` ou `ORACLE_HOST`,
`ORACLE_PORT` e `ORACLE_SERVICE`.
"""

from __future__ import annotations

import os
import logging
import re
from pathlib import Path
from typing import Optional

import oracledb
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
LOGGER = logging.getLogger(__name__)


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
    LOGGER.info("Conectando ao Oracle: usuario=%s, dsn=%s", user, dsn)
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    LOGGER.info("Conexão Oracle estabelecida.")
    return connection


def _split_statements(script: str) -> list[str]:
    statements = []
    for parte in script.split(";"):
        linhas = [
            linha for linha in parte.splitlines()
            if not linha.lstrip().startswith("--")
        ]
        statement = "\n".join(linhas).strip()
        if statement and statement.upper() != "COMMIT":
            statements.append(statement)
    return statements


def _resumo_statement(statement: str) -> str:
    primeira_linha = " ".join(statement.split())[:160]
    match = re.search(r"INSERT\s+INTO\s+([A-Z0-9_$#]+)", statement, re.IGNORECASE)
    return f"INSERT INTO {match.group(1)}" if match else primeira_linha


def execute_sql(script: str) -> None:
    """Executa um script SQL (texto) no Oracle.

    O script pode conter vários comandos separados por `;`.
    """
    conn = None
    statements = _split_statements(script)
    LOGGER.info("Script recebido: %d comandos SQL.", len(statements))
    try:
        conn = _connect()
        cur = conn.cursor()
        for indice, stmt in enumerate(statements, 1):
            LOGGER.info("Executando comando %d/%d: %s", indice, len(statements), _resumo_statement(stmt))
            try:
                cur.execute(stmt)
            except Exception:
                LOGGER.exception("Falha no comando %d/%d: %s", indice, len(statements), _resumo_statement(stmt))
                raise
        conn.commit()
        LOGGER.info("COMMIT concluído: %d comandos executados.", len(statements))
    except Exception:
        if conn is not None:
            conn.rollback()
            LOGGER.warning("ROLLBACK executado após falha.")
        raise
    finally:
        if conn is not None:
            conn.close()
            LOGGER.info("Conexão Oracle encerrada.")


def execute_file(path: str | Path) -> None:
    """Lê um arquivo SQL e executa seu conteúdo no Oracle."""
    path = Path(path)
    if not path.is_absolute() and path.parts[:1] != ("output",):
        path = BASE_DIR / "output" / path
    LOGGER.info("Lendo arquivo SQL: %s", path.resolve())
    script = path.read_text(encoding="utf-8")
    LOGGER.info("Arquivo SQL lido: %d bytes.", len(script.encode("utf-8")))
    execute_sql(script)
