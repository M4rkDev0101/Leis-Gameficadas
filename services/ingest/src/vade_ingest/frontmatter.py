"""Parser tolerante do cabeçalho YAML das normas do repositório ctresb/leis.

O cabeçalho usa um subconjunto plano de YAML (``chave: valor``). Em vez de depender
de um parser YAML completo — que aborta o lote inteiro diante de um único arquivo
malformado vindo do upstream — lemos só esse subconjunto e registramos avisos.

Regras:
- ``"texto"`` → str (escapes ``\\"`` e ``\\\\`` resolvidos)
- ``true``/``false`` → bool; ``null``/``~``/vazio → None
- ``AAAA-MM-DD`` (com ou sem aspas) → ``datetime.date`` quando a chave é de data
- demais valores → str sem aspas
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

DATE_KEYS = frozenset({"data", "data_publicacao", "baixado_em"})
_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s?(.*)$")


@dataclass
class FrontMatter:
    data: dict[str, object] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def split(text: str) -> tuple[str | None, str]:
    """Separa (cabeçalho, corpo). Sem cabeçalho (ex.: constituicao.md) → (None, texto)."""
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])
    return None, text


def _unquote(raw: str) -> str:
    inner = raw[1:-1]
    if raw[0] == '"':
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    return inner.replace("''", "'")


def _scalar(key: str, raw: str, warnings: list[str]) -> object:
    raw = raw.strip()
    if raw == "" or raw in ("null", "~"):
        return None
    quoted = len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'"
    if quoted:
        value: object = _unquote(raw)
    else:
        # comentário inline só existe fora de aspas
        raw = re.sub(r"\s+#.*$", "", raw)
        if raw == "true":
            return True
        if raw == "false":
            return False
        value = raw
    if key in DATE_KEYS and isinstance(value, str):
        m = _DATE_RE.match(value)
        if m:
            try:
                return dt.date(int(m[1]), int(m[2]), int(m[3]))
            except ValueError:
                warnings.append(f"{key}: data inválida {value!r}")
    return value


def parse(header: str) -> FrontMatter:
    fm = FrontMatter()
    for n, line in enumerate(header.split("\n"), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _KEY_RE.match(line)
        if not m:
            fm.warnings.append(f"linha {n} ignorada: {line[:80]!r}")
            continue
        key, raw = m[1], m[2]
        if key in fm.data:
            fm.warnings.append(f"chave duplicada: {key}")
        fm.data[key] = _scalar(key, raw, fm.warnings)
    return fm
