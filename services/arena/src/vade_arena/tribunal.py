"""Modo Tribunal: julgamentos jogáveis no estilo dos jogos de simulação de tribunal.

O roteiro (``content/tribunal.json``) é um grafo de cenas:

* ``titulo``      — cartão de abertura do episódio;
* ``dialogo``     — falas com personagem, expressão e efeito (protesto, martelo, tremor…);
* ``depoimento``  — a testemunha faz afirmações; o jogador pode *pressionar* cada uma ou
  *apresentar* uma prova. Uma afirmação é contraditória e uma das provas a derruba;
* ``apresentar``  — o jogador escolhe nos autos a prova/lei que responde ao argumento;
* ``escolha``     — alternativas com uma correta; erro custa credibilidade e repete a pergunta;
* ``decidir``     — o jogador é o juiz e decide o protesto (deferir/indeferir);
* ``investigar``  — explorar um local: pontos para examinar e pessoas para conversar; algumas
  provas são obrigatórias para seguir;
* ``veredicto``   — fim do episódio.

O conteúdo é dividido em ``content/tribunal.json`` (personagens, normas e atos da carreira) e
``content/atoN.json`` (episódios de cada ato). Nomes curtos de propósito: o Windows limita
caminhos a 260 caracteres.

O motor roda no navegador (``web/tribunal.html``). O servidor entrega o roteiro, enriquece as
leis com o texto vigente do catálogo e calcula o XP no fim (com limites, para não confiar no
cliente). Este módulo valida o roteiro: referências, alcançabilidade e fundamentos.
"""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from importlib import resources

CREDIBILIDADE_MAX = 5
SCENE_TYPES = {"titulo", "dialogo", "depoimento", "apresentar", "escolha", "decidir", "investigar", "veredicto"}
EXPRESSIONS = {"normal", "feliz", "bravo", "nervoso", "chocado", "pensativo", "triste", "confiante", "apontando"}
EFFECTS = {"protesto", "martelo", "tremor", "bater", "flash", "ummomento", "tomaisso"}
LOCAIS = {"tribunal", "escritorio", "rua", "bar", "delegacia", "parlatorio", "apartamento", "gabinete", "obra",
          "mercado", "ponto", "juri"}
POSICOES = {"defesa", "acusacao", "juiz", "testemunha", "escritorio", "cena"}
XP_BASE = {"basico": 80, "intermediario": 120, "avancado": 170, "especialista": 230}
INTERACTIVE = {"depoimento", "apresentar", "escolha", "decidir", "investigar"}


@lru_cache(maxsize=1)
def load() -> dict:
    content = resources.files(__package__).joinpath("content")
    data = json.loads(content.joinpath("tribunal.json").read_text(encoding="utf-8"))
    data.setdefault("atos", [])
    for f in sorted((x for x in content.iterdir() if x.name.startswith("ato") and x.name.endswith(".json")),
                    key=lambda x: x.name):
        extra = json.loads(f.read_text(encoding="utf-8"))
        for ep in extra.get("episodios", []):
            ep.setdefault("ato", extra.get("ato"))
            data["episodios"].append(ep)
        data["personagens"].update(extra.get("personagens", {}))
    # carreira na ordem dos atos; episódios avulsos no fim
    data["episodios"].sort(key=lambda e: (not e.get("ato"), e.get("ato") or "", e.get("ordem", 0)))
    return data


def estimate_minutes(ep: dict) -> float:
    """Duração estimada: leitura (~170 palavras/min, com a animação do texto) + ~25 s por decisão
    + ~40 s por ponto de investigação. Serve para mostrar ao jogador e medir a meta de horas."""
    words, decisions, spots = 0, 0, 0
    for c in ep["cenas"].values():
        for f in _falas(c):
            words += len(f.get("t", "").split())
        for a in c.get("afirmacoes", []):
            words += len(a["t"].split()) * 2  # lidas no depoimento e de novo no interrogatório
        if c["tipo"] in INTERACTIVE:
            decisions += 1
        spots += len(c.get("pontos", [])) + len(c.get("conversas", []))
    return round(words / 170 + decisions * 25 / 60 + spots * 40 / 60, 1)


def career(data: dict, won: dict[str, float], saves: set[str]) -> dict:
    """Atos e episódios com estado: bloqueado, disponível (ou com jogo salvo) e concluído."""
    eps = sorted((e for e in data["episodios"] if e.get("ato")), key=lambda e: (e["ato"], e.get("ordem", 0)))
    out, unlocked, total_min, done_min = [], True, 0.0, 0.0
    for ato in data["atos"]:
        items = []
        for ep in [e for e in eps if e["ato"] == ato["id"]]:
            minutes = estimate_minutes(ep)
            total_min += minutes
            best = won.get(ep["id"])
            status = "concluido" if best and best > 0 else ("disponivel" if unlocked else "bloqueado")
            if status == "concluido":
                done_min += minutes
            elif status == "disponivel":
                unlocked = False  # só o próximo caso fica liberado
            items.append({**summary(ep), "status": status, "melhor": best, "salvo": ep["id"] in saves, "minutos": minutes})
        out.append({**ato, "episodios": items})
    avulsos = [{**summary(e), "minutos": estimate_minutes(e), "melhor": won.get(e["id"]), "salvo": e["id"] in saves}
               for e in data["episodios"] if e.get("avulso")]
    return {"atos": out, "avulsos": avulsos, "horas_total": round(total_min / 60, 1), "horas_jogadas": round(done_min / 60, 1),
            "concluidos": sum(1 for a in out for e in a["episodios"] if e["status"] == "concluido"),
            "total": sum(len(a["episodios"]) for a in out)}


def episode(data: dict, ep_id: str) -> dict:
    for ep in data["episodios"]:
        if ep["id"] == ep_id:
            return ep
    raise KeyError(f"episódio desconhecido: {ep_id}")


def summary(ep: dict) -> dict:
    interativas = sum(1 for c in ep["cenas"].values() if c["tipo"] in INTERACTIVE)
    return {"id": ep["id"], "numero": ep["numero"], "titulo": ep["titulo"], "papel": ep["papel"], "nivel": ep["nivel"],
            "sinopse": ep["sinopse"], "desafios": interativas, "ato": ep.get("ato")}


def all_fundamentos(data: dict):
    """(dono, {chave, trecho}) de todas as leis citadas: provas do tipo lei e fundamentos das cenas."""
    for ep in data["episodios"]:
        for p in ep["provas"]:
            if p["tipo"] == "lei":
                yield f"{ep['id']}/prova:{p['id']}", {"chave": p["chave"], "trecho": p["trecho"]}
        for sid, cena in ep["cenas"].items():
            for f in cena.get("fundamentos", []):
                yield f"{ep['id']}/{sid}", f
            for i, o in enumerate(cena.get("opcoes", [])):
                for f in o.get("fundamentos", []):
                    yield f"{ep['id']}/{sid}#{i}", f


def _falas(cena: dict) -> list[dict]:
    out = list(cena.get("falas", [])) + list(cena.get("intro", [])) + list(cena.get("acerto", [])) + list(cena.get("erro", []))
    for a in cena.get("afirmacoes", []):
        out += a.get("pressionar", [])
    for p in cena.get("pontos", []) + cena.get("conversas", []):
        out += p.get("falas", [])
    for o in cena.get("opcoes", []):
        out += o.get("falas", [])
    return out


def validate(data: dict, normas: dict[str, str]) -> list[str]:
    errs: list[str] = []
    chars = data["personagens"]
    seen_ids = set()
    atos = {a["id"] for a in data.get("atos", [])}
    ordens: set[tuple] = set()
    for ep in data["episodios"]:
        if ep.get("ato"):
            if ep["ato"] not in atos:
                errs.append(f"{ep['id']}: ato desconhecido {ep['ato']}")
            key = (ep["ato"], ep.get("ordem"))
            if key in ordens:
                errs.append(f"{ep['id']}: ordem repetida no {ep['ato']}")
            ordens.add(key)
        elif not ep.get("avulso"):
            errs.append(f"{ep['id']}: episódio sem ato precisa ser marcado como avulso")
    for ep in data["episodios"]:
        eid = ep.get("id", "?")
        if eid in seen_ids:
            errs.append(f"{eid}: id repetido")
        seen_ids.add(eid)
        if ep.get("papel") not in ("advogado", "promotor", "juiz"):
            errs.append(f"{eid}: papel inválido")
        if ep.get("nivel") not in XP_BASE:
            errs.append(f"{eid}: nível inválido")
        provas = {p["id"]: p for p in ep["provas"]}
        if len(provas) != len(ep["provas"]):
            errs.append(f"{eid}: prova com id repetido")
        for p in ep["provas"]:
            if p["tipo"] not in ("prova", "lei"):
                errs.append(f"{eid}/{p['id']}: tipo de prova inválido")
            if p["tipo"] == "lei" and (not p.get("chave") or not p.get("trecho")):
                errs.append(f"{eid}/{p['id']}: lei sem chave ou trecho")
        for who, pos in ep.get("posicoes", {}).items():
            if who not in chars:
                errs.append(f"{eid}: posição para personagem desconhecido {who}")
            if pos not in POSICOES:
                errs.append(f"{eid}: posição inválida {pos}")
        cenas = ep["cenas"]
        if ep.get("inicio") not in cenas:
            errs.append(f"{eid}: cena inicial inexistente")
            continue
        received: set[str] = set()
        for sid, c in cenas.items():
            where = f"{eid}/{sid}"
            if c.get("tipo") not in SCENE_TYPES:
                errs.append(f"{where}: tipo de cena inválido {c.get('tipo')!r}")
                continue
            if c.get("local") and c["local"] not in LOCAIS:
                errs.append(f"{where}: local inválido {c['local']}")
            if c["tipo"] != "veredicto" and c.get("proxima") not in cenas:
                errs.append(f"{where}: próxima cena inexistente {c.get('proxima')!r}")
            for f in _falas(c):
                if f.get("q") not in chars:
                    errs.append(f"{where}: personagem desconhecido {f.get('q')!r}")
                elif f["q"] not in ("narrador",) and f["q"] not in ep.get("posicoes", {}):
                    errs.append(f"{where}: {f['q']} fala mas não tem posição no episódio")
                if f.get("e") and f["e"] not in EXPRESSIONS:
                    errs.append(f"{where}: expressão inválida {f['e']!r}")
                if f.get("fx") and f["fx"] not in EFFECTS:
                    errs.append(f"{where}: efeito inválido {f['fx']!r}")
                if not f.get("t"):
                    errs.append(f"{where}: fala vazia")
                for r in f.get("recebe", []):
                    if r not in provas:
                        errs.append(f"{where}: recebe prova inexistente {r}")
                    received.add(r)
            if c["tipo"] == "depoimento":
                af = c.get("afirmacoes", [])
                ct = c.get("contradicao", {})
                if c.get("testemunha") not in ep.get("posicoes", {}):
                    errs.append(f"{where}: testemunha sem posição")
                if not 0 <= ct.get("afirmacao", -1) < len(af):
                    errs.append(f"{where}: contradição aponta para afirmação inexistente")
                for pid in ct.get("provas", []):
                    if pid not in provas:
                        errs.append(f"{where}: contradição usa prova inexistente {pid}")
                if not ct.get("provas"):
                    errs.append(f"{where}: contradição sem prova")
            if c["tipo"] == "investigar":
                if c.get("local") not in LOCAIS:
                    errs.append(f"{where}: investigação precisa de local válido")
                obtained = set()
                for pt in c.get("pontos", []):
                    for k in ("x", "y", "w", "h"):
                        if not isinstance(pt.get(k), (int, float)) or not 0 <= pt[k] <= 100:
                            errs.append(f"{where}/{pt.get('id')}: coordenada {k} deve estar entre 0 e 100")
                    if not pt.get("nome") or not pt.get("falas"):
                        errs.append(f"{where}/{pt.get('id')}: ponto precisa de nome e falas")
                for conv in c.get("conversas", []):
                    if conv.get("q") not in ep.get("posicoes", {}):
                        errs.append(f"{where}: conversa com personagem sem posição {conv.get('q')!r}")
                    if not conv.get("titulo") or not conv.get("falas"):
                        errs.append(f"{where}: conversa precisa de título e falas")
                for item in c.get("pontos", []) + c.get("conversas", []):
                    for f in item.get("falas", []):
                        obtained |= set(f.get("recebe", []))
                for pid in c.get("requer", []):
                    if pid not in provas:
                        errs.append(f"{where}: requer prova inexistente {pid}")
                    elif pid not in obtained:
                        errs.append(f"{where}: requer {pid}, mas nenhum ponto ou conversa desta investigação a entrega")
                if not c.get("pontos") and not c.get("conversas"):
                    errs.append(f"{where}: investigação vazia")
            if c["tipo"] == "apresentar":
                if not c.get("provas") or any(p not in provas for p in c["provas"]):
                    errs.append(f"{where}: provas aceitas inválidas")
            if c["tipo"] == "escolha":
                n_ok = sum(1 for o in c.get("opcoes", []) if o.get("certa"))
                if n_ok != 1 or len(c.get("opcoes", [])) < 2:
                    errs.append(f"{where}: escolha precisa de 2+ opções e exatamente 1 certa")
            if c["tipo"] == "decidir" and c.get("correta") not in ("deferir", "indeferir"):
                errs.append(f"{where}: decisão correta deve ser deferir ou indeferir")
            for f in c.get("fundamentos", []) + [f for o in c.get("opcoes", []) for f in o.get("fundamentos", [])]:
                alias = f.get("chave", "").split("#", 1)[0]
                if alias not in normas:
                    errs.append(f"{where}: alias de norma desconhecido {alias!r}")
        for p in ep["provas"]:
            if p["tipo"] == "lei" and p["chave"].split("#", 1)[0] not in normas:
                errs.append(f"{eid}/{p['id']}: alias de norma desconhecido")
        # provas exigidas precisam ter sido entregues em algum momento
        needed = {pid for c in cenas.values() for pid in c.get("provas", []) + c.get("contradicao", {}).get("provas", [])}
        for pid in needed - received:
            errs.append(f"{eid}: a prova {pid} é exigida mas nunca é entregue ao jogador")
        # alcançabilidade e término (o grafo é uma cadeia/DAG que termina em veredicto)
        state: dict[str, int] = {}
        stack = [ep["inicio"]]
        while stack:
            s = stack.pop()
            if s in state or s not in cenas:
                continue
            state[s] = 1
            nxt = cenas[s].get("proxima")
            if nxt:
                stack.append(nxt)
        for sid in cenas:
            if sid not in state:
                errs.append(f"{eid}: cena {sid} inalcançável")
        if not any(cenas[s]["tipo"] == "veredicto" for s in state):
            errs.append(f"{eid}: nenhum veredicto alcançável")
        # ciclo: seguir 'proxima' a partir do início não pode repetir cena
        s, walked = ep["inicio"], set()
        while s and s in cenas:
            if s in walked:
                errs.append(f"{eid}: ciclo na cena {s}")
                break
            walked.add(s)
            s = cenas[s].get("proxima")
    return errs


def public_episode(data: dict, ep: dict, lookup, player_avatar: dict | None, player_name: str) -> dict:
    """Episódio para o navegador: personagens usados, provas com o texto vigente da lei."""
    used = set(ep["posicoes"]) | {"narrador"}
    chars = {k: dict(v) for k, v in data["personagens"].items() if k in used}
    chars["voce"] = {**chars.get("voce", {}), "nome": player_name or "Você", "visual": player_avatar}
    def enrich(f: dict) -> dict:
        item = dict(f)
        found = lookup(f["chave"]) if lookup else None
        if found:
            item["texto"] = found["texto"]
            item["rotulo"] = found.get("rotulo")
            item["norma"] = found.get("norma")
        return item

    provas = [enrich(p) if p["tipo"] == "lei" else dict(p) for p in ep["provas"]]
    cenas = copy.deepcopy(ep["cenas"])
    for c in cenas.values():
        if "fundamentos" in c:
            c["fundamentos"] = [enrich(f) for f in c["fundamentos"]]
        for o in c.get("opcoes", []):
            if "fundamentos" in o:
                o["fundamentos"] = [enrich(f) for f in o["fundamentos"]]
    return {**ep, "cenas": cenas, "personagens": chars, "provas": provas}


def score(ep: dict, credibilidade: int, erros: int) -> dict:
    """XP do episódio, calculado no servidor com limites (o cliente só informa o resultado)."""
    credibilidade = max(0, min(CREDIBILIDADE_MAX, int(credibilidade)))
    erros = max(0, min(99, int(erros)))
    venceu = credibilidade > 0
    perfeito = venceu and erros == 0
    xp = (XP_BASE[ep["nivel"]] + 20 * credibilidade + (60 if perfeito else 0)) if venceu else 25
    return {"credibilidade": credibilidade, "erros": erros, "venceu": venceu, "perfeito": perfeito, "xp": xp,
            "aproveitamento": round(credibilidade / CREDIBILIDADE_MAX, 4) if venceu else 0.0,
            "carimbo": _carimbo(ep) if venceu else "DESTITUÍDO", "faixa": "otimo" if perfeito else ("medio" if venceu else "ruim")}


def _carimbo(ep: dict) -> str:
    for c in ep["cenas"].values():
        if c["tipo"] == "veredicto":
            return c.get("carimbo", "VEREDICTO")
    return "VEREDICTO"
