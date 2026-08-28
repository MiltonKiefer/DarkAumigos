"""Funções auxiliares de datas, números e documentos."""

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def sql_string(value: Any) -> str:
    if value is None:
        return "NULL"
    return f"'{str(value).replace(chr(39), chr(39) * 2)}'"


def sql_number(value: Any) -> str:
    if value is None:
        return "NULL"
    decimal_value = Decimal(str(value)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    result = format(decimal_value, "f").rstrip("0").rstrip(".")
    return result if result else "0"


def sql_date(value: str) -> str:
    date_obj = datetime.strptime(value, "%Y-%m-%d")
    return f"DATE '{date_obj:%Y-%m-%d}'"


def data_id(data: str) -> int:
    return int(datetime.strptime(data, "%Y-%m-%d").strftime("%Y%m%d"))


def quadrimestre(data: str) -> int:
    month = datetime.strptime(data, "%Y-%m-%d").month
    return ((month - 1) // 4) + 1


def normalizar_documentos(documentos: list[dict]) -> list[dict]:
    resultado = []
    for documento in documentos:
        documento = dict(documento)
        documento.pop("_id", None)
        resultado.append(documento)
    return resultado