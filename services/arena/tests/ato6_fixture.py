"""Episódio-fixture mínimo que exercita TODAS as mecânicas do Ato 6 (validador e, via JSON, o navegador)."""

import json
import sys


def F(q, t, **kw):
    return {"q": q, "t": t, **kw}


def episode() -> dict:
    prova = lambda i, n, **kw: {"id": i, "tipo": "prova", "icone": "📄", "nome": n, "descricao": "Descrição de " + n, **kw}
    dep = lambda who, afs, **kw: {"tipo": "depoimento", "local": "tribunal", "testemunha": who, "titulo": "Depoimento de " + who,
                                  "intro": [F("lacerda", "Chamo a testemunha.")],
                                  "afirmacoes": [{"t": t, "e": "normal", "pressionar": [F("voce", "Pressiono: " + t[:20])]} for t in afs],
                                  "erro": [F("beatriz", "Não procede.")], "acerto": [F("beatriz", "Anotado.")], "proxima": "fim", **kw}
    cenas = {
        "ini": {"tipo": "dialogo", "local": "tribunal", "proxima": "analise", "falas": [
            F("beatriz", "Audiência aberta.", recebe=["real", "pen", "grav", "laudo"])]},
        "analise": {"tipo": "analisar", "local": "escritorio", "pergunta": "Quais provas não resistem?", "provas": ["real", "pen"],
                    "falsas": ["pen"], "dica": ["Veja as datas.", "A pen drive foi copiada."], "falas": [F("voce", "Vou examinar tudo.")],
                    "acerto": [F("voce", "A pen drive é falsa.")], "erro": [F("voce", "Errei na perícia.")], "proxima": "conv"},
        "conv": {"tipo": "convocar", "pergunta": "Quem você chama?", "limite": 2, "minimo": 1, "falas": [F("beatriz", "A defesa pode convocar.")],
                 "opcoes": [
                     {"rotulo": "Chamar Valdir", "perfil": "verdadeira", "risco": "baixo", "depoimento": "d_veraz", "falas": [F("voce", "Valdir.")],
                      "efeito": {"marca": "chamou_valdir", "prova": "laudo"}},
                     {"rotulo": "Chamar Jorge", "perfil": "mentirosa", "risco": "medio", "depoimento": "d_mente", "falas": [F("voce", "Jorge.")],
                      "efeito": {"cred": 1}},
                     {"rotulo": "Chamar Rafael", "perfil": "hostil", "risco": "alto", "depoimento": "d_hostil", "falas": [F("voce", "Rafael.")]}],
                 "proxima": "acar"},
        "d_veraz": dep("valdir", ["Vi tudo da cozinha.", "O rapaz pagou a conta."], veracidade={"mente": False}),
        "d_mente": dep("jorge", ["Não vi o vídeo.", "Estava no bar às 23h.", "Nunca vi o rapaz."],
                       contradicoes=[{"afirmacao": 1, "provas": ["grav"], "acerto": [F("voce", "A gravação o desmente!")]},
                                     {"afirmacao": 2, "provas": ["real"]}],
                       veracidade={"mente": True, "escala": 3, "revela": [F("narrador", "Está mentindo.")],
                                   "sinais": [{"afirmacao": 0, "tipo": "evasiva", "pressao": 1}, {"afirmacao": 2, "tipo": "nervosismo", "pressao": 2}]}),
        "d_hostil": dep("rafael", ["O réu confessou.", "Vi a faca."], hostil={"muda_versao": 1, "revela": "laudo", "dano": 1,
                                                                            "versao": [F("rafael", "Na verdade vi a faca.")]},
                        contradicoes=[{"afirmacao": 0, "provas": ["real"]}]),
        "acar": {"tipo": "acareacao", "a": "d_mente", "b": "d_hostil", "falas": [F("beatriz", "Acareação.")],
                 "pares": [{"a": 1, "b": 0, "prova": "real", "falas": [F("voce", "As versões não batem.")]}],
                 "acerto": [F("beatriz", "Resolvido.")], "erro": [F("beatriz", "Não.")], "dica": "Compare os horários.", "proxima": "arg"},
        "arg": {"tipo": "argumento", "alvo": "A prova vale mesmo sem mandado.", "pergunta": "Qual dispositivo derruba isso?",
                "falas": [F("lacerda", "A prova vale.")],
                "opcoes": [{"t": "Art. 157 do CPP", "dispositivo": "CPP#art-157", "certa": True, "falas": [F("voce", "Ilícita!")]},
                           {"t": "Art. 155 do CPP", "dispositivo": "CPP#art-155", "falas": [F("beatriz", "Não é isso.")]},
                           {"t": "Art. 212 do CPP", "dispositivo": "CPP#art-212", "falas": [F("beatriz", "Também não.")]}],
                "acerto": [F("beatriz", "Acolho.")], "proxima": "intu"},
        "intu": {"tipo": "intuicao", "pergunta": "A testemunha mente?", "pistas": ["Olhou para o chão."], "falas": [F("voce", "Hum.")],
                 "opcoes": [{"t": "Sim", "certa": True, "marca": "confiou_no_faro"}, {"t": "Não"}],
                 "revelacao": [F("narrador", "Mentia.")], "acerto": [F("voce", "Acertei.")], "erro": [F("voce", "Errei.")], "bonus": 1, "proxima": "blefe"},
        "blefe": {"tipo": "blefe", "pergunta": "Blefar?", "falas": [F("voce", "Tenho uma carta na manga.")],
                  "opcoes": [{"t": "Blefar: tenho a gravação", "blefe": {"resultado": "descoberto", "falas": [F("lacerda", "Cadê a gravação?")],
                                                                         "consequencia": [F("beatriz", "Estatuto da OAB, art. 34.")], "cred": -2}},
                             {"t": "Só o que posso provar", "falas": [F("voce", "Sigo com o que tenho.")]}],
                  "proxima": "rev"},
        "rev": {"tipo": "reviravolta", "banner": "REVIRAVOLTA!", "sub": "Testemunha surpresa", "ajuste": -1, "piso": 2,
                "falas": [F("lacerda", "Nova testemunha!")], "proxima": "d_surp"},
        "d_surp": dep("valdir", ["Vi o réu."], contradicao={"afirmacao": 0, "provas": ["real"]}, proxima="fim"),
        "fim": {"tipo": "veredicto", "carimbo": "ABSOLVIDO", "titulo": "Fim", "texto": "Teste concluído."},
    }
    cenas["d_surp"]["proxima"] = "fim"
    return {
        "id": "t-ato6", "ato": "ato1", "ordem": 99, "numero": 99, "titulo": "Fixture do Ato 6", "papel": "advogado", "nivel": "basico",
        "sinopse": "teste", "inicio": "ini",
        "posicoes": {"voce": "defesa", "lacerda": "acusacao", "beatriz": "juiz", "valdir": "testemunha", "jorge": "testemunha",
                     "rafael": "testemunha"},
        "provas": [prova("real", "Vídeo real"), prova("pen", "Pen drive", autentica=False, indicios=["metadados de ontem", "assinatura copiada"]),
                   prova("grav", "Gravação", detalhe="Áudio íntegro."), prova("laudo", "Laudo")],
        "cenas": cenas,
    }


if __name__ == "__main__":
    json.dump(episode(), sys.stdout, ensure_ascii=False)
