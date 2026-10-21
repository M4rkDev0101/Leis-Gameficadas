"""Monta o documento normalizado a partir de um arquivo do acervo."""

from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import dataclass, field

from . import classify, frontmatter, precedent, quality, structure

ESFERAS = {
    "federal": "federal",
    "estaduais": "estadual",
    "municipais": "municipal",
    "reguladores": "regulador",
    "jurisprudencia": "jurisprudencia",
    "tratados": "tratado",
}


@dataclass
class NormDocument:
    id: str  # caminho sem ".md": chave natural estável
    path: str
    content_hash: str
    esfera: str
    tipo: str
    titulo: str
    numero: str | None
    data: dt.date | None
    ano: int | None
    ementa: str | None
    uf: str | None
    municipio: str | None
    orgao: str | None
    tribunal: str | None
    situacao: str | None
    revogada: bool | None
    versao_texto: str | None
    urn: str | None
    fonte: str | None
    meta: dict[str, object]
    body: structure.ParsedBody
    quality: quality.Quality
    classification: classify.Classification
    precedent: precedent.Precedent | None = None
    warnings: list[str] = field(default_factory=list)


def _s(v: object) -> str | None:
    return None if v is None else str(v)


def build(path: str, text: str, content_hash: str | None = None) -> NormDocument:
    header, body_text = frontmatter.split(text)
    fm = frontmatter.parse(header) if header is not None else frontmatter.FrontMatter()
    meta = fm.data
    esfera = "constituicao" if path == "constituicao.md" else ESFERAS.get(path.split("/")[0], "outro")

    prec: precedent.Precedent | None = None
    if esfera == "jurisprudencia":
        body, prec = precedent.parse(body_text)
        q = quality.assess(f"{prec.enunciado} {prec.tese or ''}", 0, min_tokens=5)
    else:
        body = structure.parse_body(body_text)
        q = quality.assess(body_text, len(body.articles()))

    if esfera == "constituicao":
        meta = {"titulo": body.title, "tipo": "Constituição", "numero": "1988",
                "data": dt.date(1988, 10, 5), "ementa": "Constituição da República Federativa do Brasil."}

    data = meta.get("data")
    if isinstance(data, str):  # municipais trazem a data entre aspas e às vezes vazia
        data = None
    ano_raw = meta.get("ano") or (data.year if isinstance(data, dt.date) else None)
    try:
        ano = int(str(ano_raw)) if ano_raw else None
    except ValueError:
        ano = None
    revogada = meta.get("revogada")
    cls = classify.classify(path, meta)
    if prec and prec.area and prec.area not in cls.areas:
        cls.areas.insert(0, prec.area)
        cls.regras.append(f"ramo:{prec.ramo}")

    return NormDocument(
        id=path[:-3] if path.endswith(".md") else path,
        path=path,
        content_hash=content_hash or hashlib.sha1(text.encode("utf-8")).hexdigest(),
        esfera=esfera,
        tipo=str(meta.get("tipo") or "Desconhecido"),
        titulo=str(meta.get("titulo") or body.title or path),
        numero=_s(meta.get("numero")),
        data=data if isinstance(data, dt.date) else None,
        ano=ano,
        ementa=_s(meta.get("ementa")),
        uf=_s(meta.get("uf")),
        municipio=_s(meta.get("municipio")),
        orgao=_s(meta.get("orgao")),
        tribunal=_s(meta.get("tribunal")),
        situacao=_s(meta.get("situacao")),
        revogada=revogada if isinstance(revogada, bool) else None,
        versao_texto=_s(meta.get("versao_texto")),
        urn=_s(meta.get("urn")),
        fonte=_s(meta.get("fonte")),
        meta=meta,
        body=body,
        quality=q,
        classification=cls,
        precedent=prec,
        warnings=fm.warnings + body.warnings,
    )
