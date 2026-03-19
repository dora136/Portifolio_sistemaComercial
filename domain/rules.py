from __future__ import annotations

from datetime import date, datetime
import json
from typing import Any, Optional


def parse_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "t", "yes", "y", "sim"}:
            return True
        if normalized in {"0", "false", "f", "no", "n", "nao"}:
            return False
    return None


def normalize_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value.strip() or None
    return None


def parse_aplicacoes_json(value: Any) -> list[str]:
    if value in (None, "", "null"):
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, dict):
            parsed = parsed.get("aplicacoes_basicas", [])
        if not isinstance(parsed, list):
            return []
        return [str(item) for item in parsed]
    if isinstance(value, dict):
        parsed = value.get("aplicacoes_basicas", [])
        if not isinstance(parsed, list):
            return []
        return [str(item) for item in parsed]
    return []


def parse_kanban_json(value: Any) -> Optional[list[dict]]:
    """Parse kanban_json column into a list of etapas."""
    if value in (None, "", "null"):
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed.get("etapas", [])
        if isinstance(parsed, list):
            return parsed
        return None
    if isinstance(value, dict):
        return value.get("etapas", [])
    return None


def parse_registro_info_json(value: Any) -> list[dict]:
    """Parse registro_info_json into a list of fields."""
    if value in (None, "", "null"):
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parse_registro_info_json(parsed)
    if isinstance(value, dict):
        fields = value.get("fields")
        if isinstance(fields, list):
            return [item for item in fields if isinstance(item, dict)]
        return []
    return []


def normalize_cnpj(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        value = str(int(value))
    if not isinstance(value, str):
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return None
    if len(digits) != 14:
        return digits
    return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"
