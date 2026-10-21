"""Parser de precedentes (súmulas, temas, OJs) da pasta ``jurisprudencia/``.

Precedentes não têm artigos. O que interessa ao estudo:

* o **enunciado** (STJ: seção "Enunciado"; BNP/CNJ: "## Questão" e "## Tese");
* o **ramo e tema** (STJ: "DIREITO PENAL - LEI MARIA DA PENHA");
* as **referências legislativas** (STJ: ``LEG:FED LEI:011340 ANO:2006`` + ``ART:00005``),
  que ligam o precedente aos dispositivos que ele interpreta.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .structure import ParsedBody, Unit, fold

_STJ_SECTIONS = (
    "Enunciado", "Órgão Julgador", "Data da Decisão", "Fonte", "Referências Legislativas",
    "Precedentes", "Excerto dos Precedentes Originários", "Observação", "Data da Publicação",
)
_SECTION_FOLDED = {fold(s): s for s in _STJ_SECTIONS}
_PAGE_RE = re.compile(r"^Página \d+ de \d+$")
_RAMO_RE = re.compile(r"^DIREITO [A-ZÀ-Ú ,]+?(?:\s+-\s+(?P<tema>.+))?$")
_LEG_RE = re.compile(r"LEG:(?P<esfera>[A-Z]{3})\s+(?P<tipo>[A-Z]{3}):(?P<num>[\d*]+)\s+ANO:(?P<ano>\d{4})")
_ART_RE = re.compile(r"ART:(?P<art>\d+)(?P<rest>(?:\s+(?:PAR|INC|LET|ITEM):[\w*]+)*)")

# códigos do STJ → tipo canônico do acervo
LEG_TIPOS = {
    "CFB": "Constituição", "LEI": "Lei Ordinária", "LCP": "Lei Complementar", "DEL": "Decreto-Lei",
    "MPR": "Medida Provisória", "DEC": "Decreto", "EMC": "Emenda Constitucional", "SUM": "Súmula",
}

_AREA_BY_RAMO = {
    "penal": "penal", "processual penal": "processo-penal", "civil": "civil",
    "processual civil": "processo-civil", "tributario": "tributario", "administrativo": "administrativo",
    "previdenciario": "previdenciario", "do consumidor": "consumidor", "constitucional": "constitucional",
    "do trabalho": "trabalho", "processual do trabalho": "processo-trabalho", "empresarial": "empresarial",
    "comercial": "empresarial", "ambiental": "ambiental", "eleitoral": "eleitoral", "financeiro": "financeiro",
    "internacional": "internacional", "militar": "militar", "falimentar": "empresarial",
}


@dataclass
class LegalRef:
    tipo: str  # tipo canônico
    numero: str | None  # None para a CF
    ano: int
    caminho: str | None  # "art-226/par-8"; None quando cita a norma inteira


@dataclass
class Precedent:
    enunciado: str = ""
    tese: str | None = None
    ramo: str | None = None
    tema: str | None = None
    area: str | None = None
    orgao_julgador: str | None = None
    referencias: list[LegalRef] = field(default_factory=list)


_LEVEL = {"PAR": 1, "INC": 2, "LET": 3, "ITEM": 4}


def _segment(kind: str, val: str) -> str:
    if kind == "PAR":
        return "par-unico" if fold(val) == "unico" else f"par-{int(val)}" if val.isdigit() else f"par-{val.lower()}"
    if kind == "INC":  # o STJ escreve o inciso em arábico (INC:00002) ou romano
        return f"inc-{_to_roman(int(val)).lower()}" if val.isdigit() else f"inc-{val.lower()}"
    if kind == "LET":
        return f"ali-{val.lower()}"
    return f"item-{int(val)}" if val.isdigit() else f"item-{val.lower()}"


def _paths_from(art: str, rest: str) -> list[str]:
    """``ART:5 INC:34 LET:A INC:55`` → ["art-5/inc-xxxiv/ali-a", "art-5/inc-lv"].

    Qualificadores do mesmo nível ou de nível superior ao último fecham o caminho
    corrente: é uma lista, não um aninhamento.
    """
    base = f"art-{int(art)}"
    paths: list[str] = []
    stack: list[tuple[int, str]] = []
    for kind, val in re.findall(r"(PAR|INC|LET|ITEM):([\w*]+)", rest):
        level = _LEVEL[kind]
        if stack and stack[-1][0] >= level:
            paths.append("/".join([base, *(s for _, s in stack)]))
            while stack and stack[-1][0] >= level:
                stack.pop()
        stack.append((level, _segment(kind, val)))
    paths.append("/".join([base, *(s for _, s in stack)]))
    return paths


def _to_roman(n: int) -> str:
    out = ""
    for v, s in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"),
                 (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out, n = out + s, n - v
    return out


def parse_references(block: str) -> list[LegalRef]:
    refs: list[LegalRef] = []
    # cada referência começa em "LEG:" e vai até a próxima
    chunks = re.split(r"(?=LEG:[A-Z]{3}\s)", block)
    for ch in chunks:
        m = _LEG_RE.search(ch)
        if not m:
            continue
        tipo = LEG_TIPOS.get(m["tipo"], m["tipo"])
        numero = None if tipo == "Constituição" or "*" in m["num"] else str(int(m["num"]))
        arts = list(_ART_RE.finditer(ch[m.end():]))
        if not arts:
            refs.append(LegalRef(tipo, numero, int(m["ano"]), None))
        for a in arts:
            for path in _paths_from(a["art"], a["rest"]):
                refs.append(LegalRef(tipo, numero, int(m["ano"]), path))
    return refs


def parse(body: str) -> tuple[ParsedBody, Precedent]:
    p = Precedent()
    title = None
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in body.split("\n"):
        line = raw.strip()
        if not line or _PAGE_RE.match(line):
            continue
        if line.startswith("```"):  # bloco JSON do registro original do CNJ: fim do conteúdo útil
            break
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h:
            if h[1] == "#" and title is None:
                title = h[2].strip()
                continue
            current = h[2].strip()
            if fold(current).startswith("registro original"):
                break
            sections.setdefault(current, [])
            continue
        if fold(line) in _SECTION_FOLDED:
            current = _SECTION_FOLDED[fold(line)]
            sections.setdefault(current, [])
            continue
        if current is None:
            m = _RAMO_RE.match(line)
            if m and line.upper() == line:
                ramo = line.split(" - ")[0].strip()
                p.ramo, p.tema = ramo, (m["tema"] or None)
                p.area = _AREA_BY_RAMO.get(fold(ramo).removeprefix("direito ").strip())
            continue
        sections[current].append(line)

    def text(name: str) -> str | None:
        lines = sections.get(name)
        if not lines:
            return None
        t = re.sub(r"\s+", " ", " ".join(lines)).strip()
        return None if fold(t) in ("nao informado", "") else t

    p.enunciado = text("Enunciado") or text("Questão") or ""
    p.tese = text("Tese")
    p.orgao_julgador = text("Órgão Julgador")
    if "Referências Legislativas" in sections:
        p.referencias = parse_references("\n".join(sections["Referências Legislativas"]))

    root = Unit("raiz", "", "")
    if p.enunciado:
        root.children.append(Unit("enunciado", "Enunciado", "enunciado", text=p.enunciado, path="enunciado"))
    if p.tese:
        root.children.append(Unit("tese", "Tese", "tese", text=p.tese, path="tese"))
    return ParsedBody(title=title, preamble="", root=root), p
