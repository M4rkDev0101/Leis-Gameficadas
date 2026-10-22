# Dublagem opcional no instalador

A dublagem (mp3 em `%LOCALAPPDATA%\VadeTribunal\vozes`, ~3,8 mil falas) **não vai para o git**. Ela é distribuída
como assets de um GitHub Release com tag `vozes-vN` (N = 1, 2, 3...). O jogo já toca os mp3 dessa pasta quando
existem (`/api/arena/vozes`); sem eles usa os bipes. Nada em `tribunal.html` mudou.

## Como o lançador usa

`vade_launcher.py` -> `sync_vozes()` (depois da importação das leis, antes de abrir o servidor):

1. consulta `api.github.com/repos/M4rkDev0101/Leis-Gameficadas/releases` e escolhe a maior tag `vozes-vN`
   publicada (ignora rascunho/pré-release). Sem internet, sem release ou manifesto inválido: segue sem dublagem, em silêncio.
2. 1ª vez: pergunta "Baixar a dublagem (~X MB)?". Recusar grava `config.json` (`"vozes":"recusou"`) e não pergunta
   mais; `VadeTribunal.exe --vozes` pergunta de novo.
3. Aceitou: baixa só as partes (zips) que têm arquivo ausente/diferente, com barra de progresso, retomada (`Range`,
   arquivo `.part`) e verificação sha256 do zip e de cada mp3; extrai com troca atômica. Falha de rede = tenta de novo
   (3x) e, se persistir, avisa e o jogo abre mesmo assim; a próxima abertura retoma de onde parou.
4. Versão nova (`vozes-v2`...): atualiza sozinho (já aceitou), baixando só as partes cujos mp3 mudaram. A versão
   instalada fica em `vozes\pacote_vozes.json`. Mp3 locais que não estão no manifesto nunca são apagados.

Variáveis para teste: `LOCALAPPDATA` (pasta base), `VADE_VOZES` (pasta de vozes), `VADE_VOZES_API` (URL da lista de releases).

## Formato do release

- `vozes-manifesto.json`: `{formato, versao, tag, total_arquivos, tamanho_total, partes:[{nome, tamanho, sha256, arquivos:{"<id>.mp3":{sha256,tamanho}}}]}`
- `vozes-parte-<prefixo>.zip`: mp3 na raiz, agrupados pelo 1º caractere do id (16 partes; subdivide em 2 caracteres se
  uma parte passar de ~1,8 GB, limite de 2 GiB do GitHub). Zip determinístico (conteúdo igual = sha256 igual).

## Gerar e publicar (publicar só com autorização do usuário)

```powershell
python instalador\gerar_pacote_vozes.py --vozes "$env:LOCALAPPDATA\VadeTribunal\vozes" --saida C:\lx\pacote-vozes --versao 1
# conferir o tamanho/qtd impressos; depois, SOMENTE com autorização:
gh release create vozes-v1 C:\lx\pacote-vozes\vozes-manifesto.json (Get-ChildItem C:\lx\pacote-vozes\vozes-parte-*.zip).FullName `
  --repo M4rkDev0101/Leis-Gameficadas --title "Vozes v1" --notes "Pacote de dublagem v1"
```

Versão nova: gere com `--versao 2` a partir da pasta atualizada e publique como `vozes-v2` (o release antigo pode ficar).
Gere o pacote só quando o processo de geração de vozes tiver terminado (o gerador lê os mp3 da pasta).

## Testes

`services/arena/tests/test_instalador_vozes.py` (19 testes, servidor HTTP local com Range): manifesto, rejeição de
nomes com caminho/sha inválido, retomada após queda, servidor sem Range, corrupção, atualização incremental, recusa
lembrada, sem internet.
