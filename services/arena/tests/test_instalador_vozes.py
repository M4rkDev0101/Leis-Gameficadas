"""Dublagem opcional do instalador: manifesto, verificação sha256, retomada e atualização incremental.

Usa um servidor HTTP local (com suporte a Range) que imita a API de releases do GitHub; nada de rede real.
"""

import json
import shutil
import sys
import tempfile
import threading
import unittest
import zipfile
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

INST = Path(__file__).resolve().parents[3] / "instalador"
sys.path.insert(0, str(INST))

import gerar_pacote_vozes as gen  # noqa: E402
import vozes_pacote as vp  # noqa: E402


class Fake(BaseHTTPRequestHandler):
    """Serve self.server.files {caminho: bytes}; /releases devolve a lista de releases do servidor."""

    def log_message(self, *a):
        pass

    def do_GET(self):
        srv = self.server
        if self.path == "/releases":
            body = json.dumps(srv.releases).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        data = srv.files.get(self.path)
        if data is None:
            self.send_error(404)
            return
        srv.hits.append((self.path, self.headers.get("Range")))
        rng = self.headers.get("Range")
        if rng and srv.aceita_range:
            ini = int(rng.split("=")[1].split("-")[0])
            if ini >= len(data):
                self.send_error(416)
                return
            body = data[ini:]
            self.send_response(206)
        else:
            body = data
            self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        cortar = srv.corta_em.pop(self.path, None)  # simula queda de conexão no meio do download
        self.wfile.write(body[:cortar] if cortar else body)
        if cortar:
            self.wfile.flush()
            self.close_connection = True


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="vadeinst"))
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
        self.srv.files, self.srv.releases, self.srv.hits = {}, [], []
        self.srv.aceita_range, self.srv.corta_em = True, {}
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def fazer_vozes(self, pasta: Path, falas: dict[str, bytes]) -> Path:
        pasta.mkdir(parents=True, exist_ok=True)
        for nome, b in falas.items():
            (pasta / nome).write_bytes(b)
        return pasta

    def publicar(self, falas: dict[str, bytes], versao: int, max_bytes=gen.LIMITE_ASSET) -> dict:
        """Gera o pacote de `falas` e o expõe no servidor falso como release vozes-v<versao>."""
        origem = self.fazer_vozes(self.tmp / f"orig{versao}", falas)
        saida = self.tmp / f"pacote{versao}"
        m = gen.gerar(origem, saida, versao, max_bytes)
        assets = []
        for f in saida.iterdir():
            self.srv.files[f"/v{versao}/{f.name}"] = f.read_bytes()
            assets.append({"name": f.name, "browser_download_url": f"{self.url}/v{versao}/{f.name}"})
        rel = {"tag_name": f"vozes-v{versao}", "draft": False, "prerelease": False, "assets": assets}
        self.srv.releases = [r for r in self.srv.releases if r["tag_name"] != rel["tag_name"]] + [rel]
        return rel


FALAS = {f"{h}{i:011x}.mp3": (f"fala {h}{i} ".encode() * 300) for h in "0a" for i in range(3)}


class TestManifesto(Base):
    def test_gera_manifesto_valido_e_deterministico(self):
        orig = self.fazer_vozes(self.tmp / "o", FALAS)
        m1 = gen.gerar(orig, self.tmp / "a", 1)
        m2 = gen.gerar(orig, self.tmp / "b", 1)
        self.assertEqual([p["sha256"] for p in m1["partes"]], [p["sha256"] for p in m2["partes"]])
        self.assertEqual(m1["total_arquivos"], len(FALAS))
        self.assertEqual(sorted(p["nome"] for p in m1["partes"]), ["vozes-parte-0.zip", "vozes-parte-a.zip"])
        vp.validar_manifesto(m1)
        with zipfile.ZipFile(self.tmp / "a" / "vozes-parte-0.zip") as z:
            self.assertTrue(all("/" not in n for n in z.namelist()))

    def test_ignora_o_que_nao_e_mp3_de_fala(self):
        orig = self.fazer_vozes(self.tmp / "o", {**FALAS, "elenco.csv": b"x", "gerar.log": b"y"})
        (orig / "referencias").mkdir()
        m = gen.gerar(orig, self.tmp / "a", 1)
        self.assertEqual(m["total_arquivos"], len(FALAS))

    def test_divide_em_mais_partes_quando_passa_do_limite(self):
        orig = self.fazer_vozes(self.tmp / "o", {f"00{i}.mp3": b"x" * 1000 for i in range(4)} | {f"01{i}.mp3": b"y" * 1000 for i in range(4)})
        m = gen.gerar(orig, self.tmp / "a", 1, max_bytes=5000)
        self.assertGreater(len(m["partes"]), 1)
        self.assertEqual(sum(len(p["arquivos"]) for p in m["partes"]), 8)

    def test_manifesto_rejeita_caminhos_e_sha_invalido(self):
        m = gen.gerar(self.fazer_vozes(self.tmp / "o", FALAS), self.tmp / "a", 1)
        ruim = json.loads(json.dumps(m))
        parte = ruim["partes"][0]
        parte["arquivos"]["../fora.mp3"] = parte["arquivos"].pop(next(iter(parte["arquivos"])))
        with self.assertRaises(vp.PacoteErro):
            vp.validar_manifesto(ruim)
        ruim = json.loads(json.dumps(m))
        ruim["partes"][0]["sha256"] = "zz"
        with self.assertRaises(vp.PacoteErro):
            vp.validar_manifesto(ruim)
        with self.assertRaises(vp.PacoteErro):
            vp.validar_manifesto({"formato": 9})

    def test_escolhe_a_maior_tag_publicada(self):
        rels = [{"tag_name": t, "draft": d, "prerelease": False, "assets": []}
                for t, d in (("vozes-v2", False), ("vozes-v10", False), ("vozes-v11", True), ("v1.0", False), ("vozes-vx", False))]
        self.srv.releases = rels
        self.assertEqual(vp.buscar_release(self.url + "/releases")["tag_name"], "vozes-v10")


class TestInstalacao(Base):
    def test_instala_do_zero_e_confere_arquivos(self):
        rel = self.publicar(FALAS, 1)
        m = vp.buscar_manifesto(rel)
        destino = self.tmp / "vozes"
        prog = []
        r = vp.instalar(m, rel, destino, lambda t, f: prog.append(f))
        self.assertEqual(r["arquivos"], len(FALAS))
        for nome, b in FALAS.items():
            self.assertEqual((destino / nome).read_bytes(), b)
        self.assertEqual(vp.versao_instalada(destino), 1)
        self.assertEqual(prog[-1], 1.0)
        self.assertEqual(sorted(prog), prog)  # progresso monotônico
        self.assertFalse((destino / ".baixando").exists())

    def test_retoma_download_interrompido_com_range(self):
        rel = self.publicar(FALAS, 1)
        m = vp.buscar_manifesto(rel)
        parte = m["partes"][0]
        caminho = "/v1/" + parte["nome"]
        self.srv.corta_em[caminho] = parte["tamanho"] // 2  # 1ª tentativa cai no meio
        destino = self.tmp / "vozes"
        vp.instalar(m, rel, destino)
        pedidos = [rg for c, rg in self.srv.hits if c == caminho]
        self.assertIsNone(pedidos[0])
        self.assertTrue(pedidos[1].startswith("bytes=") and not pedidos[1].endswith("=0-"))
        for nome, b in FALAS.items():
            self.assertEqual((destino / nome).read_bytes(), b)

    def test_servidor_sem_range_recomeca_do_zero(self):
        rel = self.publicar(FALAS, 1)
        m = vp.buscar_manifesto(rel)
        parte = m["partes"][0]
        destino = self.tmp / "z.zip"
        destino.parent.mkdir(exist_ok=True)
        dados = self.srv.files["/v1/" + parte["nome"]]
        destino.with_name("z.zip.part").write_bytes(dados[:50])
        self.srv.aceita_range = False
        vp.baixar_retomavel(f"{self.url}/v1/{parte['nome']}", destino, parte["tamanho"], parte["sha256"])
        self.assertEqual(destino.read_bytes(), dados)

    def test_continua_de_um_part_existente(self):
        rel = self.publicar(FALAS, 1)
        parte = vp.buscar_manifesto(rel)["partes"][0]
        dados = self.srv.files["/v1/" + parte["nome"]]
        destino = self.tmp / "c" / "p.zip"
        destino.parent.mkdir()
        destino.with_name("p.zip.part").write_bytes(dados[:100])
        vp.baixar_retomavel(f"{self.url}/v1/{parte['nome']}", destino, parte["tamanho"], parte["sha256"])
        self.assertEqual(destino.read_bytes(), dados)
        self.assertEqual(self.srv.hits[-1][1], "bytes=100-")

    def test_sha256_errado_apaga_e_falha(self):
        rel = self.publicar(FALAS, 1)
        parte = vp.buscar_manifesto(rel)["partes"][0]
        self.srv.files["/v1/" + parte["nome"]] = b"\0" * parte["tamanho"]  # corrompido, mesmo tamanho
        destino = self.tmp / "c" / "p.zip"
        with self.assertRaises(vp.PacoteErro):
            vp.baixar_retomavel(f"{self.url}/v1/{parte['nome']}", destino, parte["tamanho"], parte["sha256"])
        self.assertFalse(destino.exists())
        self.assertFalse(destino.with_name("p.zip.part").exists())

    def test_zip_adulterado_com_sha_do_manifesto_diferente_nao_extrai(self):
        orig = self.fazer_vozes(self.tmp / "o", {"aa.mp3": b"bom"})
        m = gen.gerar(orig, self.tmp / "pk", 1)
        parte = m["partes"][0]
        with zipfile.ZipFile(self.tmp / "pk" / parte["nome"], "w") as z:  # troca o conteúdo mas mantém o nome
            z.writestr("aa.mp3", b"mau")
            z.writestr("../evil.mp3", b"x")
        destino = self.tmp / "v"
        destino.mkdir()
        with self.assertRaises(vp.PacoteErro):
            vp.extrair_parte(self.tmp / "pk" / parte["nome"], parte, destino)
        self.assertEqual(list(destino.iterdir()), [])
        self.assertFalse((self.tmp / "evil.mp3").exists())

    def test_atualizacao_baixa_so_a_parte_que_mudou(self):
        rel1 = self.publicar(FALAS, 1)
        destino = self.tmp / "vozes"
        vp.instalar(vp.buscar_manifesto(rel1), rel1, destino)
        novas = dict(FALAS)
        novas["a00000000001.mp3"] = b"regravada " * 500  # muda 1 fala da parte 'a'
        novas["a0000000ffff.mp3"] = b"nova"
        rel2 = self.publicar(novas, 2)
        m2 = vp.buscar_manifesto(rel2)
        self.assertEqual([p["nome"] for p in vp.partes_pendentes(m2, destino)], ["vozes-parte-a.zip"])
        self.srv.hits.clear()
        r = vp.instalar(m2, rel2, destino)
        self.assertEqual(r["baixadas"], 1)
        self.assertEqual({c for c, _ in self.srv.hits}, {"/v2/vozes-parte-a.zip"})
        self.assertEqual((destino / "a00000000001.mp3").read_bytes(), novas["a00000000001.mp3"])
        self.assertEqual(vp.versao_instalada(destino), 2)

    def test_nao_apaga_vozes_locais_fora_do_manifesto(self):
        rel = self.publicar(FALAS, 1)
        destino = self.fazer_vozes(self.tmp / "vozes", {"zzlocal.mp3": b"meu"})
        (destino / "elenco.csv").write_text("x")
        vp.instalar(vp.buscar_manifesto(rel), rel, destino)
        self.assertEqual((destino / "zzlocal.mp3").read_bytes(), b"meu")
        self.assertTrue((destino / "elenco.csv").exists())

    def test_nada_pendente_se_arquivos_ja_conferem(self):
        rel = self.publicar(FALAS, 1)
        m = vp.buscar_manifesto(rel)
        destino = self.fazer_vozes(self.tmp / "vozes", FALAS)
        self.assertEqual(vp.partes_pendentes(m, destino), [])
        self.assertEqual(vp.tamanho_pendente(m, destino), 0)


class TestSincronizar(Base):
    def chamar(self, cfg, pasta, resposta=True, forcar=False, api=None):
        perguntas, msgs = [], []
        r = vp.sincronizar(pasta, cfg, lambda t, m: perguntas.append(m) or resposta,
                           lambda t, f: msgs.append(t), api or self.url + "/releases", forcar)
        return r, perguntas, msgs

    def test_sem_internet_ou_sem_pacote_segue_sem_dublagem(self):
        pasta, cfg = self.tmp / "vozes", self.tmp / "config.json"
        r, perg, _ = self.chamar(cfg, pasta, api="http://127.0.0.1:1/releases")  # porta fechada
        self.assertEqual((r, perg), ("sem-pacote", []))
        r, perg, _ = self.chamar(cfg, pasta)  # servidor ok, nenhum release vozes-v*
        self.assertEqual((r, perg), ("sem-pacote", []))
        self.assertFalse(pasta.exists())

    def test_pergunta_instala_e_depois_fica_atual(self):
        self.publicar(FALAS, 1)
        pasta, cfg = self.tmp / "vozes", self.tmp / "config.json"
        r, perg, _ = self.chamar(cfg, pasta)
        self.assertEqual(r, "instalada")
        self.assertEqual(len(perg), 1)
        self.assertIn(str(len(FALAS)), perg[0])
        self.assertEqual(len(list(pasta.glob("*.mp3"))), len(FALAS))
        r, perg, _ = self.chamar(cfg, pasta)
        self.assertEqual((r, perg), ("atual", []))

    def test_recusa_e_lembrada_ate_forcar(self):
        self.publicar(FALAS, 1)
        pasta, cfg = self.tmp / "vozes", self.tmp / "config.json"
        self.assertEqual(self.chamar(cfg, pasta, resposta=False)[0], "recusada")
        r, perg, _ = self.chamar(cfg, pasta)
        self.assertEqual((r, perg), ("recusada", []))  # não pergunta de novo
        self.assertEqual(self.chamar(cfg, pasta, forcar=True)[0], "instalada")

    def test_versao_nova_atualiza_sem_perguntar(self):
        pasta, cfg = self.tmp / "vozes", self.tmp / "config.json"
        self.publicar(FALAS, 1)
        self.chamar(cfg, pasta)
        self.publicar({**FALAS, "a0000000ffff.mp3": b"nova"}, 2)
        r, perg, _ = self.chamar(cfg, pasta)
        self.assertEqual((r, perg), ("instalada", []))
        self.assertTrue((pasta / "a0000000ffff.mp3").exists())

    def test_erro_de_download_nao_levanta(self):
        rel = self.publicar(FALAS, 1)
        for a in rel["assets"]:
            if a["name"].endswith(".zip"):
                self.srv.files.pop(a["browser_download_url"].replace(self.url, ""))
        r, _, msgs = self.chamar(self.tmp / "config.json", self.tmp / "vozes")
        self.assertEqual(r, "erro")
        self.assertTrue(any("não consegui baixar" in t for t in msgs))
        self.assertIsNone(vp.versao_instalada(self.tmp / "vozes"))


if __name__ == "__main__":
    unittest.main()
