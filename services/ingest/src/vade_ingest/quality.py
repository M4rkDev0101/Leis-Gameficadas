"""Nota de qualidade do texto (0–1).

O acervo mistura textos compilados impecáveis com OCR ilegível, por exemplo
``"Ar t. lQ - Fic a rec onh eci da"``. Conteúdo de estudo (questões, flashcards) só
pode ser gerado a partir de texto confiável, então cada norma recebe uma nota e uma faixa:

* ``alta``  (>= 0.80): pode gerar conteúdo automaticamente;
* ``media`` (>= 0.50): exibir, gerar só com revisão;
* ``baixa`` (<  0.50): só exibir, com aviso, e marcar para reprocessamento.

O sinal principal é a proporção de fragmentos: palavras curtas que não são palavras
curtas comuns do português. OCR quebrado cria muitos fragmentos ("soc", "iaç", "ão").
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SHORT_OK = frozenset(
    """a o e é à ao aos as os às da de do das dos em no na nos nas um uma por que se ou com sem
    seu sua lei art arts nº n inc § sob até são ser foi dia mês ano mil pelo pela pelos pelas
    não já há só lhe me te nem mas pro cpf ii iii iv vi vii ix xi xii xiv xv xvi xix xx xxi
    vez fim uso via dez seis sete oito nove três dois duas cem ato atos fiz fez bem mal art.""".split()
)
_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ]+")


@dataclass(frozen=True)
class Quality:
    score: float
    tier: str  # alta | media | baixa
    fragment_ratio: float
    tokens: int


def assess(text: str, articles_found: int, min_tokens: int = 15) -> Quality:
    tokens = _TOKEN_RE.findall(text)
    if len(tokens) < min_tokens:
        # quase sem texto: só metadados (a fonte serviu documento vazio)
        return Quality(0.0, "baixa", 0.0, len(tokens))
    frags = sum(1 for t in tokens if len(t) <= 3 and t.lower() not in _SHORT_OK)
    ratio = frags / len(tokens)
    score = max(0.0, min(1.0, 1.0 - max(0.0, ratio - 0.06) * 3.0))
    if articles_found == 0 and re.search(r"\bAr\s?t\b", text):
        score *= 0.6  # há "Art" no texto mas nenhum artigo foi reconhecido
    tier = "alta" if score >= 0.8 else "media" if score >= 0.5 else "baixa"
    return Quality(round(score, 3), tier, round(ratio, 4), len(tokens))
