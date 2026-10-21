"""Carrega e valida o conteúdo da Arena (concursos, questões e casos).

Duas validações:

* ``validate_structure``: roda sempre, inclusive nos testes. Verifica ids únicos, gabaritos
  coerentes, níveis e áreas conhecidos, aliases de norma resolvidos e o grafo dos casos (todas as
  cenas alcançáveis, todo caminho termina, sem ciclos).
* ``validate_against_catalog``: confere no catálogo SQLite se cada dispositivo citado **existe** e se
  o trecho citado **aparece literalmente** no texto vigente (comparação sem acento e sem diferença de
  espaços). É a proteção contra questão desatualizada: se a lei mudar e o trecho sumir, a questão
  falha na validação.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from importlib import resources
from pathlib import Path

LEVELS = ("basico", "intermediario", "avancado", "especialista")
ROLES = ("advogado", "promotor", "juiz")
CE_KEYS = ("C", "E")
MC_KEYS = ("A", "B", "C", "D", "E")


@dataclass
class Bank:
    niveis: dict
    concursos: list[dict]
    questoes: list[dict]
    casos: list[dict]
    elenco: dict
    normas: dict[str, str]
    by_id: dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.by_id = {q["id"]: q for q in self.questoes}

    def concurso(self, cid: str) -> dict:
        for c in self.concursos:
            if c["id"] == cid:
                return c
        raise KeyError(f"concurso desconhecido: {cid}")

    def caso(self, cid: str) -> dict:
        for c in self.casos:
            if c["id"] == cid:
                return c
        raise KeyError(f"caso desconhecido: {cid}")

    def resolve(self, chave: str) -> str:
        """'CP#art-157' → 'federal/decretos-lei/1940/del-2848-1940-12-07#art-157'."""
        alias, _, path = chave.partition("#")
        return f"{self.normas.get(alias, alias)}#{path}"


def _read(name: str, base: Path | None) -> dict:
    if base is not None:
        return json.loads((base / name).read_text(encoding="utf-8"))
    return json.loads(resources.files(__package__).joinpath("content", name).read_text(encoding="utf-8"))


def load(base: Path | None = None) -> Bank:
    c = _read("concursos.json", base)
    q = _read("questoes.json", base)
    k = _read("casos.json", base)
    return Bank(niveis=c["niveis"], concursos=c["concursos"], questoes=q["questoes"],
                casos=k["casos"], elenco=k["elenco"], normas=q["normas"])


@lru_cache(maxsize=1)
def default_bank() -> Bank:
    return load()


# ---------------------------------------------------------------- estrutura


def _fundamentos(obj: dict) -> list[dict]:
    return obj.get("fundamentos", [])


def validate_structure(b: Bank) -> list[str]:
    errs: list[str] = []
    areas_concursos = {a for c in b.concursos for a in c["areas"]}

    seen: set[str] = set()
    for q in b.questoes:
        qid = q.get("id", "?")
        if qid in seen:
            errs.append(f"{qid}: id repetido")
        seen.add(qid)
        if q.get("nivel") not in LEVELS:
            errs.append(f"{qid}: nível inválido {q.get('nivel')!r}")
        if q.get("area") not in areas_concursos:
            errs.append(f"{qid}: área {q.get('area')!r} não é cobrada por nenhum concurso")
        if not q.get("enunciado") or not q.get("explicacao"):
            errs.append(f"{qid}: enunciado e explicação são obrigatórios")
        if q.get("formato") == "certo_errado":
            if q.get("gabarito") not in CE_KEYS:
                errs.append(f"{qid}: gabarito C/E inválido")
        elif q.get("formato") == "multipla":
            alts = q.get("alternativas", {})
            if tuple(alts) != MC_KEYS:
                errs.append(f"{qid}: múltipla escolha precisa das alternativas A–E, nessa ordem")
            if q.get("gabarito") not in alts:
                errs.append(f"{qid}: gabarito fora das alternativas")
            if len({v.strip().lower() for v in alts.values()}) != len(alts):
                errs.append(f"{qid}: alternativas repetidas")
        else:
            errs.append(f"{qid}: formato desconhecido {q.get('formato')!r}")
        if not _fundamentos(q):
            errs.append(f"{qid}: toda questão precisa de ao menos um fundamento")
        errs += _check_refs(b, qid, _fundamentos(q))

    for c in b.concursos:
        if c["formato"] not in ("certo_errado", "multipla"):
            errs.append(f"{c['id']}: formato inválido")
        if c.get("nivel_minimo") and c["nivel_minimo"] not in LEVELS:
            errs.append(f"{c['id']}: nivel_minimo inválido")

    for caso in b.casos:
        errs += _validate_case(b, caso)
    return errs


def _check_refs(b: Bank, owner: str, fundamentos: list[dict]) -> list[str]:
    errs = []
    for f in fundamentos:
        alias, sep, path = f.get("chave", "").partition("#")
        if not sep or not path:
            errs.append(f"{owner}: chave malformada {f.get('chave')!r}")
        elif alias not in b.normas:
            errs.append(f"{owner}: alias de norma desconhecido {alias!r}")
        if not f.get("trecho"):
            errs.append(f"{owner}: fundamento {f.get('chave')} sem trecho")
    return errs


def _validate_case(b: Bank, caso: dict) -> list[str]:
    cid = caso.get("id", "?")
    errs = []
    if caso.get("papel") not in ROLES:
        errs.append(f"{cid}: papel inválido {caso.get('papel')!r}")
    if caso.get("nivel") not in LEVELS:
        errs.append(f"{cid}: nível inválido")
    cenas = caso.get("cenas", {})
    if caso.get("inicio") not in cenas:
        errs.append(f"{cid}: cena inicial inexistente")
        return errs
    for sid, cena in cenas.items():
        for fala in cena.get("falas", []):
            if fala.get("quem") not in b.elenco:
                errs.append(f"{cid}/{sid}: personagem desconhecido {fala.get('quem')!r}")
        if not cena.get("escolhas"):
            errs.append(f"{cid}/{sid}: cena sem escolhas")
        for i, e in enumerate(cena.get("escolhas", [])):
            nxt = e.get("proxima")
            if nxt is not None and nxt not in cenas:
                errs.append(f"{cid}/{sid}#{i}: próxima cena inexistente {nxt!r}")
            if not e.get("feedback"):
                errs.append(f"{cid}/{sid}#{i}: escolha sem feedback")
            errs += _check_refs(b, f"{cid}/{sid}#{i}", _fundamentos(e))

    # alcançabilidade e ausência de ciclos (todo caminho termina)
    state: dict[str, int] = {}  # 1 = visitando, 2 = concluído

    def dfs(s: str) -> None:
        state[s] = 1
        for e in cenas[s]["escolhas"]:
            n = e.get("proxima")
            if n is None or n not in cenas:
                continue
            if state.get(n) == 1:
                errs.append(f"{cid}: ciclo envolvendo a cena {n}")
            elif n not in state:
                dfs(n)
        state[s] = 2

    dfs(caso["inicio"])
    for sid in cenas:
        if sid not in state:
            errs.append(f"{cid}: cena {sid} inalcançável")

    finais = caso.get("finais", [])
    if not finais or min(f["min"] for f in finais) > -50:
        errs.append(f"{cid}: precisa de um final que cubra qualquer pontuação (min <= -50)")
    if errs or not finais:  # grafo quebrado ou com ciclo: não dá para calcular o máximo
        return errs
    best = best_score(caso)
    if best < max(f["min"] for f in finais):
        errs.append(f"{cid}: o melhor final é inalcançável (máximo possível {best})")
    return errs


def best_score(caso: dict) -> int:
    """Maior pontuação possível (argumento + credibilidade) no grafo do caso."""
    cenas = caso["cenas"]

    @lru_cache(maxsize=None)
    def go(s: str) -> int:
        best = -10**9
        for e in cenas[s]["escolhas"]:
            gain = sum(e.get("efeito", {}).values())
            n = e.get("proxima")
            best = max(best, gain + (go(n) if n else 0))
        return best

    return go(caso["inicio"])


# ---------------------------------------------------------------- catálogo


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace("“", '"').replace("”", '"').replace("º", "o").replace("°", "o")
    return re.sub(r"\s+", " ", s).strip()


def all_fundamentos(b: Bank):
    for q in b.questoes:
        for f in _fundamentos(q):
            yield q["id"], f
    for caso in b.casos:
        for sid, cena in caso["cenas"].items():
            for i, e in enumerate(cena["escolhas"]):
                for f in _fundamentos(e):
                    yield f"{caso['id']}/{sid}#{i}", f


def validate_against_catalog(b: Bank, db_path: str | Path) -> tuple[list[str], int, int]:
    """Devolve (problemas, fundamentos conferidos, fundamentos cuja norma não está no catálogo)."""
    db = sqlite3.connect(str(db_path))
    problems, checked, absent = [], 0, 0
    try:
        norms = {r[0] for r in db.execute("SELECT id FROM norma")}
        for owner, f in all_fundamentos(b):
            chave = b.resolve(f["chave"])
            norma_id = chave.split("#", 1)[0]
            if norma_id not in norms:
                absent += 1  # recorte do usuário não inclui essa norma: nada a conferir
                continue
            row = db.execute("SELECT texto, rubrica FROM dispositivo WHERE chave = ?", (chave,)).fetchone()
            checked += 1
            if row is None:
                problems.append(f"{owner}: dispositivo {f['chave']} não existe no texto vigente")
                continue
            texto = _norm(" ".join(x for x in row if x))
            if _norm(f["trecho"]) not in texto:
                problems.append(f"{owner}: trecho não encontrado em {f['chave']}: {f['trecho']!r}")
    finally:
        db.close()
    return problems, checked, absent
