"""Cabeçalho YAML, precedentes, qualidade e classificação."""

import datetime as dt
import unittest

from vade_ingest import classify, document, frontmatter, precedent, quality

LGPD = """---
titulo: "Lei nº 13.709 de 14/08/2018"
tipo: "Lei Ordinária"
numero: "13709"
data: 2018-08-14
ementa: "Lei Geral de Proteção de Dados Pessoais (LGPD)."
revogada: false
versao_texto: "compilada (texto vigente)"
urn: "urn:lex:br:federal:lei:2018-08-14;13709"
baixado_em: 2026-10-13
---
# Lei nº 13.709 de 14/08/2018

**Art. 1º** Esta Lei dispõe sobre o tratamento de dados pessoais, inclusive nos meios digitais, por pessoa natural ou por pessoa jurídica de direito público ou privado, com o objetivo de proteger os direitos fundamentais de liberdade e de privacidade.
"""

STJ_600 = """---
titulo: "Súmula nº 600 do STJ"
tribunal: "STJ"
tipo: "Súmula"
numero: "600"
data: 2017-11-22
---
# Súmula nº 600 do STJ

Súmula 600

DIREITO PENAL - LEI MARIA DA PENHA

Enunciado
Para a configuração da violência doméstica e familiar prevista no
artigo 5º da Lei n. 11.340/2006 (Lei Maria da Penha) não se
exige a coabitação entre autor e vítima.

Órgão Julgador
TERCEIRA SEÇÃO

Página 2604 de 2847

Referências Legislativas
LEG:FED CFB:****** ANO:1988
***** CF-1988 CONSTITUIÇÃO FEDERAL DE 1988
ART:00226 PAR:00008

LEG:FED LEI:011340 ANO:2006
***** LMP-06 LEI MARIA DA PENHA
ART:00005 ART:00007

LEG:FED CFB:****** ANO:1988
ART:00005 INC:00034 LET:A INC:00055 PAR:ÚNICO

Precedentes
REsp 2622 SP 1990/0002974-0 Decisão:08/08/1990
"""

OCR = """# Lei Ordinária nº 5.216, de 17 de janeiro de 1990

~jj ~- GOVÊRNO DA P AR AíB A de jan eir o de 19 90 LEI N. 0 5.2 16 , de 17
ca a As soc iaç ão Rec onh ece de Ut ilid ade Pú bli dim 13 de Ma io, e dos Am igo s e Re sid ent es no Jar dá ou tra s pro vid ênc ias .
O GOVERNADOR DO ESTADO DA dec reta e eu Faço sab er que o Pod er Legislativo sanciono a seguinte Lei: Ut ilid ade Pú bli ca a Ass o- Ar t. lQ - Fic a rec onh eci da
"""


class TestFrontMatter(unittest.TestCase):
    def test_types(self):
        header, body = frontmatter.split(LGPD)
        fm = frontmatter.parse(header)
        self.assertEqual(fm.data["data"], dt.date(2018, 8, 14))
        self.assertIs(fm.data["revogada"], False)
        self.assertEqual(fm.data["numero"], "13709")
        self.assertTrue(body.lstrip().startswith("# Lei"))
        self.assertEqual(fm.warnings, [])

    def test_tolerant(self):
        fm = frontmatter.parse('data:\nrevogada: null\nlixo sem dois pontos\nementa: "com \\"aspas\\""\ndata_publicacao: "1997-05-05"')
        self.assertIsNone(fm.data["data"])
        self.assertIsNone(fm.data["revogada"])
        self.assertEqual(fm.data["ementa"], 'com "aspas"')
        self.assertEqual(fm.data["data_publicacao"], dt.date(1997, 5, 5))  # municipais trazem data entre aspas
        self.assertEqual(len(fm.warnings), 1)

    def test_no_header(self):
        self.assertEqual(frontmatter.split("# Constituição\n\ntexto"), (None, "# Constituição\n\ntexto"))


class TestPrecedent(unittest.TestCase):
    def test_stj_sumula(self):
        body, p = precedent.parse(frontmatter.split(STJ_600)[1])
        self.assertTrue(p.enunciado.startswith("Para a configuração da violência doméstica"))
        self.assertTrue(p.enunciado.endswith("entre autor e vítima."))
        self.assertEqual(p.ramo, "DIREITO PENAL")
        self.assertEqual(p.tema, "LEI MARIA DA PENHA")
        self.assertEqual(p.area, "penal")
        self.assertEqual(p.orgao_julgador, "TERCEIRA SEÇÃO")
        self.assertEqual(body.root.children[0].path, "enunciado")

    def test_references_are_lists_not_nesting(self):
        _, p = precedent.parse(frontmatter.split(STJ_600)[1])
        got = [(r.tipo, r.numero, r.ano, r.caminho) for r in p.referencias]
        self.assertEqual(got, [
            ("Constituição", None, 1988, "art-226/par-8"),
            ("Lei Ordinária", "11340", 2006, "art-5"),
            ("Lei Ordinária", "11340", 2006, "art-7"),
            ("Constituição", None, 1988, "art-5/inc-xxxiv/ali-a"),
            # PAR está acima de INC: fecha o caminho do inciso e abre outro
            ("Constituição", None, 1988, "art-5/inc-lv"),
            ("Constituição", None, 1988, "art-5/par-unico"),
        ])

    def test_bnp_format(self):
        _, p = precedent.parse("# Súmula vinculante nº 1 do STF\n\n## Questão\n\nOfende a garantia constitucional.\n\n## Tese\n\nnão informado\n\n## Registro original do CNJ\n\n```json\n{}\n```")
        self.assertEqual(p.enunciado, "Ofende a garantia constitucional.")
        self.assertIsNone(p.tese)


class TestQualityAndClassification(unittest.TestCase):
    def test_ocr_is_low_and_compiled_is_high(self):
        self.assertEqual(quality.assess(OCR, 0).tier, "baixa")
        self.assertEqual(document.build("federal/leis-ordinarias/2018/lei-13709-2018-08-14.md", LGPD).quality.tier, "alta")

    def test_empty_text_is_low(self):
        self.assertEqual(quality.assess("Só metadados.", 0).tier, "baixa")

    def test_catalog_known_law(self):
        doc = document.build("federal/leis-ordinarias/2018/lei-13709-2018-08-14.md", LGPD)
        self.assertEqual(doc.classification.sigla, "LGPD")
        self.assertEqual(doc.classification.relevancia, "alta")
        self.assertIn("protecao-de-dados", doc.classification.areas)
        self.assertEqual((doc.esfera, doc.ano, doc.id), ("federal", 2018, "federal/leis-ordinarias/2018/lei-13709-2018-08-14"))

    def test_concrete_acts_have_low_relevance(self):
        c = classify.classify("estaduais/PB/leis-ordinarias/1990/x.md",
                              {"tipo": "Lei Ordinária", "ementa": "RECONHECE DE UTILIDADE PÚBLICA A ASSOCIAÇÃO DOS AMIGOS"})
        self.assertEqual(c.relevancia, "baixa")
        c = classify.classify("estaduais/MG/leis-ordinarias/2019/y.md", {"tipo": "Lei Ordinária", "ementa": "Dá denominação a escola estadual."})
        self.assertEqual(c.relevancia, "baixa")

    def test_keyword_areas(self):
        c = classify.classify("estaduais/SP/leis-ordinarias/2015/z.md",
                              {"tipo": "Lei Ordinária", "ementa": "Altera a alíquota do ICMS e dispõe sobre o servidor público."})
        self.assertEqual(c.areas[:2], ["tributario", "administrativo"])
        self.assertEqual(c.relevancia, "normal")

    def test_precedent_area_flows_into_document(self):
        doc = document.build("jurisprudencia/stj/sumulas/sumula-600.md", STJ_600)
        self.assertEqual(doc.esfera, "jurisprudencia")
        self.assertEqual(doc.classification.areas[0], "penal")
        self.assertEqual(doc.quality.tier, "alta")

    def test_constitution_without_header(self):
        doc = document.build("constituicao.md", "# Constituição da República Federativa do Brasil de 1988\n\n**Art. 1º** A República Federativa do Brasil, formada pela união indissolúvel dos Estados e Municípios e do Distrito Federal, constitui-se em Estado Democrático de Direito.")
        self.assertEqual((doc.esfera, doc.classification.sigla, doc.ano), ("constituicao", "CF", 1988))


if __name__ == "__main__":
    unittest.main()
