"""Regressões do parser estrutural. Cada caso reproduz um padrão encontrado no acervo real."""

import unittest

from vade_ingest import structure
from vade_ingest.structure import extract_notes, parse_body, roman_to_int


def arts(body: str):
    return {a.path: a for a in parse_body(body).articles()}


def find(body: str, path: str):
    for u in parse_body(body).root.walk():
        if u.path == path:
            return u
    raise KeyError(path)


CP_ROUBO = """# Decreto-Lei nº 2.848 de 07/12/1940

## PARTE ESPECIAL

### TÍTULO II — DOS CRIMES CONTRA O PATRIMÔNIO

#### CAPÍTULO II — DO ROUBO E DA EXTORSÃO

**Roubo**

**Art. 157.** Subtrair coisa móvel alheia, para si ou para outrem, mediante grave ameaça ou violência a pessoa:

Pena - reclusão, de 6 (seis) a 10 (dez) anos, e multa. *(Pena com redação dada pela Lei nº 15.397, de 30/4/2026)*

**§ 1º-A.** A pena é de reclusão, de 6 (seis) a 12 (doze) anos. *(Parágrafo acrescido pela Lei nº 15.181, de 28/7/2025)*

**§ 2º** A pena aumenta-se de 1/3 (um terço) até metade:

I - *(Revogado pela Lei nº 13.654, de 23/4/2018)*

II - se há o concurso de duas ou mais pessoas;

III - se a vítima está em serviço de transporte de valores:

a) suspensão das atividades;

e) *(VETADA na Lei nº 15.517, de 22/9/2026)*

**Art. 359-M-A.** Quando os delitos deste Capítulo estão inseridos no mesmo contexto.
"""


class TestArticles(unittest.TestCase):
    def test_article_tree_and_paths(self):
        a = arts(CP_ROUBO)["art-157"]
        self.assertEqual(a.rubrica, "Roubo")
        self.assertTrue(a.text.startswith("Subtrair coisa móvel"))
        self.assertEqual([c.path for c in a.children],
                         ["art-157/pena", "art-157/par-1a", "art-157/par-2"])

    def test_pena_with_note(self):
        pena = find(CP_ROUBO, "art-157/pena")
        self.assertEqual(pena.kind, "pena")
        self.assertEqual(pena.text, "reclusão, de 6 (seis) a 10 (dez) anos, e multa.")
        self.assertEqual(pena.notes[0].kind, "redacao")
        self.assertEqual(pena.notes[0].ref, "Lei nº 15.397, de 30/4/2026")

    def test_revoked_and_vetoed(self):
        inc1 = find(CP_ROUBO, "art-157/par-2/inc-i")
        self.assertTrue(inc1.revoked)
        self.assertEqual(inc1.text, "")
        ali_e = find(CP_ROUBO, "art-157/par-2/inc-iii/ali-e")
        self.assertTrue(ali_e.vetoed)
        self.assertFalse(find(CP_ROUBO, "art-157/par-2/inc-ii").revoked)

    def test_double_suffix_article(self):
        self.assertIn("art-359m-a", arts(CP_ROUBO))

    def test_spaced_hyphen_is_separator_not_suffix(self):
        # "I - Incapacidade" não pode virar inciso "I-I"; "Art. 242 - A lei" não é "242-A"
        body = "**Art. 129.** Ofender:\n\nI - Incapacidade para as ocupações;\n\nII - perigo de vida;\n\n**Art. 242** - A lei dispõe."
        p = arts(body)
        self.assertEqual([c.path for c in p["art-129"].children], ["art-129/inc-i", "art-129/inc-ii"])
        self.assertIn("art-242", p)
        self.assertEqual(p["art-242"].text, "A lei dispõe.")

    def test_inciso_with_suffix_without_dash(self):
        body = "**Art. 92.** São órgãos do Poder Judiciário:\n\nI - o Supremo Tribunal Federal;\n\nI-A o Conselho Nacional de Justiça;\n\nII - o Superior Tribunal de Justiça;"
        self.assertEqual([c.label for c in arts(body)["art-92"].children], ["I", "I-A", "II"])

    def test_bare_inciso_only_when_sequence_continues(self):
        body = ("**Art. 114.** Compete à Justiça do Trabalho:\n\nI - as ações oriundas;\n\n"
                "II as ações que envolvam exercício do direito de greve;\n\n"
                "V os conflitos de competência;")  # V fora de sequência: texto, não inciso
        a = arts(body)["art-114"]
        self.assertEqual([c.label for c in a.children], ["I", "II"])
        self.assertIn("V os conflitos", a.children[-1].text)

    def test_partial_bold_article(self):
        body = "**Art**. 1º Os Estados ficam autorizados.\n\n**§ 1º** A autorização não poderá ser exercida."
        p = arts(body)
        self.assertEqual(list(p), ["art-1"])
        self.assertEqual(p["art-1"].children[0].path, "art-1/par-1")

    def test_artigo_spelled_out_and_dash_separator(self):
        body = "ARTIGO 1º - O Art. 237 passa a ter a seguinte redação.\n\n**Art. 2º** – Esta lei entra em vigor."
        p = arts(body)
        self.assertEqual(list(p), ["art-1", "art-2"])
        self.assertEqual(p["art-2"].text, "Esta lei entra em vigor.")

    def test_thousand_separator_in_number(self):
        self.assertIn("art-1000", arts("**Art. 1.000.** O sócio."))

    def test_paragrafo_unico(self):
        u = find("**Art. 1º** A República.\n\n**Parágrafo único.** Todo o poder emana do povo.", "art-1/par-unico")
        self.assertEqual(u.text, "Todo o poder emana do povo.")


class TestQuotedAmendments(unittest.TestCase):
    def test_quoted_articles_are_content_of_amending_article(self):
        body = (
            "**Art. 1º** O art. 2º da Lei nº 11.350 passa a vigorar acrescido dos seguintes §§:\n\n"
            '"Art. 2º ..........\n\n'
            "**§ 1º** É essencial a presença de Agentes.\n\n"
            '**§ 2º** Incumbe aos Agentes desempenhar as atividades."\n\n'
            "**Art. 2º** O art. 3º passa a vigorar com a seguinte redação:\n\n"
            "“Art. 3º O Agente tem como atribuição.” (NR)\n\n"
            "**Art. 3º** Esta Lei entra em vigor na data de sua publicação."
        )
        p = arts(body)
        self.assertEqual(list(p), ["art-1", "art-2", "art-3"])
        self.assertEqual(p["art-1"].children, [])  # os §§ citados não são parágrafos desta lei
        self.assertIn("Incumbe aos Agentes", p["art-1"].text)


class TestDivisions(unittest.TestCase):
    def test_hierarchy_from_keyword_not_hash_depth(self):
        # CF usa ## para TÍTULO; o Código Civil usa ###. Ambos devem dar a mesma árvore.
        for hashes in (("##", "###"), ("###", "####")):
            body = (f"{hashes[0]} TÍTULO I — DAS PESSOAS\n\n{hashes[1]} CAPÍTULO I — DA PERSONALIDADE\n\n"
                    f"**Art. 1º** Toda pessoa é capaz.\n\n{hashes[1]} CAPÍTULO II — DOS DIREITOS\n\n**Art. 11.** Os direitos.")
            root = parse_body(body).root
            titulo = root.children[0]
            self.assertEqual(titulo.div_type, "titulo")
            self.assertEqual([c.div_type for c in titulo.children], ["capitulo", "capitulo"])
            self.assertEqual(titulo.children[1].children[0].path, "art-11")

    def test_adct_opens_new_scope(self):
        body = ("## TÍTULO IX — Das Disposições Gerais\n\n**Art. 250.** Com o objetivo.\n\n"
                "# ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS\n\n**Art. 1º** O Presidente prestará compromisso.")
        self.assertEqual(list(arts(body)), ["art-250", "adct/art-1"])

    def test_article_paths_do_not_depend_on_divisions(self):
        a = arts("## TÍTULO I — X\n\n### CAPÍTULO I — Y\n\n**Art. 5º** Todos são iguais.")
        self.assertEqual(list(a), ["art-5"])

    def test_rubrica_rules(self):
        body = ("**Art. 1º** Não há crime sem lei anterior.\n\n"
                "*(Redação dada pela Emenda Constitucional nº 18, de 1998)*\n\n"
                "**Art. 2º** Ninguém pode ser punido.\n\n"
                "Lei penal no tempo\n\n**Art. 3º** A lei excepcional.")
        a = arts(body)
        self.assertIsNone(a["art-2"].rubrica)  # nota de alteração não é rubrica
        self.assertEqual(a["art-1"].notes[0].kind, "redacao")  # vira nota do artigo anterior
        self.assertEqual(a["art-3"].rubrica, "Lei penal no tempo")


class TestInnerRubrics(unittest.TestCase):
    def test_rubrics_before_paragraphs_and_incisos(self):
        body = ("**Homicídio simples**\n\n**Art. 121.** Matar alguém:\n\nPena - reclusão, de seis a vinte anos.\n\n"
                "Caso de diminuição de pena\n\n**§ 1º** Se o agente comete o crime impelido por motivo de relevante valor.\n\n"
                "**Homicídio qualificado**\n\n**§ 2º** Se o homicídio é cometido:\n\nI - mediante paga;\n\n"
                "**Feminicídio** *(Nome jurídico acrescido pela Lei nº 13.104, de 9/3/2015)*\n\nVI - *(Revogado)*\n\n"
                "**Art. 14.** Diz-se o crime:\n\nCrime consumado\n\nI - consumado, quando nele se reúnem todos os elementos;\n\n"
                "V valorização da diversidade\n\n**Art. 15.** O agente.")
        u = {x.path: x for x in parse_body(body).root.walk()}
        self.assertEqual(u["art-121"].text, "Matar alguém:")  # a rubrica não gruda no caput
        self.assertEqual(u["art-121/par-1"].rubrica, "Caso de diminuição de pena")
        self.assertEqual(u["art-121/par-2"].rubrica, "Homicídio qualificado")
        self.assertEqual(u["art-121/par-2/inc-vi"].rubrica, "Feminicídio")  # sem a nota editorial
        self.assertEqual(u["art-14/inc-i"].rubrica, "Crime consumado")
        self.assertIsNone(u["art-15"].rubrica)  # "V valorização…" não é rubrica (começa com romano)


class TestHelpers(unittest.TestCase):
    def test_roman(self):
        self.assertEqual(roman_to_int("LXXIII"), 73)
        self.assertEqual(roman_to_int("XIV"), 14)
        self.assertIsNone(roman_to_int("ABC"))

    def test_extract_notes_kinds(self):
        clean, notes = extract_notes(
            "valores sociais do trabalho; (Vide Lei nº 13.874, de 2019) (Incluído pela Emenda Constitucional nº 45, de 2004)"
        )
        self.assertEqual(clean, "valores sociais do trabalho;")
        self.assertEqual([n.kind for n in notes], ["vide", "inclusao"])
        self.assertEqual(notes[1].ref, "Emenda Constitucional nº 45, de 2004")

    def test_struck_text_is_history_not_current(self):
        a = arts("**Art. 3º** ~~São absolutamente incapazes os menores de 16 anos e os loucos.~~\n\n"
                 "São absolutamente incapazes os menores de 16 (dezesseis) anos.")["art-3"]
        self.assertEqual(a.text, "São absolutamente incapazes os menores de 16 (dezesseis) anos.")
        self.assertEqual(a.notes[0].kind, "redacao_anterior")
        self.assertIn("loucos", a.notes[0].text)

    def test_fold(self):
        self.assertEqual(structure.fold("CAPÍTULO Seção"), "capitulo secao")


if __name__ == "__main__":
    unittest.main()
