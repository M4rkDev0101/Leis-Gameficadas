"""Gera o pacote de vozes (zips + manifesto) a partir da pasta local de vozes. NÃO publica nada.

    python instalador/gerar_pacote_vozes.py --vozes %LOCALAPPDATA%\\VadeTribunal\\vozes --saida C:\\lx\\tmp-pacote --versao 1

Saída: vozes-parte-<prefixo>.zip (mp3 sem compressão, zip determinístico: conteúdo igual => sha256 igual) e
vozes-manifesto.json. Ao final imprime o comando `gh release create vozes-vN ...` (executar só com autorização).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vozes_pacote as vp  # noqa: E402

DATA_FIXA = (2020, 1, 1, 0, 0, 0)
LIMITE_ASSET = 1_800_000_000  # o GitHub aceita até 2 GiB por arquivo de release


def agrupar(arquivos: list[Path], max_bytes: int) -> dict[str, list[Path]]:
    """Agrupa por prefixo do nome: 1 caractere; se alguma parte passar do limite, usa 2 (depois 3)."""
    for n in (1, 2, 3):
        g: dict[str, list[Path]] = {}
        for p in arquivos:
            g.setdefault(p.stem[:n], []).append(p)
        if all(sum(q.stat().st_size for q in lst) <= max_bytes for lst in g.values()):
            return g
    return g


def gerar(vozes: Path, saida: Path, versao: int, max_bytes: int = LIMITE_ASSET) -> dict:
    arquivos = sorted((p for p in vozes.glob("*.mp3") if vp.NOME_MP3_RE.match(p.name)), key=lambda p: p.name)
    if not arquivos:
        raise SystemExit(f"nenhum .mp3 em {vozes}")
    saida.mkdir(parents=True, exist_ok=True)
    grupos = agrupar(arquivos, max_bytes)
    partes = []
    for pref in sorted(grupos):
        nome = f"vozes-parte-{pref}.zip"
        zp = saida / nome
        infos = {}
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
            for p in grupos[pref]:
                zi = zipfile.ZipInfo(p.name, DATA_FIXA)
                zi.compress_type = zipfile.ZIP_STORED
                zi.external_attr = 0o644 << 16
                z.writestr(zi, p.read_bytes())
                infos[p.name] = {"sha256": vp.sha256_arquivo(p), "tamanho": p.stat().st_size}
        partes.append({"nome": nome, "tamanho": zp.stat().st_size, "sha256": vp.sha256_arquivo(zp), "arquivos": infos})
    m = {"formato": 1, "versao": versao, "tag": f"vozes-v{versao}", "gerado_em": time.strftime("%Y-%m-%d"),
         "total_arquivos": len(arquivos), "tamanho_total": sum(p["tamanho"] for p in partes), "partes": partes}
    vp.validar_manifesto(m)
    (saida / vp.MANIFESTO_NOME).write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    return m


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vozes", required=True, type=Path)
    ap.add_argument("--saida", required=True, type=Path)
    ap.add_argument("--versao", required=True, type=int)
    ap.add_argument("--max-parte-mb", type=int, default=LIMITE_ASSET // 1_000_000)
    a = ap.parse_args()
    m = gerar(a.vozes, a.saida, a.versao, a.max_parte_mb * 1_000_000)
    print(f"{m['total_arquivos']} falas em {len(m['partes'])} parte(s), {m['tamanho_total'] / 1e6:.1f} MB -> {a.saida}")
    print("\nPara publicar (NÃO executado; só com autorização do usuário):")
    print(f'  gh release create {m["tag"]} "{a.saida}\\vozes-manifesto.json" "{a.saida}\\vozes-parte-*.zip" '
          f'--repo M4rkDev0101/Leis-Gameficadas --title "Vozes v{a.versao}" --notes "Pacote de dublagem v{a.versao}"')


if __name__ == "__main__":
    main()
