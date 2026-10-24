# Ato VIII — "A Presidência" (um episódio de 2 h, o final do jogo)

Pedido do usuário (23/10/2026): "acrescentar o Ato 8 com um único episódio de 2 h, voltando a ser magistrado do
Supremo, mas agora como Presidente do STF".

## Caminho juridicamente correto até a cadeira
1. **Indicação e sabatina** (CF, art. 101 e parágrafo único; art. 52, III): mais de 35 e menos de 70 anos, notável saber
   jurídico e **reputação ilibada** — é aqui que a censura do CNJ do Ato 7 vira arma dos senadores aliados de Otto.
   Arguição pública na CCJ e voto secreto; aprovação pela maioria absoluta do Senado.
2. **Ministro(a)**; anos depois, **eleito(a) Presidente pelos pares** (regimento interno; tratar só na narrativa).
3. **Presidente do STF e do CNJ** (CF, art. 103-B, § 1º): preside o plenário, organiza a pauta, dirige as sessões,
   proclama resultados — e preside o mesmo Conselho que um dia afastou o(a) protagonista.

## O episódio `a8-presidencia` (ordem 1; papel "juiz"; nivel "impossivel"; `"final": true`) — ≥ 120 min
Estrutura em quatro partes, cada uma com checkpoint natural, fora e dentro do tribunal:
- **Parte I — A Sabatina** (Senado; locais corredor, stf ou tribunal): `plenario` com `"total": 27` (CCJ), maioria 14,
  5–7 senadores jogáveis, cada um com uma preocupação (a censura, a "incompatibilidade", ativismo, garantismo, Otto);
  `blefe` disponível e caro; `celular` (Joana, Dani, Helena); `tensao` na saída do Senado. A resposta certa nunca é
  esconder o erro do Ato 7: é assumi-lo com precisão jurídica.
- **Parte II — A Primeira Sessão como Presidente**: `escolha` de pauta (o que entra primeiro e por quê), `palavra`
  (sustentações orais de 15 minutos por parte, na narrativa), `audiencia` presidindo o plenário (aparte fora de hora,
  ministro que ataca outro, manifestação na galeria, advogado que excede o tempo), proclamação do resultado com
  `escolha`/`argumento` de quórum (CF, art. 97: maioria absoluta para declarar inconstitucionalidade; CF, art. 103-A:
  dois terços para súmula vinculante; empate e ausências). Uma PEC que atinge garantias (CF, art. 60, § 4º, IV).
- **Parte III — A Noite da Crise** (fora do tribunal): ameaça às instituições, gabinete de crise, `tensao` com relógio
  curto, `celular` com Rafael doente; decisões do Presidente dentro dos limites (CF, art. 2º: independência e harmonia
  dos Poderes) — o certo é a contenção firme, não o heroísmo.
- **Parte IV — O CNJ, do outro lado**: como Presidente do CNJ, julgar um(a) juiz(a) jovem que cometeu o mesmo erro de
  boa-fé que você cometeu (advogou na licença). A tentação é a clemência por identificação ou a dureza para "provar
  isenção": o certo é a proporcionalidade motivada (CF, art. 93, X). Mini-drama: o(a) jovem é aluno(a) de Tainá ou
  filho(a) de alguém do Ato 1 (ex.: Lucas, o rapaz do primeiro caso, agora advogado, defende esse juiz).
- **Epílogo e créditos**: veredicto "CARREIRA CONCLUÍDA" com `variantes` pelas marcas da carreira inteira (ver
  a6-voto em `ato6y.json` e as marcas a7_*); fecho em que a frase de Rafael ("leia o artigo até o fim") volta.

Regras de produção: as mesmas do Ato 7 ([ATO7_SEM_TOGA.md](ATO7_SEM_TOGA.md)) e de
[MECANICAS_PAPEIS.md](MECANICAS_PAPEIS.md); arquivo `content/ato8.json`; personagens novos com prefixo `a8`.
O coordenador remove `"final": true` de a6-voto e garante que a7-raiz não o tenha.
