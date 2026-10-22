"""Ferramentas de dublagem: ids estáveis e nenhuma ferramenta pode apagar colunas do elenco."""

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import vozes  # noqa: E402


def read_cast(d: Path) -> dict[str, dict]:
    with open(d / "elenco.csv", encoding="utf-8-sig") as f:
        return {r["personagem"]: r for r in csv.DictReader(f, delimiter=";")}


class TestVozes(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_voice_id_is_stable_and_matches_the_client(self):
        # o navegador calcula o mesmo sha1("personagem|texto")[:12] (testado também na interface)
        self.assertEqual(vozes.voice_id("helena", "Bem-vindo(a) à Vasconcelos & Duarte. Aqui estagiário não serve café: "
                                        "estagiário trabalha."), "adb0f86cc1d7")

    def test_reexport_and_recast_keep_profiles(self):
        vozes.exportar(self.tmp)
        rows = list(read_cast(self.tmp).values())
        for r in rows:
            r["perfil_vs"] = "p-" + r["personagem"]
        vozes._write_cast(self.tmp, rows)
        vozes.exportar(self.tmp)  # reexportar não pode apagar perfis
        (self.tmp / "conta.json").write_text(json.dumps({"voices": [
            {"voice_id": "m1", "name": "M", "labels": {"gender": "male", "age": "middle_aged"}},
            {"voice_id": "f1", "name": "F", "labels": {"gender": "female", "age": "young"}}]}), encoding="utf-8")
        subprocess.run([sys.executable, str(TOOLS / "escalar_vozes.py"), "--saida", str(self.tmp), "--vozes",
                        str(self.tmp / "conta.json")], check=True, capture_output=True)
        cast = read_cast(self.tmp)
        self.assertEqual(cast["helena"]["perfil_vs"], "p-helena")
        self.assertEqual(cast["helena"]["genero"], "mulher")
        self.assertTrue(all(r["perfil_vs"] for r in cast.values()))


if __name__ == "__main__":
    unittest.main()
