"""Gera o banco de questões de "letra da lei" a partir do texto vigente do catálogo.

    python services/arena/tools/gerar_questoes.py --db catalogo.sqlite

Por que gerar em vez de escrever à mão: em questão de letra da lei, o erro mais grave é a
questão errada (pena, prazo ou competência trocados). Aqui o gabarito sai do próprio texto legal,
por construção:

* **Certo/Errado — literal** (C): o item cita o dispositivo exatamente como está no texto vigente.
* **Certo/Errado — troca** (E): o item cita o dispositivo com UMA troca controlada (prazo, fração,
  reclusão↔detenção, poderá↔deverá, órgão competente, negação em súmula). A explicação mostra a
  redação correta e o que foi trocado.
* **Múltipla escolha**: completar o número exato; identificar a pena cominada; localizar o artigo
  de um crime; reconhecer o tipo penal pela descrição da conduta.

O enunciado sempre se ancora no dispositivo ("Conforme o art. X da Lei Y…"), então uma troca torna
o item falso sem ambiguidade. Toda questão traz o fundamento (chave + trecho literal), e
``python jogar.py validar`` confere de novo o trecho contra o texto vigente. A saída é determinística
(semente fixa): rodar de novo com o mesmo catálogo gera o mesmo arquivo.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
import unicodedata
from pathlib import Path

# sem resolve(): no Windows o app pode virtualizar o caminho resolvido
# nome curto de propósito: caminhos longos estouram o limite de 260 caracteres do Windows
OUT = Path(__file__).parents[1] / "src" / "vade_arena" / "content" / "geradas.json"
SEED = 20261021
LEVELS = ("basico", "intermediario", "avancado", "especialista")

# alias, id da norma, nome no enunciado, área, nº de questões-alvo, peso extra de dificuldade
NORMAS = [
    ("CF", "constituicao", "da Constituição Federal", "constitucional", 130, 0),
    ("CP", "federal/decretos-lei/1940/del-2848-1940-12-07", "do Código Penal", "penal", 75, 0),
    ("CPP", "federal/decretos-lei/1941/del-3689-1941-10-03", "do Código de Processo Penal", "processo-penal", 45, 0),
    ("CC", "federal/leis-ordinarias/2002/lei-10406-2002-01-10", "do Código Civil", "civil", 55, 0),
    ("CPC", "federal/leis-ordinarias/2015/lei-13105-2015-03-16", "do Código de Processo Civil", "processo-civil", 45, 0),
    ("CLT", "federal/decretos-lei/1943/del-5452-1943-05-01", "da CLT", "trabalho", 40, 0),
    ("CTN", "federal/leis-ordinarias/1966/lei-5172-1966-10-25", "do Código Tributário Nacional", "tributario", 35, 0),
    ("CDC", "federal/leis-ordinarias/1990/lei-8078-1990-09-11", "do Código de Defesa do Consumidor", "consumidor", 30, 0),
    ("ECA", "federal/leis-ordinarias/1990/lei-8069-1990-07-13", "do Estatuto da Criança e do Adolescente", "crianca-adolescente", 25, 0),
    ("L8112", "federal/leis-ordinarias/1990/lei-8112-1990-12-11", "da Lei nº 8.112/1990", "administrativo", 30, 0),
    ("L9784", "federal/leis-ordinarias/1999/lei-9784-1999-01-29", "da Lei nº 9.784/1999", "administrativo", 15, 0),
    ("LIA", "federal/leis-ordinarias/1992/lei-8429-1992-06-02", "da Lei de Improbidade Administrativa", "administrativo", 12, 1),
    ("LAI", "federal/leis-ordinarias/2011/lei-12527-2011-11-18", "da Lei de Acesso à Informação", "administrativo", 8, 1),
    ("LMS", "federal/leis-ordinarias/2009/lei-12016-2009-08-07", "da Lei do Mandado de Segurança", "constitucional", 8, 1),
    ("LGPD", "federal/leis-ordinarias/2018/lei-13709-2018-08-14", "da LGPD", "protecao-de-dados", 20, 0),
    ("LMP", "federal/leis-ordinarias/2006/lei-11340-2006-08-07", "da Lei Maria da Penha", "penal-especial", 14, 0),
    ("LD", "federal/leis-ordinarias/2006/lei-11343-2006-08-23", "da Lei de Drogas", "penal-especial", 15, 0),
    ("LEP", "federal/leis-ordinarias/1984/lei-7210-1984-07-11", "da Lei de Execução Penal", "processo-penal", 15, 1),
    ("JEC", "federal/leis-ordinarias/1995/lei-9099-1995-09-26", "da Lei dos Juizados Especiais", "processo-penal", 12, 0),
    ("LCH", "federal/leis-ordinarias/1990/lei-8072-1990-07-25", "da Lei dos Crimes Hediondos", "penal-especial", 6, 1),
    ("LTORT", "federal/leis-ordinarias/1997/lei-9455-1997-04-07", "da Lei de Tortura", "penal-especial", 3, 1),
    ("EDES", "federal/leis-ordinarias/2003/lei-10826-2003-12-22", "do Estatuto do Desarmamento", "penal-especial", 8, 1),
    ("LORC", "federal/leis-ordinarias/2013/lei-12850-2013-08-02", "da Lei das Organizações Criminosas", "penal-especial", 8, 1),
    ("LAA", "federal/leis-ordinarias/2019/lei-13869-2019-09-05", "da Lei de Abuso de Autoridade", "penal-especial", 8, 1),
    ("CTB", "federal/leis-ordinarias/1997/lei-9503-1997-09-23", "do Código de Trânsito Brasileiro", "transito", 15, 0),
    ("LCA", "federal/leis-ordinarias/1998/lei-9605-1998-02-12", "da Lei de Crimes Ambientais", "ambiental", 12, 1),
    ("CE", "federal/leis-ordinarias/1965/lei-4737-1965-07-15", "do Código Eleitoral", "eleitoral", 12, 1),
    ("L8213", "federal/leis-ordinarias/1991/lei-8213-1991-07-24", "da Lei nº 8.213/1991", "previdenciario", 15, 1),
    ("EPI", "federal/leis-ordinarias/2003/lei-10741-2003-10-01", "do Estatuto da Pessoa Idosa", "direitos-humanos", 10, 0),
    ("LRF", "federal/leis-complementares/2000/lcp-101-2000-05-04", "da Lei de Responsabilidade Fiscal", "financeiro", 12, 1),
]
SUMULAS = 45  # STJ (não canceladas) e vinculantes do STF

# ---------------------------------------------------------------- números por extenso

_U = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze",
      "treze", "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
_D = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
_C = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"]


def extenso(n: int, fem: bool = False) -> str:
    def lt1000(x: int) -> str:
        if x == 0:
            return ""
        if x == 100:
            return "cem"
        c, r = divmod(x, 100)
        parts = [_C[c]] if c else []
        if r:
            if r < 20:
                parts.append(_U[r])
            else:
                d, u = divmod(r, 10)
                parts.append(_D[d] + (f" e {_U[u]}" if u else ""))
        return " e ".join(parts)

    if n == 0:
        return "zero"
    mil, resto = divmod(n, 1000)
    out = []
    if mil:
        out.append("mil" if mil == 1 else f"{lt1000(mil)} mil")
    if resto:
        out.append(("e " if mil and (resto < 100 or resto % 100 == 0) else "") + lt1000(resto))
    s = " ".join(out)
    if fem:
        s = re.sub(r"\bum\b", "uma", s)
        s = re.sub(r"\bdois\b", "duas", s)
        s = re.sub(r"entos\b", "entas", s)
    return s


_WORD2NUM = {extenso(i): i for i in range(1, 1001)}
_WORD2NUM.update({extenso(i, True): i for i in range(1, 1001)})

# ---------------------------------------------------------------- utilidades de texto


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def clean_end(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[;,:.]\s*(e|ou)?\s*$", "", s).strip()
    return s.rstrip(".").strip()


def em(nome: str) -> str:
    """'do Código Penal' → 'no Código Penal'; 'da Lei…' → 'na Lei…'."""
    return re.sub(r"^d([oa])\b", r"n\1", nome)


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def roman_ok(label: str) -> bool:
    return bool(re.fullmatch(r"[IVXLCDM]+(-[A-Z])?", label))


def ref_label(chain: list[dict]) -> str:
    """[art, par, inc, ali] → 'art. 5º, § 1º, inciso II, alínea a'."""
    parts = []
    for u in chain:
        if u["tipo"] == "artigo":
            parts.append(u["rotulo"].replace("Art.", "art."))
        elif u["tipo"] == "paragrafo":
            parts.append("parágrafo único" if u["rotulo"].lower().startswith("parágrafo") else u["rotulo"])
        elif u["tipo"] == "inciso":
            parts.append(f"inciso {u['rotulo']}")
        elif u["tipo"] == "alinea":
            parts.append(f"alínea {u['rotulo']}")
        elif u["tipo"] == "item":
            parts.append(f"item {u['rotulo']}")
    return ", ".join(parts)


BAD = re.compile(r"vetad|revogad|\(vide|\.{4,}|[“”\"]|art\. \d+ desta lei, nos termos|renumerad|em vigor na data|entra em vigor|revogam-se", re.I)

# ---------------------------------------------------------------- trocas que tornam o item falso

NUM_EXT_RE = re.compile(r"(?<![/\d])\b(\d{1,4}(?:\.\d{3})?)\s*\(([a-zà-úç ]+?)\)")
WORD_NUM_RE = re.compile(
    r"\b(" + "|".join(sorted({re.escape(extenso(i)) for i in range(1, 121)} | {re.escape(extenso(i, True)) for i in range(1, 121)},
                             key=len, reverse=True)) + r")\s+(anos?|meses|mês|dias|dia|horas?|vezes)\b")
FRAC_RE = re.compile(r"\b([12])/([2-6])\s*\(([a-zà-ú ]+)\)")
FRACS = [("1/6", "um sexto"), ("1/5", "um quinto"), ("1/4", "um quarto"), ("1/3", "um terço"), ("1/2", "metade"), ("2/3", "dois terços")]

SWAPS = [  # (de, para) — só aplicada se "para" não aparece no texto original
    ("reclusão", "detenção"), ("detenção", "reclusão"),
    ("obrigatório", "facultativo"), ("obrigatória", "facultativa"), ("obrigatórios", "facultativos"),
    ("facultativo", "obrigatório"), ("facultativa", "obrigatória"), ("facultativos", "obrigatórios"),
    ("absolutamente", "relativamente"), ("relativamente", "absolutamente"),
    ("inafiançável", "afiançável"), ("imprescritível", "prescritível"),
    ("poderá", "deverá"), ("deverá", "poderá"),
    ("é vedado", "é permitido"), ("é vedada", "é permitida"),
    ("maioria absoluta", "maioria simples"), ("três quintos", "dois terços"),
    ("Senado Federal", "Câmara dos Deputados"), ("Câmara dos Deputados", "Senado Federal"),
    ("Supremo Tribunal Federal", "Superior Tribunal de Justiça"), ("Superior Tribunal de Justiça", "Supremo Tribunal Federal"),
    ("primário", "reincidente"), ("doloso", "culposo"), ("culposo", "doloso"),
    ("solidariamente", "subsidiariamente"), ("subsidiariamente", "solidariamente"),
    ("objetiva", "subjetiva"),
]
UNIT_VALUES = {
    "dia": [1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60, 90, 120, 180],
    "mes": [1, 2, 3, 4, 6, 8, 12, 18, 24],
    "ano": [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 18, 20, 21, 25, 30, 35, 40, 60, 65, 70],
    "hora": [1, 2, 4, 6, 8, 12, 24, 48, 72],
    "vez": [1, 2, 3, 4],
}


def unit_key(unit: str) -> str:
    u = fold(unit)
    if u.startswith("dia"):
        return "dia"
    if u.startswith("mes"):
        return "mes"
    if u.startswith("ano"):
        return "ano"
    if u.startswith("hora"):
        return "hora"
    return "vez"


def unit_word(key: str, n: int) -> str:
    one = {"dia": "dia", "mes": "mês", "ano": "ano", "hora": "hora", "vez": "vez"}[key]
    many = {"dia": "dias", "mes": "meses", "ano": "anos", "hora": "horas", "vez": "vezes"}[key]
    return one if n == 1 else many


def alt_values(n: int, rng: random.Random, pool: list[int] | None, k: int) -> list[int]:
    cands = set(pool or []) | {n + 1, n * 2, max(1, n - 1), max(1, n // 2), n + 5, n * 3}
    cands.discard(n)
    cands = sorted(c for c in cands if 0 < c < 10000)
    rng.shuffle(cands)
    near = sorted(cands, key=lambda c: abs(c - n))[: max(k * 2, 6)]
    rng.shuffle(near)
    return near[:k]


def mutations(text: str, rng: random.Random) -> list[dict]:
    """Trocas possíveis no texto. Cada uma: {texto, de, para, tipo}."""
    out = []
    for m in NUM_EXT_RE.finditer(text):
        n = int(m[1].replace(".", ""))
        if n > 5000 or _WORD2NUM.get(m[2].strip()) != n:
            continue
        fem = bool(re.search(r"\b(uma|duas)\b|entas\b", m[2]))
        tail = text[m.end(): m.end() + 12]
        pool = UNIT_VALUES[unit_key(tail.split()[0])] if tail.split() and re.match(r"(anos?|meses|m[eê]s|dias?|horas?|vezes)", fold(tail.split()[0])) else None
        for v in alt_values(n, rng, pool, 1):
            new = f"{v} ({extenso(v, fem)})"
            out.append({"texto": text[: m.start()] + new + text[m.end():], "de": m.group(0), "para": new, "tipo": "troca-numero"})
    for m in WORD_NUM_RE.finditer(text):
        n = _WORD2NUM.get(m[1])
        if not n:
            continue
        fem = m[1] != extenso(n)
        key = unit_key(m[2])
        bigger = [v for v in UNIT_VALUES[key] if v > n] or [n + 1]
        v = rng.choice(bigger[:3])
        new = f"{extenso(v, fem)} {unit_word(key, v)}"
        out.append({"texto": text[: m.start()] + new + text[m.end():], "de": m.group(0), "para": new, "tipo": "troca-prazo"})
    for m in FRAC_RE.finditer(text):
        cur = f"{m[1]}/{m[2]}"
        others = [f for f in FRACS if f[0] != cur]
        frac, word = rng.choice(others)
        new = f"{frac} ({word})"
        out.append({"texto": text[: m.start()] + new + text[m.end():], "de": m.group(0), "para": new, "tipo": "troca-fracao"})
    low = text
    for a, b in SWAPS:
        m = re.search(r"(?<![\wÀ-ú])" + re.escape(a) + r"(?![\wÀ-ú])", low)
        if m and not re.search(r"(?<![\wÀ-ú])" + re.escape(b) + r"(?![\wÀ-ú])", low, re.I):
            new = b
            out.append({"texto": text[: m.start()] + new + text[m.end():], "de": a, "para": b, "tipo": "troca-termo"})
    # sem ambiguidade: o trecho trocado aparece uma vez só, e o valor novo não existe em outro ponto
    # (senão a explicação "diz X, e não Y" apontaria para o lugar errado)
    return [m for m in out if text.count(m["de"]) == 1 and m["para"] not in text]


# ---------------------------------------------------------------- leitura do catálogo


class Catalog:
    def __init__(self, path: str) -> None:
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row

    def units(self, norma_id: str) -> tuple[list[dict], dict[int, dict]]:
        rows = [dict(r) for r in self.db.execute(
            "SELECT id, pai_id, chave, caminho, tipo, rotulo, rubrica, texto, revogado, vetado, ordem "
            "FROM dispositivo WHERE norma_id = ? ORDER BY ordem", (norma_id,))]
        return rows, {r["id"]: r for r in rows}

    def norma_exists(self, norma_id: str) -> bool:
        return self.db.execute("SELECT 1 FROM norma WHERE id = ?", (norma_id,)).fetchone() is not None


def chain_of(u: dict, by_id: dict[int, dict]) -> list[dict]:
    out = []
    while u and u["tipo"] != "divisao":
        out.append(u)
        u = by_id.get(u["pai_id"])
    return list(reversed(out))


def statement_parts(u: dict, by_id: dict[int, dict]) -> tuple[str, str] | None:
    """(introdução do pai, texto do dispositivo) ou None se o dispositivo não é bom para questão."""
    t = u["texto"].strip()
    if u["revogado"] or u["vetado"] or not (30 <= len(t) <= 380) or BAD.search(t):
        return None
    if u["caminho"].startswith("adct/"):
        return None
    if u["tipo"] in ("inciso", "alinea", "item"):
        p = by_id.get(u["pai_id"])
        if not p or not p["texto"].rstrip().endswith(":") or len(p["texto"]) > 260 or BAD.search(p["texto"]):
            return None
        return p["texto"].rstrip().rstrip(":").strip(), clean_end(t)
    if u["tipo"] in ("artigo", "paragrafo"):
        if t.endswith(":"):
            return None
        return "", clean_end(t)
    return None


# ---------------------------------------------------------------- geração


def level(base: int, depth: int, extra: int) -> str:
    return LEVELS[max(0, min(3, base + (1 if depth >= 3 else 0) + extra))]


def make_ce(alias, nome, area, extra, u, chain, intro, leaf, rng, want_true):
    ref = ref_label(chain)
    tema = next((c["rubrica"] for c in reversed(chain) if c.get("rubrica")), None) or cap(ref.split(",")[0])
    quote = (f"{intro}: {leaf}" if intro else leaf)
    trecho = leaf[:240] if len(leaf) <= 240 else leaf[:240].rsplit(" ", 1)[0]
    base = {"formato": "certo_errado", "area": area, "tema": tema, "gerada": True,
            "fundamentos": [{"chave": f"{alias}#{u['caminho']}", "trecho": trecho}]}
    if want_true:
        return {**base, "nivel": level(0, len(chain) - 1, extra), "tipo_geracao": "literal",
                "enunciado": f"Conforme o {ref} {nome}: “{quote}.”", "gabarito": "C",
                "explicacao": f"Certo. É a redação literal do {ref} {nome}."}
    muts = mutations(leaf, rng)
    if not muts:
        return None
    pref = {"troca-numero": 0, "troca-prazo": 0, "troca-fracao": 0, "troca-termo": 1}
    muts.sort(key=lambda m: (pref[m["tipo"]], rng.random()))
    m = muts[0]
    mq = (f"{intro}: {m['texto']}" if intro else m["texto"])
    # o trecho do fundamento é o pedaço original em volta do que foi trocado
    i = leaf.find(m["de"])
    lo = max(0, i - 80)
    piece = leaf[lo: i + len(m["de"]) + 80]
    piece = piece if lo == 0 else piece.split(" ", 1)[-1]
    piece = piece.rsplit(" ", 1)[0] if i + len(m["de"]) + 80 < len(leaf) else piece
    base["fundamentos"] = [{"chave": f"{alias}#{u['caminho']}", "trecho": piece.strip(" ,;")}]
    lvl = {"troca-numero": 1, "troca-prazo": 0, "troca-fracao": 1}.get(m["tipo"], 2 if m["de"] in ("poderá", "deverá") else 1)
    return {**base, "nivel": level(lvl, len(chain) - 1, extra), "tipo_geracao": m["tipo"],
            "enunciado": f"Conforme o {ref} {nome}: “{mq}.”", "gabarito": "E",
            "explicacao": f"Errado. O {ref} {nome} diz “{m['de']}”, e não “{m['para']}”. Redação correta: “{quote}.”",
            "pegadinha": f"Troca de “{m['de']}” por “{m['para']}”."}


LETTERS = "ABCDE"


def mc_from(options: list[str], correct: str, rng: random.Random) -> tuple[dict, str]:
    opts = list(dict.fromkeys(options))
    rng.shuffle(opts)
    alts = {LETTERS[i]: o for i, o in enumerate(opts[:5])}
    gab = next(k for k, v in alts.items() if v == correct)
    return alts, gab


def make_cloze(alias, nome, area, extra, u, chain, intro, leaf, rng):
    m = NUM_EXT_RE.search(leaf) or WORD_NUM_RE.search(leaf)
    if not m:
        return None
    ref = ref_label(chain)
    if m.re is NUM_EXT_RE:
        n = int(m[1].replace(".", ""))
        if _WORD2NUM.get(m[2].strip()) != n or n > 5000:
            return None
        fem = bool(re.search(r"\b(uma|duas)\b|entas\b", m[2]))
        tail = leaf[m.end(): m.end() + 12].split()
        pool = UNIT_VALUES[unit_key(tail[0])] if tail and re.match(r"(anos?|meses|m[eê]s|dias?|horas?|vezes)", fold(tail[0])) else None
        fmtv = lambda v: f"{v} ({extenso(v, fem)})"  # noqa: E731
    else:
        n = _WORD2NUM[m[1]]
        fem = m[1] != extenso(n)
        key = unit_key(m[2])
        pool = UNIT_VALUES[key]
        fmtv = lambda v: f"{extenso(v, fem)} {unit_word(key, v)}"  # noqa: E731
    vals = alt_values(n, rng, pool, 4)
    if len(vals) < 4:
        return None
    correct = fmtv(n) if m.re is WORD_NUM_RE else m.group(0)
    alts, gab = mc_from([correct] + [fmtv(v) for v in vals], correct, rng)
    if len(alts) < 5:
        return None
    blank = leaf[: m.start()] + "______" + leaf[m.end():]
    quote = f"{intro}: {blank}" if intro else blank
    tema = next((c["rubrica"] for c in reversed(chain) if c.get("rubrica")), None) or cap(ref.split(",")[0])
    return {"formato": "multipla", "area": area, "tema": tema, "gerada": True, "tipo_geracao": "completar-numero",
            "nivel": level(0 if u["tipo"] == "artigo" else 1, len(chain) - 1, extra),
            "enunciado": f"Complete conforme o {ref} {nome}: “{quote}.”",
            "alternativas": alts, "gabarito": gab,
            "explicacao": f"O {ref} {nome} diz: “{(intro + ': ') if intro else ''}{leaf}.”",
            "fundamentos": [{"chave": f"{alias}#{u['caminho']}", "trecho": m.group(0)}]}


def crimes(units: list[dict], by_id: dict[int, dict]) -> list[dict]:
    """Artigos com rubrica e pena própria no caput (tipos penais)."""
    out = []
    for u in units:
        if u["tipo"] != "artigo" or u["revogado"] or not u["rubrica"]:
            continue
        penas = [c for c in units if c["pai_id"] == u["id"] and c["tipo"] == "pena"]
        if not penas or not u["texto"] or BAD.search(u["texto"]):
            continue
        rub = re.sub(r"\s+", " ", u["rubrica"]).strip()
        if len(rub) > 60 or re.search(r"pena|disposi|aumento|forma|qualificad|culpos|privilegi|causa", rub, re.I):
            continue
        out.append({**u, "rub": rub, "pena": clean_end(penas[0]["texto"]).rstrip(".")})
    return out


def make_crime_questions(alias, nome, area, extra, units, by_id, rng, budget):
    cs = crimes(units, by_id)
    if len(cs) < 6:
        return []
    qs = []
    rng.shuffle(cs)
    penas = list(dict.fromkeys(c["pena"] for c in cs
                               if len(c["pena"]) <= 90 and re.match(r"(reclusão|detenção|multa)", c["pena"], re.I)))
    for c in cs:
        if len(qs) >= budget:
            break
        kind = len(qs) % 3
        art = c["rotulo"].replace("Art.", "art.")
        if kind == 0 and c["pena"] in penas and len(penas) >= 5:  # pena cominada
            others = [p for p in penas if p != c["pena"]]
            rng.shuffle(others)
            alts, gab = mc_from([c["pena"]] + others[:4], c["pena"], rng)
            if len(alts) < 5:
                continue
            qs.append({"formato": "multipla", "area": area, "tema": c["rub"], "gerada": True, "tipo_geracao": "pena-cominada",
                       "nivel": level(2, 1, extra), "enunciado": f"A pena cominada ao crime de {c['rub'].lower()} ({art} {nome}), na forma do caput, é:",
                       "alternativas": alts, "gabarito": gab,
                       "explicacao": f"O {art} {nome} comina: {c['pena']}.",
                       "fundamentos": [{"chave": f"{alias}#{c['caminho']}/pena", "trecho": c["pena"][:200]}]})
        elif kind == 1:  # artigo do crime
            others = [o for o in cs if o["rotulo"] != c["rotulo"]]
            rng.shuffle(others)
            labels = [c["rotulo"]] + [o["rotulo"] for o in others[:4]]
            alts, gab = mc_from(labels, c["rotulo"], rng)
            if len(alts) < 5:
                continue
            qs.append({"formato": "multipla", "area": area, "tema": c["rub"], "gerada": True, "tipo_geracao": "artigo-do-crime",
                       "nivel": level(2, 1, extra), "enunciado": f"O crime de {c['rub'].lower()} está tipificado {em(nome)} no:",
                       "alternativas": alts, "gabarito": gab,
                       "explicacao": f"{c['rub']}: {art} {nome} — “{c['texto']}”",
                       "fundamentos": [{"chave": f"{alias}#{c['caminho']}", "trecho": c["texto"][:200]}]})
        else:  # tipo pela descrição
            desc = clean_end(c["texto"]).rstrip(":")
            if len(desc) > 300 or any(fold(w) in fold(desc) for w in re.findall(r"[A-Za-zÀ-ú]{5,}", c["rub"])):
                continue
            others = [o["rub"] for o in cs if o["rub"] != c["rub"]]
            rng.shuffle(others)
            alts, gab = mc_from([c["rub"]] + others[:4], c["rub"], rng)
            if len(alts) < 5:
                continue
            qs.append({"formato": "multipla", "area": area, "tema": c["rub"], "gerada": True, "tipo_geracao": "tipo-pela-conduta",
                       "nivel": level(1, 1, extra), "enunciado": f"A conduta “{desc}” corresponde, {em(nome)}, ao crime de:",
                       "alternativas": alts, "gabarito": gab,
                       "explicacao": f"É o tipo do {art} {nome} ({c['rub']}).",
                       "fundamentos": [{"chave": f"{alias}#{c['caminho']}", "trecho": desc[:200]}]})
    return qs


def generate_norma(cat: Catalog, spec, rng: random.Random) -> list[dict]:
    alias, norma_id, nome, area, target, extra = spec
    if not cat.norma_exists(norma_id):
        print(f"  ! {alias}: norma fora do catálogo, pulada")
        return []
    units, by_id = cat.units(norma_id)
    cands = []
    for u in units:
        parts = statement_parts(u, by_id)
        if parts:
            cands.append((u, chain_of(u, by_id), *parts))
    if not cands:
        return []
    crime_qs = make_crime_questions(alias, nome, area, extra, units, by_id, rng, budget=max(3, target // 6)) \
        if alias in ("CP", "LD", "EDES", "LAA", "LCA", "CTB", "LORC", "ECA", "CDC", "EPI") else []
    mc_target = max(0, round(target * 0.4) - len(crime_qs))
    ce_target = target - len(crime_qs) - mc_target

    # amostra espalhada primeiro (cobre todos os títulos), depois o resto da lei
    step = max(1, len(cands) // max(1, target * 3))
    spread = cands[::step]
    picked = {id(c) for c in spread}
    rest = [c for c in cands if id(c) not in picked]
    rng.shuffle(spread)
    rng.shuffle(rest)
    pool = spread + rest
    used: set[str] = set()

    def take(pred):
        for c in pool:
            if c[0]["chave"] not in used and pred(c):
                used.add(c[0]["chave"])
                return c
        return None

    # --- múltipla escolha: completar número, assinalar a correta, assinalar a incorreta
    mc: list[dict] = []
    kinds = ["completar", "correta", "incorreta"]
    k = 0
    misses = 0
    while len(mc) < mc_target and misses < 6:
        kind = kinds[k % 3]
        k += 1
        q = None
        if kind == "completar":
            c = take(lambda c: NUM_EXT_RE.search(c[3]) or WORD_NUM_RE.search(c[3]))
            if c:
                q = make_cloze(alias, nome, area, extra, c[0], c[1], c[2], c[3], rng)
        else:
            q = make_pick(alias, nome, area, extra, take, rng, correct_is_literal=(kind == "correta"))
        if q:
            mc.append(q)
            misses = 0
        else:
            misses += 1

    # --- certo/errado: ~3 erradas para 2 certas
    ce: list[dict] = []
    cycle = ["E", "C", "E", "E", "C"]
    i = 0
    for c in pool:
        if len(ce) >= ce_target:
            break
        u, chain, intro, leaf = c
        if u["chave"] in used:
            continue
        want = cycle[i % len(cycle)]
        q = make_ce(alias, nome, area, extra, u, chain, intro, leaf, rng, want_true=(want == "C"))
        if q is None and want == "E":
            continue  # sem troca possível: guarda o dispositivo para um item certo depois
        if q is None:
            continue
        used.add(u["chave"])
        ce.append(q)
        i += 1
    return crime_qs + mc + ce


def short_ref(chain: list[dict]) -> str:
    r = ref_label(chain)
    return r[0].upper() + r[1:]


def option_text(chain, intro, leaf, mutated=None) -> str | None:
    body = mutated if mutated is not None else leaf
    txt = f"{intro}: {body}" if intro else body
    if len(txt) > 280:
        return None
    return f"{short_ref(chain)}: {txt}."


def make_pick(alias, nome, area, extra, take, rng, correct_is_literal: bool):
    """Correta: 1 literal + 4 com troca. Incorreta: 4 literais + 1 com troca. Cada opção é de um
    dispositivo diferente e vem identificada (“Art. 37, inciso III: …”), então a troca não pode
    coincidir com outro texto verdadeiro."""
    n_mut = 4 if correct_is_literal else 1
    n_lit = 5 - n_mut
    lits, muts = [], []
    for _ in range(n_lit):
        c = take(lambda c: option_text(c[1], c[2], c[3]) is not None)
        if not c:
            return None
        lits.append((c, option_text(c[1], c[2], c[3])))
    for _ in range(n_mut):
        c = take(lambda c: bool(mutations(c[3], rng)) and option_text(c[1], c[2], c[3]) is not None)
        if not c:
            return None
        m = sorted(mutations(c[3], rng), key=lambda m: m["tipo"] == "troca-termo")[0]
        txt = option_text(c[1], c[2], c[3], m["texto"])
        if not txt:
            return None
        muts.append((c, txt, m))
    options = [t for _, t in lits] + [t for _, t, _ in muts]
    correct = lits[0][1] if correct_is_literal else muts[0][1]
    alts, gab = mc_from(options, correct, rng)
    if len(alts) < 5:
        return None
    lines = [f"{short_ref(c[1])} diz “{m['de']}”, não “{m['para']}”." for c, _, m in muts]
    if correct_is_literal:
        enun = f"Assinale a alternativa que reproduz corretamente a literalidade {nome}:"
        expl = "A única alternativa fiel ao texto é a do " + ref_label(lits[0][0][1]) + ". Nas demais houve troca: " + " ".join(lines)
        fund = lits[0][0]
        trecho = lits[0][0][3]
    else:
        enun = f"Assinale a alternativa que NÃO corresponde à literalidade {nome}:"
        expl = "A alternativa alterada é a do " + ref_label(muts[0][0][1]) + ": " + lines[0] + " As demais reproduzem o texto legal."
        fund = muts[0][0]
        trecho = muts[0][0][3]
    chain = fund[1]
    trecho = trecho if len(trecho) <= 240 else trecho[:240].rsplit(" ", 1)[0]
    tema = next((c["rubrica"] for c in reversed(chain) if c.get("rubrica")), None) or "Literalidade da lei"
    lvl = level(2 if correct_is_literal else 1, max(len(c[1]) for c, _ in lits), extra)
    return {"formato": "multipla", "area": area, "tema": tema, "gerada": True,
            "tipo_geracao": "assinale-correta" if correct_is_literal else "assinale-incorreta",
            "nivel": lvl, "enunciado": enun, "alternativas": alts, "gabarito": gab, "explicacao": expl,
            "fundamentos": [{"chave": f"{alias}#{fund[0]['caminho']}", "trecho": trecho}]}


def generate_sumulas(cat: Catalog, rng: random.Random, target: int) -> tuple[list[dict], dict]:
    rows = [dict(r) for r in cat.db.execute(
        """SELECT n.id, n.titulo, n.revogada, n.areas, n.situacao, d.texto, d.caminho
             FROM norma n JOIN dispositivo d ON d.norma_id = n.id AND d.caminho = 'enunciado'
            WHERE n.esfera = 'jurisprudencia'
              AND (n.id LIKE 'jurisprudencia/stj/sumulas/%' OR n.id LIKE 'jurisprudencia/stf/sumulas-vinculantes/%')
              AND coalesce(n.revogada, 0) = 0""")]
    rows = [r for r in rows if 40 <= len(r["texto"]) <= 300 and not BAD.search(r["texto"])
            and not re.search(r"cancelad|revogad|superad", fold(r["situacao"] or "") + fold(r["titulo"]))]
    rows.sort(key=lambda r: r["id"])
    rng.shuffle(rows)
    qs, aliases = [], {}
    for r in rows:
        if len(qs) >= target:
            break
        tribunal = "STF" if "/stf/" in r["id"] else "STJ"
        num = r["id"].rsplit("-", 1)[-1]
        alias = f"{'SV' if tribunal == 'STF' else 'STJ'}{num}"
        nome = f"a Súmula Vinculante {num} do STF" if tribunal == "STF" else f"a Súmula {num} do STJ"
        areas = json.loads(r["areas"] or "[]")
        area = areas[0] if areas else "jurisprudencia"
        text = clean_end(r["texto"]).rstrip(".")
        true_item = len(qs) % 3 == 1
        mut = None
        if not true_item:
            if re.search(r"\bnão\b", text):
                new = re.sub(r"\bnão\s+", "", text, count=1)
                mut = {"texto": new[0].upper() + new[1:], "de": "não", "para": "(sem a negação)", "tipo": "troca-negacao"}
            else:
                ms = mutations(text, rng)
                mut = ms[0] if ms else None
            if mut is None:
                true_item = True
        aliases[alias] = r["id"]
        base = {"formato": "certo_errado", "area": area, "tema": f"Súmula {num} ({tribunal})", "gerada": True,
                "fundamentos": [{"chave": f"{alias}#enunciado", "trecho": text[:240].rsplit(' ', 1)[0] if len(text) > 240 else text}]}
        if true_item:
            qs.append({**base, "nivel": "avancado", "tipo_geracao": "sumula-literal", "gabarito": "C",
                       "enunciado": f"Segundo {nome}: “{text}.”", "explicacao": f"Certo. É o enunciado literal d{nome[0]} {nome[2:]}."})
        else:
            how = "retirou a negação “não”" if mut["tipo"] == "troca-negacao" else f"trocou “{mut['de']}” por “{mut['para']}”"
            qs.append({**base, "nivel": "especialista", "tipo_geracao": mut["tipo"], "gabarito": "E",
                       "enunciado": f"Segundo {nome}: “{mut['texto']}.”",
                       "explicacao": f"Errado. O item {how}. Enunciado correto: “{text}.”",
                       "pegadinha": "Súmula com a negação ou o termo-chave invertido." if mut["tipo"] == "troca-negacao" else f"Troca de “{mut['de']}” por “{mut['para']}”."})
    return qs, aliases


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--saida", default=str(OUT))
    a = ap.parse_args()
    cat = Catalog(a.db)
    rng = random.Random(SEED)
    all_q, normas = [], {}
    for spec in NORMAS:
        qs = generate_norma(cat, spec, random.Random(f"{SEED}-{spec[0]}"))
        normas[spec[0]] = spec[1]
        for j, q in enumerate(qs, start=1):
            q["id"] = f"g-{spec[0].lower()}-{j:03d}"
        all_q += qs
        print(f"  {spec[0]:6} {len(qs):4} questões")
    sq, saliases = generate_sumulas(cat, rng, SUMULAS)
    normas.update(saliases)
    for j, q in enumerate(sq, start=1):
        q["id"] = f"g-sum-{j:03d}"
    all_q += sq
    print(f"  SÚMULAS {len(sq):4} questões")
    order = ["id", "formato", "nivel", "area", "tema", "enunciado", "alternativas", "gabarito", "explicacao",
             "pegadinha", "fundamentos", "gerada", "tipo_geracao"]
    all_q = [{k: q[k] for k in order if k in q} for q in all_q]
    data = {"_sobre": ("Questões de letra da lei geradas por services/arena/tools/gerar_questoes.py a partir do "
                       "texto vigente do catálogo. Gabarito por construção: item literal (Certo) ou com uma troca "
                       "controlada e explicada (Errado). Não edite à mão: rode o gerador de novo."),
            "normas": normas, "questoes": all_q}
    Path(a.saida).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ce = sum(q["formato"] == "certo_errado" for q in all_q)
    print(f"Total: {len(all_q)} questões ({ce} Certo/Errado, {len(all_q) - ce} múltipla escolha) → {a.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
