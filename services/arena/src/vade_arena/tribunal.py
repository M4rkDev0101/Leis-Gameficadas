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
import re
from functools import lru_cache
from importlib import resources

from .recompensas import raridade_carta

CREDIBILIDADE_MAX = 5
SCENE_TYPES = {"titulo", "dialogo", "depoimento", "apresentar", "escolha", "decidir", "investigar", "veredicto"}
EXPRESSIONS = {"normal", "feliz", "bravo", "nervoso", "chocado", "pensativo", "triste", "confiante", "apontando"}
EFFECTS = {"protesto", "martelo", "tremor", "bater", "flash", "ummomento", "tomaisso"}
LOCAIS = {"tribunal", "escritorio", "rua", "bar", "delegacia", "parlatorio", "apartamento", "gabinete", "obra",
          "mercado", "ponto", "juri", "loja", "clinica"}
POSICOES = {"defesa", "acusacao", "juiz", "testemunha", "escritorio", "cena"}
XP_BASE = {"basico": 80, "intermediario": 120, "avancado": 170, "especialista": 230}
# Ajuste de XP pela duração estimada: o XP base do nível vale para um caso de DUR_REF minutos; cada minuto a mais
# (ou a menos) soma (ou tira) DUR_XP_MIN, arredondado a múltiplos de 5 e limitado a [DUR_MIN, DUR_MAX].
DUR_REF, DUR_XP_MIN, DUR_MIN, DUR_MAX = 12.0, 3.0, -20, 45
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


def xp_base(ep: dict) -> int:
    """XP base do episódio: base do nível + ajuste pela duração estimada (casos longos pagam mais, curtos menos)."""
    ajuste = round((estimate_minutes(ep) - DUR_REF) * DUR_XP_MIN / 5) * 5
    return XP_BASE[ep["nivel"]] + max(DUR_MIN, min(DUR_MAX, ajuste))


def cover_info(data: dict, ep: dict) -> dict:
    """Dados leves para a capa do menu: personagem-chave do caso, expressão típica, local principal e nº de cenas."""
    chars, pos = data.get("personagens", {}), ep.get("posicoes", {})
    score: dict[str, float] = {}
    exprs: dict[str, list[str]] = {}
    local = None
    for c in ep["cenas"].values():
        if c["tipo"] == "investigar" and c.get("local") and not local:
            local = c["local"]
        w = 3 if c["tipo"] == "depoimento" else 1
        for f in _falas(c):
            q = f.get("q")
            if q in chars and q not in ("voce", "narrador"):
                score[q] = score.get(q, 0) + w
                exprs.setdefault(q, []).append(f.get("e", "normal"))
    for q in pos:
        if q in chars and q not in ("voce", "narrador"):
            score[q] = score.get(q, 0) + {"testemunha": 4, "defesa": 2, "acusacao": 2, "juiz": -6}.get(pos[q], 0)
    cands = [q for q in score if chars[q].get("visual")]
    if not cands:
        return {"cenas": len(ep["cenas"]), "local": local, "ordem": list(ep["cenas"])}
    q = max(cands, key=lambda k: (score[k], k))
    emot = [e for e in exprs.get(q, []) if e != "normal"]
    # "nervoso" é a expressão padrão das testemunhas pressionadas: conta pela metade para as capas não ficarem todas iguais
    expr = max(set(emot), key=lambda e: (emot.count(e) * (.5 if e == "nervoso" else 1), e)) if emot else "normal"
    return {"q": q, "nome": chars[q].get("nome"), "visual": chars[q]["visual"], "expr": expr, "pos": pos.get(q, "testemunha"),
            "local": local, "cenas": len(ep["cenas"]), "ordem": list(ep["cenas"])}


def _cover(data: dict, ep: dict) -> dict:
    c = cover_info(data, ep)
    c.pop("ordem", None)
    return c


def _progress(ep: dict, scene: str | None) -> float | None:
    """Fração do caso já percorrida, pela posição da cena salva na ordem do roteiro (None sem jogo salvo)."""
    if not scene:
        return None
    order = list(ep["cenas"])
    return round((order.index(scene) + 1) / len(order), 3) if scene in order else None


def career(data: dict, won: dict[str, float], saves: set[str], save_scenes: dict[str, str] | None = None) -> dict:
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
            items.append({**summary(ep), "status": status, "melhor": best, "salvo": ep["id"] in saves, "minutos": minutes,
                          "capa": _cover(data, ep), "progresso": _progress(ep, (save_scenes or {}).get(ep["id"]))})
        out.append({**ato, "episodios": items})
    avulsos = [{**summary(e), "minutos": estimate_minutes(e), "melhor": won.get(e["id"]), "salvo": e["id"] in saves,
                "capa": _cover(data, e), "progresso": _progress(e, (save_scenes or {}).get(e["id"]))}
               for e in data["episodios"] if e.get("avulso")]
    return {"atos": out, "avulsos": avulsos, "horas_total": round(total_min / 60, 1), "horas_jogadas": round(done_min / 60, 1),
            "concluidos": sum(1 for a in out for e in a["episodios"] if e["status"] == "concluido"),
            "total": sum(len(a["episodios"]) for a in out)}


def episode(data: dict, ep_id: str) -> dict:
    for ep in data["episodios"]:
        if ep["id"] == ep_id:
            return ep
    raise KeyError(f"episódio desconhecido: {ep_id}")


MARCA_RE = re.compile(r"^[a-z0-9_]{2,40}$")


def episode_marks(ep: dict) -> set[str]:
    """Marcas que as escolhas livres deste episódio podem deixar na carreira."""
    return {o["marca"] for c in ep["cenas"].values() if c.get("livre") for o in c.get("opcoes", []) if o.get("marca")}


def choice_texts(data: dict) -> dict[str, dict]:
    """Marca -> texto da opção escolhida e caso em que foi feita (para o resumo da carreira)."""
    return {o["marca"]: {"texto": o["t"], "caso": ep["titulo"]} for ep in data["episodios"] for c in ep["cenas"].values()
            if c.get("livre") for o in c.get("opcoes", []) if o.get("marca")}


RARIDADE_CONQUISTA = {"primeiro": "comum", "perfeito": "comum", "escolhas": "incomum", "perfeito10": "rara", "carreira": "lendaria"}


def achievements(data: dict, won: dict[str, float], perfect: set[str], marks: set[str],
                 extras: dict | None = None) -> list[dict]:
    """Conquistas calculadas do histórico (nada é gravado à parte: refazer um caso só melhora).

    Cada uma traz ``progresso`` {atual, meta} (para a barra "7/10") e ``raridade``. ``extras`` (opcional):
    contradicoes, combo_max, cartas, cartas_total, notas_s, streak_max, dias_completos."""
    ex = extras or {}
    atos = [(a, [e["id"] for e in data["episodios"] if e.get("ato") == a["id"]]) for a in data.get("atos", [])]
    done = {k for k, v in won.items() if v and v > 0}
    career_ids = [i for _, ids in atos for i in ids]

    def conq(id_, icone, nome, desc, atual, meta, raridade):
        return {"id": id_, "icone": icone, "nome": nome, "descricao": desc, "ok": atual >= meta,
                "progresso": {"atual": min(atual, meta), "meta": meta}, "raridade": raridade}

    out = [
        conq("primeiro", "⚖️", "Primeiro veredicto", "Vença o seu primeiro caso.", len(done), 1, "comum"),
        conq("perfeito", "✨", "Sem um arranhão", "Vença um caso sem perder credibilidade.", len(perfect), 1, "comum"),
        conq("perfeito10", "💎", "Mão firme", "Dez casos perfeitos.", len(perfect), 10, "rara"),
    ]
    for a, ids in atos:
        if ids:
            out.append(conq("ato-" + a["id"], "🏛️", f"{a['cargo']}", f"Conclua o Ato {a['numero']}: {a['titulo']}.",
                            sum(i in done for i in ids), len(ids), "incomum"))
            out.append(conq("impecavel-" + a["id"], "🌟", f"Impecável no Ato {a['numero']}", "Todos os casos do ato perfeitos.",
                            sum(i in perfect for i in ids), len(ids), "epica"))
    out.append(conq("carreira", "👑", "Da toga ao veredicto final", "Conclua o Modo Carreira.",
                    sum(i in done for i in career_ids), max(1, len(career_ids)), "lendaria"))
    out.append(conq("escolhas", "🧭", "Consciência", "Tome cinco decisões morais na carreira.", len(marks), 5, "incomum"))
    out += [
        conq("contradicoes10", "🔎", "Olho clínico", "Aponte dez contradições.", ex.get("contradicoes", 0), 10, "comum"),
        conq("contradicoes50", "🕵️", "Inquisidor(a)", "Aponte cinquenta contradições.", ex.get("contradicoes", 0), 50, "rara"),
        conq("combo8", "🔥", "Sem piscar", "Encadeie oito acertos seguidos em um julgamento.", ex.get("combo_max", 0), 8, "incomum"),
        conq("notas_s5", "🏅", "Colecionador(a) de selos", "Selo dourado (nota S) em cinco casos.", ex.get("notas_s", 0), 5, "rara"),
        conq("album25", "🃏", "Jurisprudência na mão", "Reúna 25 cartas no álbum.", ex.get("cartas", 0), 25, "incomum"),
        conq("album-tudo", "📚", "Biblioteca completa", "Complete o álbum de cartas.", ex.get("cartas", 0), max(1, ex.get("cartas_total", 0)), "lendaria"),
        conq("streak7", "📅", "Uma semana de toga", "Jogue em 7 dias seguidos.", ex.get("streak_max", 0), 7, "incomum"),
        conq("dia10", "⚡", "Relâmpago", "Feche o desafio do dia dez vezes.", ex.get("dias_completos", 0), 10, "incomum"),
    ]
    return out


def cards_catalog(data: dict) -> dict[str, dict]:
    """Cartas de jurisprudência: uma por dispositivo citado nos casos. Raridade = caso mais difícil que o cita."""
    niveis: dict[str, list[str]] = {}
    donos: dict[str, list[str]] = {}
    ep_nivel = {e["id"]: e["nivel"] for e in data["episodios"]}
    for dono, f in all_fundamentos(data):
        ep_id = dono.split("/")[0]
        niveis.setdefault(f["chave"], []).append(ep_nivel[ep_id])
        donos.setdefault(f["chave"], [])
        if ep_id not in donos[f["chave"]]:
            donos[f["chave"]].append(ep_id)
    return {k: {"chave": k, "raridade": raridade_carta(niveis[k], len(donos[k])), "casos": donos[k], "trecho": ""} for k in sorted(niveis)}


def episode_cards(data: dict, ep_id: str) -> list[dict]:
    cat = cards_catalog(data)
    return [{"chave": k, "raridade": c["raridade"]} for k, c in cat.items() if ep_id in c["casos"]]


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
    all_marcas = {m for e in data["episodios"] for m in episode_marks(e)}
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
            if c["tipo"] == "escolha" and c.get("livre"):
                # dilema: todas as opções valem, cada uma pode deixar uma marca na carreira
                if len(c.get("opcoes", [])) < 2 or any(o.get("certa") for o in c["opcoes"]):
                    errs.append(f"{where}: escolha livre precisa de 2+ opções e nenhuma 'certa'")
            elif c["tipo"] == "escolha":
                n_ok = sum(1 for o in c.get("opcoes", []) if o.get("certa"))
                if n_ok != 1 or len(c.get("opcoes", [])) < 2:
                    errs.append(f"{where}: escolha precisa de 2+ opções e exatamente 1 certa")
            for o in c.get("opcoes", []):
                if "marca" in o and (not c.get("livre") or not MARCA_RE.match(str(o["marca"]))):
                    errs.append(f"{where}: marca inválida {o['marca']!r} (só em escolha livre; a-z, 0-9 e _)")
            conds = [f.get("se") for f in _falas(c)] + [v.get("se") for v in c.get("variantes", [])]
            for cond in filter(None, conds):
                if cond.lstrip("!") not in all_marcas:
                    errs.append(f"{where}: condição usa marca que nenhuma escolha cria {cond!r}")
            for v in c.get("variantes", []):
                if not v.get("se") or not any(v.get(k) for k in ("carimbo", "titulo", "texto")):
                    errs.append(f"{where}: variante de veredicto precisa de 'se' e de carimbo/título/texto")
            if "dica" in c:
                dicas = c["dica"] if isinstance(c["dica"], list) else [c["dica"]]
                if c["tipo"] not in INTERACTIVE - {"investigar"} or not 1 <= len(dicas) <= 2                         or not all(isinstance(d, str) and d.strip() for d in dicas):
                    errs.append(f"{where}: 'dica' deve ser texto (ou [vaga, específica]) em cena com erro possível")
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
    xp = (xp_base(ep) + 20 * credibilidade + (60 if perfeito else 0)) if venceu else 25
    return {"credibilidade": credibilidade, "erros": erros, "venceu": venceu, "perfeito": perfeito, "xp": xp,
            "aproveitamento": round(credibilidade / CREDIBILIDADE_MAX, 4) if venceu else 0.0,
            "carimbo": _carimbo(ep) if venceu else "DESTITUÍDO", "faixa": "otimo" if perfeito else ("medio" if venceu else "ruim")}


def _carimbo(ep: dict) -> str:
    for c in ep["cenas"].values():
        if c["tipo"] == "veredicto":
            return c.get("carimbo", "VEREDICTO")
    return "VEREDICTO"
