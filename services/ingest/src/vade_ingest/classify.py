"""Classificação inicial por regras: área do Direito, nome popular e relevância para estudo.

É a camada 0 da taxonomia (ver docs/05-pipeline-importacao.md): regras determinísticas e
auditáveis. Depois, um classificador por embeddings e revisão editorial refinam
disciplina/tema/subtema. As regras daqui servem de rótulo fraco para treinar essa etapa.

Relevância: a maior parte das leis estaduais e municipais é **ato de efeito concreto**
(declara utilidade pública, dá nome a rua, concede título de cidadão). Elas continuam
pesquisáveis, mas não entram nas trilhas de estudo nem na geração de questões.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .structure import fold

AREAS = (
    "constitucional", "administrativo", "civil", "processo-civil", "penal", "processo-penal",
    "penal-especial", "trabalho", "processo-trabalho", "tributario", "financeiro", "empresarial",
    "ambiental", "eleitoral", "previdenciario", "consumidor", "direitos-humanos", "internacional",
    "economico", "militar", "digital", "protecao-de-dados", "crianca-adolescente", "saude",
    "educacao", "urbanistico", "agrario",
)


@dataclass(frozen=True)
class Known:
    nome: str
    sigla: str | None
    areas: tuple[str, ...]


# (tipo canônico, número) das normas federais mais estudadas. A CF entra pelo caminho.
KNOWN: dict[tuple[str, str], Known] = {
    ("Decreto-Lei", "2848"): Known("Código Penal", "CP", ("penal",)),
    ("Decreto-Lei", "3689"): Known("Código de Processo Penal", "CPP", ("processo-penal",)),
    ("Decreto-Lei", "5452"): Known("Consolidação das Leis do Trabalho", "CLT", ("trabalho", "processo-trabalho")),
    ("Decreto-Lei", "4657"): Known("Lei de Introdução às Normas do Direito Brasileiro", "LINDB", ("civil",)),
    ("Decreto-Lei", "1001"): Known("Código Penal Militar", "CPM", ("militar", "penal")),
    ("Decreto-Lei", "1002"): Known("Código de Processo Penal Militar", "CPPM", ("militar", "processo-penal")),
    ("Decreto-Lei", "3688"): Known("Lei das Contravenções Penais", "LCP", ("penal-especial",)),
    ("Lei Ordinária", "10406"): Known("Código Civil", "CC", ("civil",)),
    ("Lei Ordinária", "13105"): Known("Código de Processo Civil", "CPC", ("processo-civil",)),
    ("Lei Ordinária", "5172"): Known("Código Tributário Nacional", "CTN", ("tributario",)),
    ("Lei Ordinária", "8078"): Known("Código de Defesa do Consumidor", "CDC", ("consumidor",)),
    ("Lei Ordinária", "8069"): Known("Estatuto da Criança e do Adolescente", "ECA", ("crianca-adolescente",)),
    ("Lei Ordinária", "10741"): Known("Estatuto da Pessoa Idosa", None, ("direitos-humanos",)),
    ("Lei Ordinária", "13146"): Known("Estatuto da Pessoa com Deficiência", "LBI", ("direitos-humanos",)),
    ("Lei Ordinária", "11340"): Known("Lei Maria da Penha", None, ("penal-especial", "direitos-humanos")),
    ("Lei Ordinária", "11343"): Known("Lei de Drogas", None, ("penal-especial",)),
    ("Lei Ordinária", "13709"): Known("Lei Geral de Proteção de Dados", "LGPD", ("protecao-de-dados", "digital")),
    ("Lei Ordinária", "12965"): Known("Marco Civil da Internet", None, ("digital",)),
    ("Lei Ordinária", "14133"): Known("Lei de Licitações e Contratos", None, ("administrativo",)),
    ("Lei Ordinária", "8666"): Known("Lei de Licitações (revogada)", None, ("administrativo",)),
    ("Lei Ordinária", "8429"): Known("Lei de Improbidade Administrativa", "LIA", ("administrativo",)),
    ("Lei Ordinária", "8112"): Known("Estatuto dos Servidores Públicos Federais", None, ("administrativo",)),
    ("Lei Ordinária", "9784"): Known("Lei do Processo Administrativo Federal", None, ("administrativo",)),
    ("Lei Ordinária", "12846"): Known("Lei Anticorrupção", None, ("administrativo",)),
    ("Lei Ordinária", "12527"): Known("Lei de Acesso à Informação", "LAI", ("administrativo",)),
    ("Lei Ordinária", "4737"): Known("Código Eleitoral", None, ("eleitoral",)),
    ("Lei Ordinária", "9504"): Known("Lei das Eleições", None, ("eleitoral",)),
    ("Lei Ordinária", "9605"): Known("Lei de Crimes Ambientais", None, ("ambiental", "penal-especial")),
    ("Lei Ordinária", "6938"): Known("Política Nacional do Meio Ambiente", None, ("ambiental",)),
    ("Lei Ordinária", "12651"): Known("Código Florestal", None, ("ambiental",)),
    ("Lei Ordinária", "7210"): Known("Lei de Execução Penal", "LEP", ("processo-penal",)),
    ("Lei Ordinária", "9099"): Known("Lei dos Juizados Especiais", None, ("processo-civil", "processo-penal")),
    ("Lei Ordinária", "8072"): Known("Lei dos Crimes Hediondos", None, ("penal-especial",)),
    ("Lei Ordinária", "9455"): Known("Lei de Tortura", None, ("penal-especial",)),
    ("Lei Ordinária", "12850"): Known("Lei das Organizações Criminosas", None, ("penal-especial",)),
    ("Lei Ordinária", "10826"): Known("Estatuto do Desarmamento", None, ("penal-especial",)),
    ("Lei Ordinária", "13869"): Known("Lei de Abuso de Autoridade", None, ("penal-especial",)),
    ("Lei Ordinária", "9613"): Known("Lei de Lavagem de Dinheiro", None, ("penal-especial",)),
    ("Lei Ordinária", "9503"): Known("Código de Trânsito Brasileiro", "CTB", ("administrativo", "penal-especial")),
    ("Lei Ordinária", "8213"): Known("Lei de Benefícios da Previdência Social", None, ("previdenciario",)),
    ("Lei Ordinária", "8212"): Known("Lei de Custeio da Seguridade Social", None, ("previdenciario",)),
    ("Lei Ordinária", "4320"): Known("Lei de Normas Gerais de Direito Financeiro", None, ("financeiro",)),
    ("Lei Ordinária", "6404"): Known("Lei das Sociedades Anônimas", None, ("empresarial",)),
    ("Lei Ordinária", "11101"): Known("Lei de Falências e Recuperação", None, ("empresarial",)),
    ("Lei Ordinária", "12529"): Known("Lei de Defesa da Concorrência", None, ("economico",)),
    ("Lei Ordinária", "13874"): Known("Lei da Liberdade Econômica", None, ("economico", "empresarial")),
    ("Lei Ordinária", "9868"): Known("Lei da ADI e ADC", None, ("constitucional",)),
    ("Lei Ordinária", "12016"): Known("Lei do Mandado de Segurança", None, ("constitucional", "processo-civil")),
    ("Lei Ordinária", "7347"): Known("Lei da Ação Civil Pública", None, ("processo-civil",)),
    ("Lei Complementar", "101"): Known("Lei de Responsabilidade Fiscal", "LRF", ("financeiro",)),
    ("Lei Complementar", "64"): Known("Lei de Inelegibilidades", None, ("eleitoral",)),
    ("Lei Complementar", "123"): Known("Estatuto da Microempresa", None, ("empresarial", "tributario")),
    ("Lei Complementar", "75"): Known("Lei Orgânica do Ministério Público da União", None, ("administrativo",)),
    ("Lei Complementar", "80"): Known("Lei Orgânica da Defensoria Pública", None, ("administrativo",)),
    ("Lei Complementar", "35"): Known("Lei Orgânica da Magistratura", "LOMAN", ("administrativo",)),
    ("Lei Complementar", "214"): Known("Lei do IBS e da CBS", None, ("tributario",)),
}

# palavra-chave (sem acento, minúscula) → área. Aplicadas sobre ementa + título.
_KEYWORDS: tuple[tuple[str, str], ...] = (
    (r"\b(tribut|imposto|icms|iss\b|ipva|itcmd|contribuic|taxa de|isenc|credito tributario)", "tributario"),
    (r"\b(orcament|diretrizes orcamentarias|credito (especial|suplementar)|despesa publica|fundo estadual)", "financeiro"),
    (r"\b(servidor|cargos? (publico|efetivo|em comissao)|carreira|concurso publico|licitac|administracao publica|autarquia|"
     r"estatuto dos funcionarios|vencimento|remuneracao)", "administrativo"),
    (r"\b(crime|penal|pena\b|delito|contraven)", "penal"),
    (r"\b(eleic|eleitor|partido|inelegib)", "eleitoral"),
    (r"\b(meio ambiente|ambiental|florest|recursos hidricos|residuos|licenciamento ambiental)", "ambiental"),
    (r"\b(consumidor)", "consumidor"),
    (r"\b(previdenc|aposentador|pensao|seguridade social|beneficio previdenciario)", "previdenciario"),
    (r"\b(trabalh|empregad|sindica|salario minimo)", "trabalho"),
    (r"\b(crianca|adolescente|juventude)", "crianca-adolescente"),
    (r"\b(direitos humanos|pessoa com deficiencia|idoso|igualdade racial|indigena|mulher)", "direitos-humanos"),
    (r"\b(dados pessoais|protecao de dados)", "protecao-de-dados"),
    (r"\b(internet|digital|eletronic|informatic|tecnologia da informacao)", "digital"),
    (r"\b(militar|forcas armadas|policia militar|bombeiro)", "militar"),
    (r"\b(saude|sus\b|vigilancia sanitaria|medicament)", "saude"),
    (r"\b(educac|ensino|escola|universidade)", "educacao"),
    (r"\b(urban|plano diretor|parcelamento do solo|zoneamento)", "urbanistico"),
    (r"\b(agrari|reforma agraria|rural)", "agrario"),
    (r"\b(sociedades? (anonima|limitada|empresaria)|empresari|falenc|recuperacao judicial|registro mercantil)", "empresarial"),
    (r"\b(tratado|convencao internacional|acordo internacional)", "internacional"),
    (r"\b(constituic|emenda constitucional)", "constitucional"),
)
_KEYWORDS_RE = tuple((re.compile(p), a) for p, a in _KEYWORDS)

_CONCRETE = re.compile(
    r"(declara de utilidade publica|considera de utilidade publica|reconhece de utilidade publica|"
    r"de utilidade publica|denomina|da (o )?nome|da denominacao|concede (o )?titulo|titulo de cidadao|"
    r"institui o dia|inclui no calendario|autoriza (a )?(doacao|alienacao|permuta|cessao)|"
    r"desafeta|abre (ao orcamento )?credito|declara patrimonio)"
)

_JURIS_AREAS = {"tst": ("trabalho", "processo-trabalho"), "tnu": ("previdenciario",)}


@dataclass
class Classification:
    areas: list[str] = field(default_factory=list)
    nome_popular: str | None = None
    sigla: str | None = None
    relevancia: str = "normal"  # alta | normal | baixa (efeito concreto)
    regras: list[str] = field(default_factory=list)  # por que — para auditoria


def classify(path: str, meta: dict[str, object]) -> Classification:
    c = Classification()
    tipo = str(meta.get("tipo") or "")
    numero = str(meta.get("numero") or "")
    federal = path.startswith("federal/")

    if path == "constituicao.md":
        c.areas, c.nome_popular, c.sigla, c.relevancia = ["constitucional"], "Constituição Federal", "CF", "alta"
        c.regras.append("caminho:constituicao")
        return c
    if federal and (k := KNOWN.get((tipo, numero))):
        c.areas, c.nome_popular, c.sigla, c.relevancia = list(k.areas), k.nome, k.sigla, "alta"
        c.regras.append(f"catalogo:{tipo}:{numero}")
        return c
    if path.startswith("jurisprudencia/"):
        trib = path.split("/")[1]
        c.relevancia = "alta" if "sumula" in path else "normal"
        if trib in _JURIS_AREAS:
            c.areas = list(_JURIS_AREAS[trib])
            c.regras.append(f"tribunal:{trib}")

    text = fold(f"{meta.get('ementa') or ''} {meta.get('titulo') or ''}")
    if (_CONCRETE.search(text) and not federal) or "utilidade publica" in text:
        c.relevancia = "baixa"
        c.regras.append("efeito-concreto")
    for rx, area in _KEYWORDS_RE:
        if rx.search(text) and area not in c.areas:
            c.areas.append(area)
            c.regras.append(f"palavra:{area}")
    if tipo == "Emenda Constitucional" and "constitucional" not in c.areas:
        c.areas.insert(0, "constitucional")
        c.regras.append("tipo:emenda-constitucional")
    return c
