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
* ``audiencia``   — (juiz) a audiência corre fala a fala; o jogador decide quando intervir e como
  (indeferir pergunta, advertir, cassar a palavra…). Intervir sem motivo ou se omitir custa credibilidade;
* ``palavra``     — (juiz) conceder a palavra: ordem e tempo de cada orador (alegações finais, debates do júri);
* ``sentenca``    — (juiz) montar a sentença escolhendo uma peça para cada parte (relatório, fundamentação…);
* ``protesto``    — (advogado/promotor) a outra parte inquire; o jogador protesta na hora certa e dá o fundamento;
* ``denuncia``    — (promotor) montar a denúncia: partes com opções e partes que exigem uma prova dos autos;
* ``plenario``    — (STF) convencer os ministros um a um; o placar de votos decide. Com ``colegiado: "juri"`` são os
  7 jurados do Conselho de Sentença (maioria 4): o jogador lê a reação de cada um ('rotulo', ex. "Jurada 3") nos debates;
* ``tensao``      — (fora do tribunal) escolha no susto, com cronômetro; o tempo esgotado vale a opção 'padrao';
* ``celular``     — (fora do tribunal) mensagens chegando no celular (provocações, ameaças), com resposta opcional;
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
SCENE_TYPES = {"titulo", "dialogo", "depoimento", "apresentar", "escolha", "decidir", "investigar", "veredicto",
               "analisar", "convocar", "acareacao", "argumento", "intuicao", "blefe", "reviravolta",
               "audiencia", "palavra", "sentenca", "protesto", "denuncia", "plenario", "tensao", "celular"}
EXPRESSIONS = {"normal", "feliz", "bravo", "nervoso", "chocado", "pensativo", "triste", "confiante", "apontando"}
EFFECTS = {"protesto", "martelo", "tremor", "bater", "flash", "ummomento", "tomaisso", "ordem"}
LOCAIS = {"tribunal", "escritorio", "rua", "bar", "delegacia", "parlatorio", "apartamento", "gabinete", "obra",
          "mercado", "ponto", "juri", "loja", "clinica",
          # cenários novos (frente "cada papel no seu papel"): até a arte chegar, usam o fundo genérico
          "custodia", "stf", "promotoria", "garagem", "carro", "casa", "corredor", "praca", "cafe", "cemiterio"}
POSICOES = {"defesa", "acusacao", "juiz", "testemunha", "escritorio", "cena"}
XP_BASE = {"basico": 80, "intermediario": 120, "avancado": 170, "especialista": 230, "impossivel": 300}
# Ajuste de XP pela duração estimada: o XP base do nível vale para um caso de DUR_REF minutos; cada minuto a mais
# (ou a menos) soma (ou tira) DUR_XP_MIN, arredondado a múltiplos de 5 e limitado a [DUR_MIN, DUR_MAX].
DUR_REF, DUR_XP_MIN, DUR_MIN, DUR_MAX = 12.0, 3.0, -20, 45
INTERACTIVE = {"depoimento", "apresentar", "escolha", "decidir", "investigar", "analisar", "convocar", "acareacao",
               "argumento", "intuicao", "blefe", "reviravolta", "audiencia", "palavra", "sentenca",
               "protesto", "denuncia", "plenario"}
PERFIS = {"verdadeira", "mentirosa", "hostil"}
RISCOS = {"baixo", "medio", "alto"}
MARCAS_AUTOMATICAS = ("usou_falsa", "descartou_autentica", "hostil_revelou", "blefou", "blefe_descoberto")


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
        # marcas que um ato declara para episódios escritos em paralelo (criadas num arquivo, usadas em outro)
        data.setdefault("marcas_declaradas", set()).update(extra.get("marcas_declaradas", []))
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
        decisions += sum(1 for ln in c.get("linhas", []) if ln.get("incidente")) + max(0, len(c.get("partes", [])) - 1) \
            + max(0, len(c.get("ministros", [])) - 1)
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


def contradicoes_of(c: dict) -> list[dict]:
    """Contradições de um depoimento: a lista nova ('contradicoes') ou a antiga, de uma só ('contradicao')."""
    if c.get("contradicoes"):
        return list(c["contradicoes"])
    return [c["contradicao"]] if c.get("contradicao") else []


def sub_scenes(cenas: dict) -> set[str]:
    """Cenas de depoimento que só rodam dentro de uma 'convocar' ou de uma 'acareacao' (fora da cadeia 'proxima')."""
    out: set[str] = set()
    for c in cenas.values():
        if c.get("tipo") == "convocar":
            out |= {o.get("depoimento") for o in c.get("opcoes", [])}
        elif c.get("tipo") == "acareacao":
            out |= {c.get("a"), c.get("b")}
    return {x for x in out if x}


def episode_marks(ep: dict) -> set[str]:
    """Marcas que o episódio pode deixar: escolhas livres, efeitos de 'convocar' e as automáticas (prova falsa, hostil)."""
    out = {o["marca"] for c in ep["cenas"].values() if c.get("livre") for o in c.get("opcoes", []) if o.get("marca")}
    for c in ep["cenas"].values():
        if c.get("tipo") == "convocar":
            out |= {o["efeito"]["marca"] for o in c.get("opcoes", []) if (o.get("efeito") or {}).get("marca")}
        if c.get("tipo") == "depoimento" and c.get("hostil"):
            out.add("hostil_revelou")
    if any(p.get("autentica") is False for p in ep.get("provas", [])):
        out |= {"usou_falsa", "descartou_autentica"}
    if any(c.get("tipo") == "blefe" for c in ep["cenas"].values()):
        out |= {"blefou", "blefe_descoberto"}
    for c in ep["cenas"].values():
        if c.get("tipo") in ("intuicao", "tensao", "celular"):
            out |= {o["marca"] for o in c.get("opcoes", []) if o.get("marca")}
    return out


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
            for ln in cena.get("linhas", []):
                for f in (ln.get("incidente") or {}).get("fundamentos", []):
                    yield f"{ep['id']}/{sid}", f
            for i, o in enumerate(_opcoes_com_fundamento(cena)):
                for f in o.get("fundamentos", []):
                    yield f"{ep['id']}/{sid}#{i}", f
                if o.get("dispositivo"):
                    yield f"{ep['id']}/{sid}#{i}", {"chave": o["dispositivo"], "trecho": o.get("trecho", "")}


def _falas(cena: dict) -> list[dict]:
    out = list(cena.get("falas", [])) + list(cena.get("intro", [])) + list(cena.get("acerto", [])) + list(cena.get("erro", []))
    out += list(cena.get("erro_veraz", []))
    for a in cena.get("afirmacoes", []):
        out += a.get("pressionar", [])
    for ct in cena.get("contradicoes", []):
        out += ct.get("acerto", [])
    out += (cena.get("hostil") or {}).get("versao", []) + (cena.get("veracidade") or {}).get("revela", [])
    for pr in cena.get("pares", []):
        out += pr.get("falas", [])
    out += cena.get("revelacao", [])
    for o in cena.get("opcoes", []):
        if isinstance(o.get("blefe"), dict):
            out += o["blefe"].get("falas", []) + o["blefe"].get("consequencia", [])
    for p in cena.get("pontos", []) + cena.get("conversas", []):
        out += p.get("falas", [])
    for o in cena.get("opcoes", []):
        out += o.get("falas", [])
    out += list(cena.get("erro_ordem", [])) + list(cena.get("erro_omissao", [])) + list(cena.get("erro_interromper", []))
    for ln in cena.get("linhas", []):
        out.append({k: v for k, v in ln.items() if k in ("q", "e", "t", "fx", "se")})
        out += ln.get("cerceamento", [])
        inc = ln.get("incidente") or {}
        out += inc.get("omissao", [])
        for o in inc.get("opcoes", []):
            out += o.get("falas", [])
    for pt in cena.get("partes", []):
        out += pt.get("erro", [])
        for o in pt.get("opcoes", []):
            out += o.get("falas", [])
    out += list(cena.get("depois", []))
    for o in cena.get("opcoes", []):
        out += [m for m in o.get("retorno", []) if m.get("q")]
    for m in cena.get("ministros", []):
        out += m.get("falas", [])
        for a in m.get("argumentos", []):
            out += a.get("falas", [])
    return out


def _opcoes_com_fundamento(cena: dict) -> list[dict]:
    """Opções que podem citar lei: as da cena, as dos incidentes de audiência e as das partes da sentença."""
    out = list(cena.get("opcoes", []))
    for ln in cena.get("linhas", []):
        out += (ln.get("incidente") or {}).get("opcoes", [])
    for pt in cena.get("partes", []):
        out += pt.get("opcoes", [])
    for m in cena.get("ministros", []):
        out += m.get("argumentos", [])
    return out


def _lista(v) -> list:
    return [] if v is None else (list(v) if isinstance(v, (list, tuple)) else [v])


def _provas_exigidas(c: dict) -> set[str]:
    """Provas que a cena exige do jogador (apresentar, contradições, pares de acareação)."""
    out = set(c.get("provas", [])) if c.get("tipo") == "apresentar" else set()
    for ct in contradicoes_of(c):
        out |= set(ct.get("provas", []))
    for pr in c.get("pares", []):
        out |= set(_lista(pr.get("prova")))
    for pt in c.get("partes", []):
        out |= set(pt.get("provas", []))
    return out


def _validar_depoimento(c: dict, where: str, ep: dict, provas: dict, errs: list[str], received: set[str]) -> None:
    af = c.get("afirmacoes", [])
    cts = contradicoes_of(c)
    ver = c.get("veracidade")
    if c.get("testemunha") not in ep.get("posicoes", {}):
        errs.append(f"{where}: testemunha sem posição")
    if ver is not None and not isinstance(ver, dict):
        errs.append(f"{where}: 'veracidade' deve ser um objeto")
        ver = None
    veraz = bool(ver) and ver.get("mente") is False
    if "contradicao" in c and "contradicoes" in c:
        errs.append(f"{where}: use 'contradicao' ou 'contradicoes', não os dois")
    if not cts and not veraz:
        errs.append(f"{where}: depoimento sem contradição (só testemunha veraz, veracidade.mente=false, pode não ter)")
    if veraz and cts:
        errs.append(f"{where}: testemunha veraz não pode ter contradições (apresentar prova a ela custa credibilidade)")
    vistas = set()
    for ct in cts:
        if not 0 <= ct.get("afirmacao", -1) < len(af):
            errs.append(f"{where}: contradição aponta para afirmação inexistente")
        elif ct["afirmacao"] in vistas:
            errs.append(f"{where}: duas contradições na mesma afirmação {ct['afirmacao']}")
        vistas.add(ct.get("afirmacao"))
        for pid in ct.get("provas", []):
            if pid not in provas:
                errs.append(f"{where}: contradição usa prova inexistente {pid}")
        if not ct.get("provas"):
            errs.append(f"{where}: contradição sem prova")
        elif all(provas.get(pid, {}).get("autentica") is False for pid in ct["provas"]):
            errs.append(f"{where}: contradição só aceita provas falsas (não há caminho sem prova falsa)")
    if "exige" in c and not (isinstance(c["exige"], int) and 1 <= c["exige"] <= max(1, len(cts))):
        errs.append(f"{where}: 'exige' deve estar entre 1 e o número de contradições")
    if ver:
        if not isinstance(ver.get("mente"), bool):
            errs.append(f"{where}: veracidade.mente deve ser true ou false")
        sinais = ver.get("sinais", [])
        if veraz and sinais:
            errs.append(f"{where}: testemunha veraz não tem sinais de falsidade")
        if ver.get("mente") and not sinais:
            errs.append(f"{where}: testemunha que mente precisa de ao menos um sinal em veracidade.sinais")
        total, usados = 0, set()
        for sg in sinais:
            if not 0 <= sg.get("afirmacao", -1) < len(af):
                errs.append(f"{where}: sinal aponta para afirmação inexistente")
            elif sg["afirmacao"] in usados:
                errs.append(f"{where}: dois sinais na mesma afirmação {sg['afirmacao']}")
            usados.add(sg.get("afirmacao"))
            if not sg.get("tipo"):
                errs.append(f"{where}: sinal sem 'tipo'")
            if not isinstance(sg.get("pressao"), int) or not 1 <= sg["pressao"] <= 5:
                errs.append(f"{where}: sinal precisa de 'pressao' inteira entre 1 e 5")
            else:
                total += sg["pressao"]
        escala = ver.get("escala", total)
        if sinais and (not isinstance(escala, int) or escala < total or escala > 8):
            errs.append(f"{where}: veracidade.escala deve ser inteiro, ao menos a soma das pressões ({total}) e no máximo 8")
    h = c.get("hostil")
    if h is not None:
        if not isinstance(h, dict):
            errs.append(f"{where}: 'hostil' deve ser um objeto")
        else:
            if not 0 <= h.get("muda_versao", -1) < len(af):
                errs.append(f"{where}: hostil.muda_versao aponta para afirmação inexistente")
            if h.get("revela") not in provas:
                errs.append(f"{where}: hostil.revela usa prova inexistente {h.get('revela')!r}")
            else:
                received.add(h["revela"])
            if "dano" in h and not (isinstance(h["dano"], int) and 0 <= h["dano"] <= 2):
                errs.append(f"{where}: hostil.dano deve ser 0, 1 ou 2")
            if h.get("se", "pressao_antes_de_prova") not in ("pressao_antes_de_prova", "sempre"):
                errs.append(f"{where}: hostil.se deve ser 'pressao_antes_de_prova' ou 'sempre'")
            if not h.get("versao"):
                errs.append(f"{where}: hostil precisa de 'versao' (falas da nova versão)")
            if veraz:
                errs.append(f"{where}: testemunha hostil não pode ser veraz")


def _validar_analisar(c: dict, where: str, provas: dict, errs: list[str]) -> None:
    ps, fs = c.get("provas", []), c.get("falsas", [])
    if not ps or any(p not in provas for p in ps):
        errs.append(f"{where}: analisar usa prova inexistente ou lista vazia")
        return
    if len(ps) < 2:
        errs.append(f"{where}: analisar precisa de 2+ provas (ao menos uma autêntica)")
    if not fs or any(f not in ps for f in fs):
        errs.append(f"{where}: 'falsas' deve ser uma lista não vazia de provas que estão em 'provas'")
    for pid in ps:
        if (provas[pid].get("autentica") is False) != (pid in fs):
            errs.append(f"{where}: {pid} deve ter autentica: false se e somente se estiver em 'falsas'")
    if not c.get("acerto") or not c.get("erro"):
        errs.append(f"{where}: analisar precisa de 'acerto' e 'erro'")


def _validar_convocar(c: dict, where: str, cenas: dict, provas: dict, errs: list[str], received: set[str]) -> None:
    ops = c.get("opcoes", [])
    lim = c.get("limite")
    if not c.get("pergunta"):
        errs.append(f"{where}: convocar sem pergunta")
    if len(ops) < 2:
        errs.append(f"{where}: convocar precisa de 2+ testemunhas")
    if not isinstance(lim, int) or not 1 <= lim <= max(1, len(ops)):
        errs.append(f"{where}: 'limite' deve ser inteiro entre 1 e o número de opções")
        lim = 1
    if "minimo" in c and not (isinstance(c["minimo"], int) and 0 <= c["minimo"] <= lim):
        errs.append(f"{where}: 'minimo' deve estar entre 0 e o limite")
    usadas = set()
    for i, o in enumerate(ops):
        w = f"{where}#{i}"
        d = cenas.get(o.get("depoimento"))
        if not o.get("rotulo"):
            errs.append(f"{w}: opção sem rótulo")
        if o.get("perfil") not in PERFIS:
            errs.append(f"{w}: perfil deve ser um de {sorted(PERFIS)}")
        if "risco" in o and o["risco"] not in RISCOS:
            errs.append(f"{w}: risco deve ser um de {sorted(RISCOS)}")
        if d is None or d.get("tipo") != "depoimento":
            errs.append(f"{w}: 'depoimento' deve ser o id de uma cena de depoimento ({o.get('depoimento')!r})")
            continue
        if o["depoimento"] in usadas:
            errs.append(f"{w}: o mesmo depoimento em duas opções")
        usadas.add(o["depoimento"])
        ver = d.get("veracidade") or {}
        perfil = o.get("perfil")
        if perfil == "verdadeira" and ver.get("mente") is not False:
            errs.append(f"{w}: perfil verdadeira exige veracidade.mente=false no depoimento")
        if perfil == "mentirosa" and (ver.get("mente") is False or not contradicoes_of(d) or d.get("hostil")):
            errs.append(f"{w}: perfil mentirosa exige depoimento com contradições, sem hostil e sem mente=false")
        if perfil == "hostil" and not d.get("hostil"):
            errs.append(f"{w}: perfil hostil exige 'hostil' no depoimento")
        ef = o.get("efeito") or {}
        if not isinstance(ef, dict) or set(ef) - {"cred", "marca", "prova"}:
            errs.append(f"{w}: efeito aceita apenas cred, marca e prova")
            ef = {}
        if "cred" in ef and not (isinstance(ef["cred"], int) and -3 <= ef["cred"] <= 1):
            errs.append(f"{w}: efeito.cred deve ser inteiro entre -3 e 1")
        if "marca" in ef and not MARCA_RE.match(str(ef["marca"])):
            errs.append(f"{w}: marca inválida {ef['marca']!r} (a-z, 0-9 e _)")
        if "prova" in ef:
            if ef["prova"] not in provas:
                errs.append(f"{w}: efeito.prova inexistente {ef['prova']!r}")
            else:
                received.add(ef["prova"])


def _validar_novas(c: dict, where: str, provas: dict, normas: dict, errs: list[str], received: set[str]) -> None:
    t, ops = c["tipo"], c.get("opcoes", [])
    if t == "reviravolta":
        if "ajuste" in c and not (isinstance(c["ajuste"], int) and -3 <= c["ajuste"] <= 0):
            errs.append(f"{where}: 'ajuste' deve ser inteiro entre -3 e 0")
        if "piso" in c and not (isinstance(c["piso"], int) and 1 <= c["piso"] <= 5):
            errs.append(f"{where}: 'piso' deve ser inteiro entre 1 e 5")
        if not c.get("falas"):
            errs.append(f"{where}: reviravolta sem falas")
        return
    if not c.get("pergunta"):
        errs.append(f"{where}: {t} sem pergunta")
    if t in ("argumento", "intuicao"):
        n_ok = sum(1 for o in ops if o.get("certa"))
        if n_ok != 1 or len(ops) < (3 if t == "argumento" else 2):
            errs.append(f"{where}: {t} precisa de {'3+' if t == 'argumento' else '2+'} opções e exatamente 1 certa")
    for o in ops:
        if not o.get("t"):
            errs.append(f"{where}: opção sem texto 't'")
    if t == "argumento":
        for o in ops:
            alias = str(o.get("dispositivo", "")).split("#", 1)[0]
            if not o.get("dispositivo") or "#" not in o["dispositivo"] or alias not in normas:
                errs.append(f"{where}: opção sem 'dispositivo' válido (alias#trecho com alias do catálogo): {o.get('dispositivo')!r}")
        if not c.get("acerto"):
            errs.append(f"{where}: argumento precisa de 'acerto'")
    if t == "intuicao":
        if not c.get("revelacao") or not c.get("acerto") or not c.get("erro"):
            errs.append(f"{where}: intuicao precisa de 'revelacao', 'acerto' e 'erro'")
        if "bonus" in c and not (isinstance(c["bonus"], int) and 0 <= c["bonus"] <= 2):
            errs.append(f"{where}: 'bonus' deve ser 0, 1 ou 2")
        for o in ops:
            if "marca" in o and not MARCA_RE.match(str(o["marca"])):
                errs.append(f"{where}: marca inválida {o['marca']!r}")
    if t == "blefe":
        if len(ops) < 2 or all(o.get("blefe") for o in ops):
            errs.append(f"{where}: blefe precisa de 2+ opções e ao menos uma honesta (sem 'blefe')")
        if not any(o.get("blefe") for o in ops):
            errs.append(f"{where}: blefe precisa de ao menos uma opção com 'blefe'")
        for o in ops:
            b = o.get("blefe")
            if b is None:
                continue
            if not isinstance(b, dict) or b.get("resultado") not in ("funciona", "descoberto"):
                errs.append(f"{where}: blefe.resultado deve ser 'funciona' ou 'descoberto'")
                continue
            if not b.get("falas"):
                errs.append(f"{where}: blefe sem 'falas'")
            if b["resultado"] == "descoberto":
                if not b.get("consequencia"):
                    errs.append(f"{where}: blefe descoberto precisa de 'consequencia' (a consequência ética)")
                if "cred" in b and not (isinstance(b["cred"], int) and -3 <= b["cred"] <= -1):
                    errs.append(f"{where}: blefe.cred deve ser inteiro entre -3 e -1")
            elif "cred" in b:
                errs.append(f"{where}: blefe.cred só vale em blefe descoberto")
            if "prova" in b:
                if b["prova"] not in provas:
                    errs.append(f"{where}: blefe.prova inexistente {b['prova']!r}")
                else:
                    received.add(b["prova"])


def _uma_certa(ops: list, where: str, errs: list[str], minimo: int = 2) -> None:
    if len(ops) < minimo or sum(1 for o in ops if o.get("certa")) != 1 or any(not o.get("t") for o in ops):
        errs.append(f"{where}: precisa de {minimo}+ opções com texto e exatamente 1 certa")


def _validar_juiz(c: dict, where: str, ep: dict, errs: list[str]) -> None:
    """Mecânicas próprias de cada papel: audiencia, palavra e sentenca (juiz), protesto (partes), denuncia (promotor)
    e plenario (STF)."""
    pos = ep.get("posicoes", {})
    papeis = {"audiencia": ("juiz",), "palavra": ("juiz",), "sentenca": ("juiz",), "protesto": ("advogado", "promotor", "investigado"),
              "denuncia": ("promotor",),
              "plenario": ("advogado", "promotor") if c.get("colegiado") == "juri" else ("advogado", "juiz", "investigado")}[c["tipo"]]
    if ep.get("papel") not in papeis:
        errs.append(f"{where}: {c['tipo']} só existe em episódio de {' ou '.join(papeis)}")
    if c["tipo"] == "plenario":
        juri = c.get("colegiado") == "juri"
        if c.get("colegiado", "stf") not in ("stf", "juri"):
            errs.append(f"{where}: colegiado deve ser 'stf' ou 'juri'")
        mins, total = c.get("ministros", []), c.get("total", 7 if juri else 11)
        fix = c.get("votos_fixos", {"favor": 0, "contra": 0})
        maioria = c.get("maioria", total // 2 + 1)
        if not mins:
            errs.append(f"{where}: plenário sem ministros")
        if fix.get("favor", 0) + fix.get("contra", 0) + len(mins) != total:
            errs.append(f"{where}: votos fixos + ministros jogáveis devem somar {total}")
        if fix.get("favor", 0) + len(mins) < maioria:
            errs.append(f"{where}: a maioria ({maioria}) é inalcançável")
        for k, m in enumerate(mins):
            if (m.get("q") not in pos and not (juri and m.get("rotulo"))) or not m.get("preocupacao"):
                errs.append(f"{where}/ministro {k}: precisa de 'q' com posição e 'preocupacao'")
            if m.get("voto", "indeciso") not in ("indeciso", "contra"):
                errs.append(f"{where}/ministro {k}: voto inicial deve ser 'indeciso' ou 'contra'")
            _uma_certa(m.get("argumentos", []), f"{where}/ministro {k}", errs)
        if not c.get("acerto"):
            errs.append(f"{where}: plenário precisa de 'acerto'")
        return
    if c["tipo"] in ("audiencia", "protesto"):
        linhas = c.get("linhas", [])
        incs = [ln for ln in linhas if ln.get("incidente")]
        if any(ln.get("se") and ln.get("incidente") for ln in linhas):
            errs.append(f"{where}: incidente não pode depender de marca ('se'): o jogador poderia nunca vê-lo")
        if not incs or len(incs) == len(linhas):
            errs.append(f"{where}: audiência precisa de falas regulares e de ao menos um incidente")
        for k, ln in enumerate(linhas):
            if ln.get("q") not in pos or ln.get("q") == "voce":
                errs.append(f"{where}/linha {k}: orador precisa ter posição no episódio (e não ser o juiz)")
            inc = ln.get("incidente")
            if inc is not None:
                if not isinstance(inc, dict):
                    errs.append(f"{where}/linha {k}: incidente inválido")
                    continue
                _uma_certa(inc.get("opcoes", []), f"{where}/linha {k}", errs)
                if not (inc.get("fundamentos") or any(o.get("fundamentos") for o in inc.get("opcoes", []) if o.get("certa"))):
                    errs.append(f"{where}/linha {k}: incidente sem fundamento legal")
    elif c["tipo"] == "palavra":
        ors, passo = c.get("oradores", []), c.get("passo", 5)
        if len(ors) < 2:
            errs.append(f"{where}: palavra precisa de 2+ oradores")
        for k, o in enumerate(ors):
            lo, hi = o.get("min_ok", o.get("tempo")), o.get("max_ok", o.get("tempo"))
            if o.get("q") not in pos or not o.get("papel"):
                errs.append(f"{where}/orador {k}: precisa de 'q' com posição e 'papel'")
            if not all(isinstance(x, int) and x >= 0 and x % passo == 0 for x in (lo, hi)) or lo > hi:
                errs.append(f"{where}/orador {k}: 'tempo' (ou min_ok/max_ok) em minutos múltiplos de {passo}")
        if not c.get("acerto") or not c.get("erro") or not c.get("fundamentos"):
            errs.append(f"{where}: palavra precisa de 'acerto', 'erro' e 'fundamentos'")
    else:
        partes = c.get("partes", [])
        if len(partes) < 2:
            errs.append(f"{where}: {c['tipo']} precisa de 2+ partes")
        for k, pt in enumerate(partes):
            if not pt.get("nome"):
                errs.append(f"{where}/parte {k}: sem nome")
            if "provas" in pt:
                if c["tipo"] != "denuncia" or not pt["provas"] or "opcoes" in pt:
                    errs.append(f"{where}/parte {k}: parte com 'provas' só na denúncia, sem 'opcoes'")
                if not pt.get("erro"):
                    errs.append(f"{where}/parte {k}: parte com 'provas' precisa de 'erro'")
            else:
                _uma_certa(pt.get("opcoes", []), f"{where}/parte {k}", errs)
        if not c.get("acerto"):
            errs.append(f"{where}: {c['tipo']} precisa de 'acerto'")


def _validar_fora(c: dict, where: str, errs: list[str]) -> None:
    """tensao e celular: cenas fora do tribunal, sem resposta certa; cada opção tem consequência."""
    ops = c.get("opcoes", [])
    if c["tipo"] == "tensao":
        if not c.get("pergunta") or len(ops) < 2:
            errs.append(f"{where}: tensão precisa de pergunta e 2+ opções")
        if not (isinstance(c.get("tempo", 8), int) and 3 <= c.get("tempo", 8) <= 20):
            errs.append(f"{where}: 'tempo' da tensão deve ser inteiro entre 3 e 20 segundos")
        if "padrao" in c and not (isinstance(c["padrao"], int) and 0 <= c["padrao"] < len(ops)):
            errs.append(f"{where}: 'padrao' deve ser o índice de uma opção")
    else:
        msgs = c.get("mensagens", [])
        if not msgs or any(not m.get("t") or m.get("de", "ele") not in ("ele", "voce") for m in msgs):
            errs.append(f"{where}: celular precisa de mensagens com 't' e 'de' ('ele' ou 'voce')")
    for o in ops:
        if not o.get("t"):
            errs.append(f"{where}: opção sem texto 't'")
        if "cred" in o and not (isinstance(o["cred"], int) and -2 <= o["cred"] <= 1):
            errs.append(f"{where}: 'cred' da opção deve ser inteiro entre -2 e 1")
        if "certa" in o:
            errs.append(f"{where}: {c['tipo']} não tem opção 'certa' (cada escolha tem consequência)")
        if "marca" in o and not MARCA_RE.match(str(o["marca"])):
            errs.append(f"{where}: marca inválida {o['marca']!r}")
        for m in o.get("retorno", []):
            if not m.get("t"):
                errs.append(f"{where}: retorno sem texto")


def _validar_acareacao(c: dict, where: str, cenas: dict, provas: dict, errs: list[str]) -> None:
    ds = []
    for k in ("a", "b"):
        d = cenas.get(c.get(k))
        if d is None or d.get("tipo") != "depoimento":
            errs.append(f"{where}: '{k}' deve ser o id de uma cena de depoimento ({c.get(k)!r})")
        ds.append(d)
    if c.get("a") and c.get("a") == c.get("b"):
        errs.append(f"{where}: acareação precisa de dois depoimentos diferentes")
    if not c.get("pares"):
        errs.append(f"{where}: acareação sem pares")
    for i, pr in enumerate(c.get("pares", [])):
        w = f"{where}#{i}"
        for k, d in zip(("a", "b"), ds):
            if d is not None and not 0 <= pr.get(k, -1) < len(d.get("afirmacoes", [])):
                errs.append(f"{w}: '{k}' aponta para afirmação inexistente")
        ids = _lista(pr.get("prova"))
        if not ids or any(p not in provas for p in ids):
            errs.append(f"{w}: par com prova inexistente ou ausente")
        elif all(provas[p].get("autentica") is False for p in ids):
            errs.append(f"{w}: par só aceita provas falsas (não há caminho sem prova falsa)")
    if not c.get("acerto") or not c.get("erro"):
        errs.append(f"{where}: acareação precisa de 'acerto' e 'erro'")


def _ganho_opcao(cenas: dict, o: dict) -> set[str]:
    d = cenas.get(o.get("depoimento")) or {}
    g = {x for f in _falas(d) for x in f.get("recebe", [])}
    g |= {x for x in [(o.get("efeito") or {}).get("prova")] if x}
    if d.get("hostil", {}).get("revela"):
        g.add(d["hostil"]["revela"])
    return g | {x for f in o.get("falas", []) for x in f.get("recebe", [])}


def _cobertura_convocar(eid: str, ep: dict, cenas: dict, subs: set[str]) -> list[str]:
    """Para cada 'convocar': existe um conjunto de até 'limite' testemunhas que entrega as provas que só elas dão
    e que o resto do caso exige? (a 'soma possível de contradições' alcança as provas necessárias)."""
    from itertools import combinations
    errs: list[str] = []
    principal = {sid: c for sid, c in cenas.items() if sid not in subs}
    base = {x for c in principal.values() if c.get("tipo") != "convocar" for f in _falas(c) for x in f.get("recebe", [])}
    for c in principal.values():
        if c.get("tipo") == "convocar":
            for o in c.get("opcoes", []):
                if not isinstance(o, dict):
                    continue
                base -= set()  # provas de opções não entram na base
    exigidas = {pid for c in principal.values() for pid in _provas_exigidas(c)}
    for sid, c in principal.items():
        if c.get("tipo") != "convocar":
            continue
        ops = [o for o in c.get("opcoes", []) if isinstance(o, dict) and o.get("depoimento") in cenas]
        lim = c.get("limite")
        if not isinstance(lim, int) or not ops:
            continue
        lim = min(lim, len(ops))
        ok = False
        for combo in combinations(ops, lim):
            obtido = set(base)
            for o in combo:
                obtido |= _ganho_opcao(cenas, o)
            falta = set(exigidas) - obtido
            for o in combo:
                falta |= _provas_exigidas(cenas[o["depoimento"]]) - obtido
            if not falta:
                ok = True
                break
        if not ok:
            errs.append(f"{eid}/{sid}: nenhuma combinação de {lim} testemunha(s) entrega as provas que o caso exige")
    return errs


def validate(data: dict, normas: dict[str, str]) -> list[str]:
    errs: list[str] = []
    chars = data["personagens"]
    seen_ids = set()
    atos = {a["id"] for a in data.get("atos", [])}
    ordens: set[tuple] = set()
    all_marcas = {m for e in data["episodios"] for m in episode_marks(e)} | set(data.get("marcas_declaradas", ()))
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
        if ep.get("papel") not in ("advogado", "promotor", "juiz", "investigado"):
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
            if "autentica" in p and not isinstance(p["autentica"], bool):
                errs.append(f"{eid}/{p['id']}: 'autentica' deve ser true ou false")
            if p.get("autentica") is False:
                if p["tipo"] != "prova":
                    errs.append(f"{eid}/{p['id']}: só uma prova (não uma lei) pode ser falsa")
                ind = p.get("indicios")
                if not isinstance(ind, list) or not ind or not all(isinstance(i, str) and i.strip() for i in ind):
                    errs.append(f"{eid}/{p['id']}: prova falsa precisa de 'indicios' (lista de textos)")
            elif "indicios" in p:
                errs.append(f"{eid}/{p['id']}: 'indicios' só em prova com autentica: false")
        for who, pos in ep.get("posicoes", {}).items():
            if who not in chars:
                errs.append(f"{eid}: posição para personagem desconhecido {who}")
            if pos not in POSICOES:
                errs.append(f"{eid}: posição inválida {pos}")
        cenas = ep["cenas"]
        if ep.get("inicio") not in cenas:
            errs.append(f"{eid}: cena inicial inexistente")
            continue
        subs = sub_scenes(cenas)
        falsas_ep = {pid for pid, p in provas.items() if p.get("autentica") is False}
        received: set[str] = set()
        for sid, c in cenas.items():
            where = f"{eid}/{sid}"
            if c.get("tipo") not in SCENE_TYPES:
                errs.append(f"{where}: tipo de cena inválido {c.get('tipo')!r}")
                continue
            if c.get("local") and c["local"] not in LOCAIS:
                errs.append(f"{where}: local inválido {c['local']}")
            if c["tipo"] != "veredicto" and sid not in subs and c.get("proxima") not in cenas:
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
                _validar_depoimento(c, where, ep, provas, errs, received)
            if c["tipo"] == "analisar":
                _validar_analisar(c, where, provas, errs)
            if c["tipo"] == "convocar":
                _validar_convocar(c, where, cenas, provas, errs, received)
            if c["tipo"] == "acareacao":
                _validar_acareacao(c, where, cenas, provas, errs)
            if c["tipo"] in ("argumento", "intuicao", "blefe", "reviravolta"):
                _validar_novas(c, where, provas, normas, errs, received)
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
                elif all(p in falsas_ep for p in c["provas"]):
                    errs.append(f"{where}: todas as provas aceitas são falsas (não há caminho sem prova falsa)")
            if c["tipo"] == "escolha" and c.get("livre"):
                # dilema: todas as opções valem, cada uma pode deixar uma marca na carreira
                if len(c.get("opcoes", [])) < 2 or any(o.get("certa") for o in c["opcoes"]):
                    errs.append(f"{where}: escolha livre precisa de 2+ opções e nenhuma 'certa'")
            elif c["tipo"] == "escolha":
                n_ok = sum(1 for o in c.get("opcoes", []) if o.get("certa"))
                if n_ok != 1 or len(c.get("opcoes", [])) < 2:
                    errs.append(f"{where}: escolha precisa de 2+ opções e exatamente 1 certa")
            for o in c.get("opcoes", []):
                if "marca" in o and c["tipo"] not in ("intuicao", "tensao", "celular") and (not c.get("livre") or not MARCA_RE.match(str(o["marca"]))):
                    errs.append(f"{where}: marca inválida {o['marca']!r} (só em escolha livre; a-z, 0-9 e _)")
            conds = [f.get("se") for f in _falas(c)] + [v.get("se") for v in c.get("variantes", [])]
            for cond in filter(None, conds):
                if cond.lstrip("!") not in all_marcas and cond.lstrip("!") not in MARCAS_AUTOMATICAS:
                    errs.append(f"{where}: condição usa marca que nenhuma escolha cria {cond!r}")
            for v in c.get("variantes", []):
                if not v.get("se") or not any(v.get(k) for k in ("carimbo", "titulo", "texto")):
                    errs.append(f"{where}: variante de veredicto precisa de 'se' e de carimbo/título/texto")
            if "dica" in c:
                dicas = c["dica"] if isinstance(c["dica"], list) else [c["dica"]]
                if c["tipo"] not in INTERACTIVE - {"investigar", "convocar", "intuicao", "blefe", "reviravolta"} or not 1 <= len(dicas) <= 2                         or not all(isinstance(d, str) and d.strip() for d in dicas):
                    errs.append(f"{where}: 'dica' deve ser texto (ou [vaga, específica]) em cena com erro possível")
            if "tempo" in c and c["tipo"] != "tensao" and (c["tipo"] not in ("decidir", "escolha", "argumento") or c.get("livre")
                                 or not (isinstance(c["tempo"], int) and 10 <= c["tempo"] <= 120)):
                errs.append(f"{where}: 'tempo' (relógio) só em decidir/escolha/argumento, inteiro de 10 a 120 s")
            if c["tipo"] == "decidir" and c.get("correta") not in ("deferir", "indeferir"):
                errs.append(f"{where}: decisão correta deve ser deferir ou indeferir")
            if c["tipo"] in ("audiencia", "palavra", "sentenca", "protesto", "denuncia", "plenario"):
                _validar_juiz(c, where, ep, errs)
            if c["tipo"] in ("tensao", "celular"):
                _validar_fora(c, where, errs)
            incs = [ln["incidente"] for ln in c.get("linhas", []) if isinstance(ln.get("incidente"), dict)]
            for f in c.get("fundamentos", []) + [f for i in incs for f in i.get("fundamentos", [])] \
                    + [f for o in _opcoes_com_fundamento(c) for f in o.get("fundamentos", [])]:
                alias = f.get("chave", "").split("#", 1)[0]
                if alias not in normas:
                    errs.append(f"{where}: alias de norma desconhecido {alias!r}")
        for p in ep["provas"]:
            if p["tipo"] == "lei" and p["chave"].split("#", 1)[0] not in normas:
                errs.append(f"{eid}/{p['id']}: alias de norma desconhecido")
        # provas exigidas precisam ter sido entregues em algum momento
        needed = {pid for c in cenas.values() for pid in _provas_exigidas(c)}
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
            if cenas[s].get("tipo") == "convocar":
                stack += [o.get("depoimento") for o in cenas[s].get("opcoes", [])]
            elif cenas[s].get("tipo") == "acareacao":
                stack += [cenas[s].get("a"), cenas[s].get("b")]
        errs += _cobertura_convocar(eid, ep, cenas, subs)
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
            if o.get("dispositivo") and "fundamentos" not in o:
                o["fundamentos"] = [{"chave": o["dispositivo"], "trecho": o.get("trecho", "")}]
            if "fundamentos" in o:
                o["fundamentos"] = [enrich(f) for f in o["fundamentos"]]
        for ln in c.get("linhas", []):
            inc = ln.get("incidente") or {}
            if "fundamentos" in inc:
                inc["fundamentos"] = [enrich(f) for f in inc["fundamentos"]]
        for o in [o for ln in c.get("linhas", []) for o in (ln.get("incidente") or {}).get("opcoes", [])] \
                + [o for pt in c.get("partes", []) for o in pt.get("opcoes", [])] \
                + [a for m in c.get("ministros", []) for a in m.get("argumentos", [])]:
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
