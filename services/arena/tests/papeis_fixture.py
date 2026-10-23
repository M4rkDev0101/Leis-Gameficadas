"""Episódios-fixture mínimos com as mecânicas próprias de cada papel (validador e, via JSON, o navegador):
juiz (audiencia, palavra, sentenca), promotor (protesto, denuncia) e STF (plenario)."""

import json
import sys


def F(q, t, **kw):
    return {"q": q, "t": t, **kw}


FUND = lambda chave, trecho: [{"chave": chave, "trecho": trecho}]
prova = lambda i, n, **kw: {"id": i, "tipo": "prova", "icone": "📄", "nome": n, "descricao": "Descrição de " + n, **kw}
op = lambda t, certa=False, **kw: {"t": t, **({"certa": True} if certa else {}), "falas": [F("narrador", "Resposta: " + t)], **kw}


def juiz() -> dict:
    cenas = {
        "ini": {"tipo": "dialogo", "local": "tribunal", "proxima": "aud", "falas": [F("voce", "Declaro aberta a audiência.", fx="martelo")]},
        "aud": {"tipo": "audiencia", "local": "tribunal", "titulo": "Inquirição do cabo", "falas": [F("lacerda", "Chamo a testemunha.")],
                "linhas": [
                    F("lacerda", "Cabo, onde o senhor estava às 2h?"),
                    {**F("lacerda", "O réu entregou a senha por vontade própria, não foi?"),
                     "incidente": {"pergunta": "A pergunta é…", "fundamentos": FUND("CPP#art-212", "não admitindo o juiz aquelas que puderem induzir a resposta"),
                                   "opcoes": [op("Indefiro: pergunta indutiva. Reformule.", True), op("Deixo responder: o MP sabe o que faz.")]}},
                    F("valdir", "Abordei o réu perto do banco."),
                ], "acerto": [F("narrador", "A inquirição seguiu em ordem.")], "proxima": "pal"},
        "pal": {"tipo": "palavra", "titulo": "Alegações finais orais", "ordenar": True, "falas": [F("voce", "Encerrada a instrução.")],
                "oradores": [{"q": "lacerda", "papel": "Acusação (MP)", "tempo": 20}, {"q": "beatriz", "papel": "Defesa", "min_ok": 20, "max_ok": 30}],
                "fundamentos": FUND("CPP#art-403", "alegações finais orais por 20 (vinte) minutos"),
                "acerto": [F("voce", "Com a palavra o Ministério Público.")], "erro": [F("narrador", "Tempo ou ordem fora da lei.")], "proxima": "sent"},
        "sent": {"tipo": "sentenca", "titulo": "Sentença", "falas": [F("voce", "Passo a sentenciar.")],
                 "partes": [{"nome": "Fundamentação", "opcoes": [op("Valoro as provas do contraditório.", True, fundamentos=FUND("CPP#art-155", "livre apreciação da prova produzida em contraditório judicial")),
                                                                 op("Baseio-me só no inquérito.")]},
                            {"nome": "Dispositivo", "opcoes": [op("Absolvo por falta de provas.", True), op("Condeno por convicção íntima.")]}],
                 "acerto": [F("voce", "Publique-se.")], "proxima": "fim"},
        "fim": {"tipo": "veredicto", "carimbo": "SENTENÇA", "titulo": "Fim", "texto": "Teste concluído."},
    }
    return {"id": "t-juiz", "ato": "ato4", "ordem": 99, "numero": 99, "titulo": "Fixture do juiz", "papel": "juiz", "nivel": "basico",
            "sinopse": "teste", "inicio": "ini", "posicoes": {"voce": "juiz", "lacerda": "acusacao", "beatriz": "defesa", "valdir": "testemunha"},
            "provas": [prova("termo", "Termo")], "cenas": cenas}


def promotor() -> dict:
    cenas = {
        "ini": {"tipo": "dialogo", "local": "gabinete", "proxima": "den", "falas": [F("voce", "Chegou o inquérito.", recebe=["laudo", "video", "foto"])]},
        "den": {"tipo": "denuncia", "titulo": "Denúncia", "falas": [F("voce", "Vou denunciar.")],
                "partes": [{"nome": "Classificação do crime", "opcoes": [op("Furto qualificado (CP, art. 155, § 4º)", True, fundamentos=FUND("CP#art-155", "Subtrair, para si ou para outrem, coisa alheia móvel")),
                                                                        op("Roubo (CP, art. 157)")]},
                           {"nome": "Materialidade", "provas": ["laudo"], "erro": [F("narrador", "Essa peça não prova que o crime aconteceu.")]},
                           {"nome": "Autoria", "provas": ["video"], "erro": [F("narrador", "Essa peça não aponta quem foi.")]}],
                "acerto": [F("voce", "Ofereço a denúncia.")], "proxima": "prot"},
        "prot": {"tipo": "protesto", "titulo": "A defesa inquire a vítima", "falas": [F("beatriz", "Com a palavra a defesa.")],
                 "linhas": [F("beatriz", "A senhora trabalha onde?"),
                            {**F("beatriz", "A senhora costuma sair à noite com essas roupas?"),
                             "incidente": {"fundamentos": FUND("CPP#art-400a/inc-ii", "a utilização de linguagem, de informações ou de material que ofendam a dignidade da vítima ou de testemunhas"),
                                           "opcoes": [op("Ofende a dignidade da vítima e é alheia aos fatos.", True), op("Pergunta repetida.")]}}],
                 "acerto": [F("narrador", "A inquirição terminou.")], "proxima": "zap"},
        "zap": {"tipo": "celular", "contato": "Número desconhecido", "falas": [F("narrador", "O celular vibra.")],
                "mensagens": [{"de": "ele", "t": "Belo discurso hoje, doutor(a)."}, {"de": "ele", "t": "Sabemos onde você estaciona."}],
                "opcoes": [{"t": "Não responder e registrar ocorrência", "marca": "registrou_ameaca", "falas": [F("voce", "Vou à delegacia.")]},
                           {"t": "Responder: 'Quem é?'", "envia": "Quem é?", "retorno": [{"de": "ele", "t": "Um admirador."}], "cred": -1}],
                "depois": [F("narrador", "A noite fica longa.")], "proxima": "fuga"},
        "fuga": {"tipo": "tensao", "local": "rua", "tempo": 6, "padrao": 1, "pergunta": "Um carro escuro te segue há três quarteirões.",
                 "falas": [F("narrador", "Faróis no retrovisor.")],
                 "opcoes": [{"t": "Entrar no posto iluminado", "falas": [F("narrador", "O carro passa direto.")], "cred": 1},
                            {"t": "Acelerar para casa", "falas": [F("narrador", "O carro some, mas agora sabem seu caminho.")], "marca": "seguido_ate_casa"}],
                 "proxima": "juri"},
        "juri": {"tipo": "plenario", "colegiado": "juri", "titulo": "Conselho de Sentença", "votos_fixos": {"favor": 3, "contra": 2},
                 "falas": [F("lacerda", "Com a palavra a acusação.")],
                 "ministros": [{"rotulo": "Jurada 2", "preocupacao": "Franze a testa quando ouve falar do laudo.",
                                "argumentos": [op("Explico o laudo em linguagem simples.", True), op("Leio o laudo inteiro.")]},
                               {"rotulo": "Jurado 5", "voto": "contra", "preocupacao": "Olha para o réu com pena.",
                                "argumentos": [op("Lembro a vítima, sem atacar o réu.", True), op("Chamo o réu de monstro.")]}],
                 "acerto": [F("lacerda", "O Conselho votou.")], "proxima": "fim"},
        "fim": {"tipo": "veredicto", "carimbo": "DENUNCIADO", "titulo": "Fim", "texto": "Teste concluído."},
    }
    return {"id": "t-promotor", "ato": "ato3", "ordem": 99, "numero": 98, "titulo": "Fixture do promotor", "papel": "promotor", "nivel": "basico",
            "sinopse": "teste", "inicio": "ini", "posicoes": {"voce": "acusacao", "beatriz": "defesa", "lacerda": "juiz", "valdir": "testemunha"},
            "provas": [prova("laudo", "Laudo pericial"), prova("video", "Vídeo da loja"), prova("foto", "Foto falsa", autentica=False, indicios=["sombra errada"])],
            "cenas": cenas}


def supremo() -> dict:
    arg = lambda t, certa=False: {"t": t, **({"certa": True} if certa else {}), "falas": [F("narrador", "Ministro reage: " + t)]}
    cenas = {
        "ini": {"tipo": "dialogo", "local": "tribunal", "proxima": "plen", "falas": [F("voce", "Excelências, peço a palavra.")]},
        "plen": {"tipo": "plenario", "titulo": "Plenário", "votos_fixos": {"favor": 4, "contra": 5}, "falas": [F("lacerda", "Em votação.")],
                 "ministros": [{"q": "lacerda", "preocupacao": "E a segurança jurídica?", "falas": [F("lacerda", "Temo a insegurança.")],
                                "argumentos": [arg("Modular os efeitos (Lei 9.868, art. 27).", True), arg("Isso não importa.")]},
                               {"q": "beatriz", "preocupacao": "O STF é competente?", "voto": "contra", "falas": [F("beatriz", "Duvido da competência.")],
                                "argumentos": [arg("Há foro por prerrogativa (CF, art. 102, I, b).", True), arg("Competência é detalhe.")]}],
                 "acerto": [F("narrador", "Proclamado o resultado.")], "proxima": "fim"},
        "fim": {"tipo": "veredicto", "carimbo": "PROCEDENTE", "titulo": "Fim", "texto": "Teste concluído."},
    }
    return {"id": "t-stf", "ato": "ato6", "ordem": 99, "numero": 97, "titulo": "Fixture do STF", "papel": "advogado", "nivel": "basico",
            "sinopse": "teste", "inicio": "ini", "posicoes": {"voce": "defesa", "lacerda": "juiz", "beatriz": "juiz"}, "provas": [], "cenas": cenas}


def episodes() -> list[dict]:
    return [juiz(), promotor(), supremo()]


if __name__ == "__main__":
    json.dump(episodes(), sys.stdout, ensure_ascii=False)
