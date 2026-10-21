"""Parser estrutural: transforma o corpo Markdown de uma norma em árvore de dispositivos.

Hierarquia produzida::

    divisão (PARTE > LIVRO > TÍTULO > SUBTÍTULO > CAPÍTULO > SEÇÃO > SUBSEÇÃO)
      └─ artigo (caput no próprio nó)
           ├─ parágrafo (§ 1º, § 1º-A, Parágrafo único)
           │    └─ inciso (I, II-A) └─ alínea (a, b) └─ item (1, 2)
           ├─ inciso …
           └─ pena (linhas "Pena - …", valiosas para questões de concurso)

Decisões que vêm da análise do acervo (ver docs/01-analise-repositorio.md):

* O nível de ``#`` **não** é confiável (TÍTULO é ``##`` na CF e ``###`` no Código Civil);
  a posição na hierarquia vem da palavra-chave da divisão.
* Leis que alteram outras citam artigos entre aspas (``“Art. 1º-A …”``); esses trechos são
  conteúdo do artigo que altera, não artigos da norma.
* A CF tem o ADCT com numeração própria: ele abre um novo *escopo* (``adct/art-1``).
* Rubricas (epígrafes como "Lei penal no tempo") ficam numa linha curta antes do artigo.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# ---------------------------------------------------------------- modelo


@dataclass
class Note:
    kind: str  # redacao | inclusao | revogacao | veto | vide | vigencia | renumeracao | redacao_anterior | outro
    text: str
    ref: str | None = None  # norma alteradora citada, ex.: "Lei nº 13.654, de 23/4/2018"


@dataclass
class Unit:
    kind: str  # divisao | artigo | paragrafo | inciso | alinea | item | pena | preambulo
    label: str  # rótulo como aparece: "Art. 157", "§ 1º-A", "II", "a"
    key: str  # segmento do caminho: "art-157", "par-1a", "inc-ii"
    text: str = ""
    div_type: str | None = None  # para divisões: parte, livro, titulo, capitulo, secao…
    rubrica: str | None = None
    notes: list[Note] = field(default_factory=list)
    revoked: bool = False
    vetoed: bool = False
    line: int = 0
    children: list["Unit"] = field(default_factory=list)
    path: str = ""

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


@dataclass
class ParsedBody:
    title: str | None
    preamble: str
    root: Unit
    warnings: list[str] = field(default_factory=list)

    def articles(self) -> list[Unit]:
        return [u for u in self.root.walk() if u.kind == "artigo"]


# ---------------------------------------------------------------- padrões

DIV_RANK = {
    "parte": 1,
    "livro": 2,
    "titulo": 3,
    "subtitulo": 4,
    "capitulo": 5,
    "secao": 6,
    "subsecao": 7,
}

_DIV_RE = re.compile(
    r"^(?P<kw>PARTE|LIVRO|T[ÍI]TULO|SUBT[ÍI]TULO|CAP[ÍI]TULO|SE[ÇC][ÃA]O|SUBSE[ÇC][ÃA]O)"
    r"(?P<num>\s+(?:[IVXLCDM]+|[ÚU]NIC[OA]|PRELIMINAR|GERAL|ESPECIAL|\d+)(?:-[A-Z])?)?\b"
    r"(?P<rest>.*)$",
    re.IGNORECASE,
)
_SCOPE_RE = re.compile(r"^ATO DAS DISPOSI[ÇC][ÕO]ES CONSTITUCIONAIS TRANSIT[ÓO]RIAS", re.I)

_NUM = r"(?P<num>\d{1,3}(?:\.\d{3})+|\d+)"
_ORD = r"(?:\s*(?:[º°ª]|o(?![a-zà-ú])))?"
# sufixo colado ao número ("1º-A", "359-M-A"); com espaço seria separador: "Art. 242 - A lei"
_SUF = r"(?:-(?P<suf>[A-Z]{1,2}(?:-[A-Z]{1,2})*)(?![\wÀ-ú]))?"
_TAIL = r"\s*\.?\s*(?:\*\*)?\s*(?:[-–—.:]\s*)?(?:\*\*)?\s*(?P<rest>.*)$"

_ART_RE = re.compile(r"^(?:\*\*)?\s*(?:Art\.?|ART\.?|Artigo|ARTIGO)\s*" + _NUM + _ORD + _SUF + _TAIL)
_PAR_RE = re.compile(r"^(?:\*\*)?\s*§\s*" + _NUM + _ORD + _SUF + _TAIL)
_PAR_UNICO_RE = re.compile(
    r"^(?:\*\*)?\s*Par[áa]grafo\s+[úu]nico" + _TAIL, re.IGNORECASE
)
_INC_RE = re.compile(
    r"^(?:\*\*)?(?P<num>[IVXLCDM]+)(?:-(?P<suf>[A-Z])(?![\wÀ-ú])(?:\*\*)?\s*[-–—)]?|(?:\*\*)?\s*[-–—)])\s*(?P<rest>.*)$"
)
# inciso sem travessão ("V os conflitos…", CF art. 114): só aceito se continuar a sequência
_INC_BARE_RE = re.compile(r"^(?P<num>[IVXLCDM]+)(?:-(?P<suf>[A-Z]))?\s+(?P<rest>[a-zà-ú].*)$")
_ALI_RE = re.compile(r"^(?:\*\*)?(?P<num>[a-z])(?:-(?P<suf>[a-zA-Z]))?\s*\)\s*(?:\*\*)?\s*(?P<rest>.*)$")
_ITEM_RE = re.compile(r"^(?P<num>\d{1,2})\s*[.)]\s+(?P<rest>.*)$")
_PENA_RE = re.compile(r"^(?:\*\*)?Pena\s*(?:\*\*)?\s*[-–—:]\s*(?P<rest>.*)$", re.IGNORECASE)

_NOTE_RE = re.compile(
    r"\((?P<body>[^()]*?(?:reda[çc][ãa]o dad|acrescid|inclu[íi]d|revogad|vide\b|vig[êe]ncia|"
    r"renumerad|suprimid|vetad|regulamenta|convers[ãa]o)[^()]*)\)",
    re.IGNORECASE,
)
_STRUCK_RE = re.compile(r"~~(.+?)~~|<(?:s|del|strike)>(.+?)</(?:s|del|strike)>", re.S)
_REF_RE = re.compile(
    r"((?:Lei(?: Complementar)?|Decreto(?:-Lei)?|Medida Provis[óo]ria|Emenda Constitucional"
    r"(?: de Revis[ãa]o)?|Resolu[çc][ãa]o)\s+n[ºo°]?\.?\s*[\d.]+(?:-[A-Z])?(?:,\s*de\s*[^),;]+)?)",
    re.IGNORECASE,
)
_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


# ---------------------------------------------------------------- utilidades


def _strip_md(s: str) -> str:
    s = s.replace("**", "").replace("\\*", "\x00")
    s = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", s)
    return re.sub(r"\s+", " ", s.replace("\x00", "*")).strip()


def fold(s: str) -> str:
    """Minúsculas sem acento — para comparar palavras-chave."""
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def roman_to_int(s: str) -> int | None:
    s = s.upper()
    if not s or any(c not in _ROMAN for c in s):
        return None
    total = 0
    for i, c in enumerate(s):
        v = _ROMAN[c]
        total += -v if i + 1 < len(s) and _ROMAN[s[i + 1]] > v else v
    return total


def _note_kind(body: str) -> str:
    b = fold(body)
    for needle, kind in (
        ("revogad", "revogacao"),
        ("vetad", "veto"),
        ("redacao dad", "redacao"),
        ("acrescid", "inclusao"),
        ("incluid", "inclusao"),
        ("renumerad", "renumeracao"),
        ("vigencia", "vigencia"),
        ("vide", "vide"),
    ):
        if needle in b:
            return kind
    return "outro"


def extract_notes(text: str) -> tuple[str, list[Note]]:
    """Remove as anotações editoriais de alteração e devolve (texto limpo, notas)."""
    notes: list[Note] = []
    # redação tachada (versões históricas preservadas por algumas fontes): não é texto vigente
    for m in _STRUCK_RE.finditer(text):
        notes.append(Note("redacao_anterior", _strip_md(m[1] or m[2])))
    text = _STRUCK_RE.sub(" ", text)

    def repl(m: re.Match) -> str:
        body = _strip_md(m["body"])
        ref = _REF_RE.search(body)
        notes.append(Note(_note_kind(body), body, ref[1].strip() if ref else None))
        return " "

    clean = _NOTE_RE.sub(repl, _strip_md(text))
    clean = re.sub(r"\s+([.;,:])", r"\1", re.sub(r"\s+", " ", clean)).strip()
    return clean, notes


def _is_revoked(clean: str, notes: list[Note]) -> bool:
    if clean in ("", ".", "-", "–") and any(n.kind == "revogacao" for n in notes):
        return True
    return bool(re.match(r"^\(?\s*(revogad[oa]s?|suprimid[oa]|vetad[oa])\b", fold(clean)))


def _slug_num(num: str, suf: str | None) -> str:
    return num.replace(".", "") + (suf.lower() if suf else "")  # "359", "M-A" → "359m-a"


# ---------------------------------------------------------------- parser


class _Builder:
    def __init__(self) -> None:
        self.root = Unit("raiz", "", "")
        self.scope = ""  # "" ou "adct"
        self.div_stack: list[Unit] = []  # divisões abertas
        self.article: Unit | None = None
        self.paragraph: Unit | None = None
        self.inciso: Unit | None = None
        self.alinea: Unit | None = None
        self.last: Unit | None = None  # último nó que recebe continuação de texto
        self.pending_rubrica: str | None = None
        self.warnings: list[str] = []
        self.seen_paths: dict[str, int] = {}

    # --- divisões
    def container(self) -> Unit:
        return self.div_stack[-1] if self.div_stack else self.root

    def open_scope(self, label: str, line: int) -> None:
        self.close_article()
        self.div_stack.clear()
        self.scope = "adct"
        node = Unit("divisao", label, "adct", div_type="escopo", line=line)
        self.root.children.append(node)
        self.div_stack.append(node)

    def open_division(self, div_type: str, label: str, title: str, line: int) -> None:
        self.close_article()
        rank = DIV_RANK[div_type]
        while self.div_stack and DIV_RANK.get(self.div_stack[-1].div_type or "", 0) >= rank:
            self.div_stack.pop()
        node = Unit("divisao", label, "", text=title, div_type=div_type, line=line)
        self.container().children.append(node)
        self.div_stack.append(node)
        self.last = node

    # --- dispositivos
    def close_article(self) -> None:
        self.article = self.paragraph = self.inciso = self.alinea = None

    def _new(self, kind: str, label: str, key: str, rest: str, line: int) -> Unit:
        clean, notes = extract_notes(rest)
        u = Unit(kind, label, key, text=clean, notes=notes, line=line)
        u.revoked = _is_revoked(clean, notes)
        u.vetoed = not clean and any(n.kind == "veto" for n in notes)
        if self.pending_rubrica:  # "Homicídio qualificado" antes do § 2º, "Tentativa" antes do inciso II…
            u.rubrica, self.pending_rubrica = self.pending_rubrica, None
        self.last = u
        return u

    def add_article(self, m: re.Match, line: int) -> None:
        self.close_article()
        num, suf = m["num"], m["suf"]
        label = f"Art. {num}" + ("º" if num.isdigit() and int(num) < 10 else "") + (f"-{suf}" if suf else "")
        u = self._new("artigo", label, f"art-{_slug_num(num, suf)}", m["rest"], line)
        self.container().children.append(u)
        self.article = u

    def add_paragraph(self, label: str, key: str, rest: str, line: int) -> None:
        if not self.article:
            self.warnings.append(f"linha {line}: parágrafo fora de artigo")
            return self.add_text(label + " " + rest, line)
        u = self._new("paragrafo", label, key, rest, line)
        self.article.children.append(u)
        self.paragraph, self.inciso, self.alinea = u, None, None

    def add_inciso(self, m: re.Match, line: int) -> None:
        parent = self.paragraph or self.article
        if not parent:
            return self.add_text(m.group(0), line)
        num, suf = m["num"], m["suf"]
        u = self._new("inciso", num + (f"-{suf}" if suf else ""), f"inc-{num.lower()}{(suf or '').lower()}", m["rest"], line)
        parent.children.append(u)
        self.inciso, self.alinea = u, None

    def continues_inciso_sequence(self, num: str, suf: str | None) -> bool:
        val = roman_to_int(num)
        parent = self.paragraph or self.article
        if val is None or parent is None:
            return False
        last = next((c for c in reversed(parent.children) if c.kind == "inciso"), None)
        if last is None:
            return val == 1 and not suf
        last_val = roman_to_int(last.label.split("-")[0]) or 0
        return val == last_val + 1 or (bool(suf) and val == last_val)

    def add_alinea(self, m: re.Match, line: int) -> None:
        parent = self.inciso or self.paragraph or self.article
        if not parent:
            return self.add_text(m.group(0), line)
        num, suf = m["num"], m["suf"]
        u = self._new("alinea", num + (f"-{suf}" if suf else ""), f"ali-{num}{(suf or '').lower()}", m["rest"], line)
        parent.children.append(u)
        self.alinea = u

    def add_item(self, m: re.Match, line: int) -> None:
        u = self._new("item", m["num"], f"item-{m['num']}", m["rest"], line)
        self.alinea.children.append(u)  # type: ignore[union-attr]

    def add_pena(self, rest: str, line: int) -> None:
        parent = self.paragraph or self.article
        u = self._new("pena", "Pena", "pena", rest, line)
        parent.children.append(u)  # type: ignore[union-attr]
        self.last = parent  # continuação volta ao dispositivo

    def add_text(self, raw: str, line: int) -> None:
        target = self.last if self.article or (self.last and self.last.kind == "divisao") else None
        clean, notes = extract_notes(raw)
        if target is None:
            return
        if target.kind == "divisao" and not self.article:
            # texto solto após divisão (subtítulo em linha seguinte, ou rubrica de bloco)
            target.text = (target.text + " " + clean).strip() if not target.text else target.text
            target.notes += notes
            return
        target.text = (target.text + " " + clean).strip()
        target.notes += notes

    def finalize(self) -> Unit:
        self._assign_paths(self.root, "")
        return self.root

    def _assign_paths(self, node: Unit, prefix: str) -> None:
        div_counter: dict[str, int] = {}
        for child in node.children:
            if child.kind == "divisao" and child.div_type != "escopo":
                n = div_counter[child.div_type or ""] = div_counter.get(child.div_type or "", 0) + 1
                child.key = f"{child.div_type}-{n}"
            base = f"{prefix}/{child.key}" if prefix else child.key
            # divisões não entram no caminho dos artigos: "art-157" deve continuar
            # estável se o legislador reorganizar capítulos.
            if child.kind == "artigo":
                base = f"{self.scope_of(child)}art-{child.key[4:]}"
            path = base
            if path in self.seen_paths:
                self.seen_paths[path] += 1
                path = f"{base}~{self.seen_paths[base]}"
                self.warnings.append(f"caminho repetido {base} (linha {child.line}) → {path}")
            else:
                self.seen_paths[path] = 1
            child.path = path
            self._assign_paths(child, path)

    def scope_of(self, art: Unit) -> str:
        return "adct/" if art.line >= self._adct_line else ""

    _adct_line = 1 << 60


def _quote_balance(s: str) -> int:
    return s.count("“") - s.count("”")


def parse_body(body: str) -> ParsedBody:
    lines = body.split("\n")
    b = _Builder()
    title: str | None = None
    preamble: list[str] = []
    in_quote = False

    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i].rstrip()
        lineno = i + 1
        i += 1
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):  # avisos editoriais do repositório
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        text = _strip_md(heading[2]) if heading else stripped

        if heading and heading[1] == "#" and title is None and not _SCOPE_RE.match(text):
            title = text
            continue

        # --- aspas: dentro de citação de texto alterado, tudo é conteúdo
        if in_quote:
            b.add_text(stripped, lineno)
            if _quote_balance(stripped) < 0 or re.search(r"[”\"]\s*(?:\(NR\)|\(AC\))?\s*[.;]?\s*\**\s*$", stripped):
                in_quote = False
            continue
        if stripped[:1] in "“\"" or stripped[:3] in ('**“', '**"'):
            b.add_text(stripped, lineno)
            bal = _quote_balance(stripped)
            closes = bal <= 0 and "“" in stripped or stripped.count('"') >= 2
            in_quote = not closes
            continue

        if _SCOPE_RE.match(text):
            b._adct_line = lineno
            b.open_scope(text, lineno)
            continue

        dm = _DIV_RE.match(text)
        if dm and (heading or _looks_like_bare_division(text)):
            kw = fold(dm["kw"])
            div_type = {"titulo": "titulo", "subtitulo": "subtitulo", "capitulo": "capitulo",
                        "secao": "secao", "subsecao": "subsecao"}.get(kw, kw)
            rest = re.sub(r"^\s*[-–—:.]\s*", "", dm["rest"] or "").strip()
            label = (dm["kw"] + (dm["num"] or "")).strip()
            b.pending_rubrica = None
            b.open_division(div_type, label, rest, lineno)
            continue
        if heading and fold(text).startswith("preambulo"):
            continue
        if heading:
            # outros cabeçalhos (ANEXO, DISPOSIÇÕES FINAIS sem palavra-chave…) viram rubrica
            b.pending_rubrica = text
            continue

        # negrito parcial ("**Art**. 1º") não pode impedir o reconhecimento
        probe = stripped.replace("**", "")
        m = _ART_RE.match(probe)
        if m:
            b.add_article(m, lineno)
            continue

        if b.article is None and not b.root.children:
            if _is_rubrica_candidate(stripped) and _next_is_article(lines, i):
                b.pending_rubrica = extract_notes(stripped)[0]  # rubrica do primeiro artigo
            else:
                preamble.append(_strip_md(stripped))
            continue

        m = _PAR_RE.match(probe)
        if m:
            num, suf = m["num"], m["suf"]
            label = f"§ {num}" + ("º" if int(num.replace(".", "")) < 10 else "") + (f"-{suf}" if suf else "")
            b.add_paragraph(label, f"par-{_slug_num(num, suf)}", m["rest"], lineno)
            continue
        m = _PAR_UNICO_RE.match(probe)
        if m:
            b.add_paragraph("Parágrafo único", "par-unico", m["rest"], lineno)
            continue
        if b.article is not None:
            m = _INC_RE.match(probe)
            if m and roman_to_int(m["num"]) is not None:
                b.add_inciso(m, lineno)
                continue
            m = _INC_BARE_RE.match(probe)
            if m and b.continues_inciso_sequence(m["num"], m["suf"]):
                b.add_inciso(m, lineno)
                continue
            m = _ALI_RE.match(probe)
            if m and (b.inciso or b.paragraph or b.article):
                b.add_alinea(m, lineno)
                continue
            m = _ITEM_RE.match(probe)
            if m and b.alinea is not None:
                b.add_item(m, lineno)
                continue
            m = _PENA_RE.match(probe)
            if m:
                b.add_pena(m["rest"], lineno)
                continue

        # rubrica candidata: linha curta, sem pontuação final, seguida de artigo, § ou inciso
        if _is_rubrica_candidate(stripped) and _next_is_dispositivo(lines, i, b.article is not None):
            b.pending_rubrica = extract_notes(stripped)[0]
            continue

        b.add_text(stripped, lineno)

    root = b.finalize()
    return ParsedBody(title=title, preamble=" ".join(preamble).strip(), root=root, warnings=b.warnings)


def _looks_like_bare_division(text: str) -> bool:
    """Divisão sem ``#`` (comum em textos originais): 'CAPÍTULO II' sozinho na linha."""
    return len(text) <= 120 and text.upper() == text and not text.endswith((".", ";", ","))


def _is_rubrica_candidate(s: str) -> bool:
    t = _strip_md(s)
    clean, _ = extract_notes(t)
    return (
        2 <= len(clean) <= 120
        and not re.search(r"[.;:,]$", clean)
        and not clean[:1].islower()  # continuação de linha quebrada
        and not clean.startswith(("§", "("))
        and not re.match(r"^[IVXLCDM]+\b", clean)  # inciso sem travessão
        and not _ART_RE.match(s.replace("**", ""))
    )


def _next_is_article(lines: list[str], i: int) -> bool:
    while i < len(lines):
        s = lines[i].strip()
        if s:
            return bool(_ART_RE.match(s.replace("**", "")))
        i += 1
    return False


def _next_is_dispositivo(lines: list[str], i: int, inside_article: bool) -> bool:
    """Próxima linha não vazia abre artigo, ou (dentro de um artigo) parágrafo ou inciso."""
    while i < len(lines):
        s = lines[i].strip()
        if s:
            probe = s.replace("**", "")
            if _ART_RE.match(probe):
                return True
            if not inside_article:
                return False
            if _PAR_RE.match(probe) or _PAR_UNICO_RE.match(probe):
                return True
            m = _INC_RE.match(probe)
            return bool(m and roman_to_int(m["num"]) is not None)
        i += 1
    return False
