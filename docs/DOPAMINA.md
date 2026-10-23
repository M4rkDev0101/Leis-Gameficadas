# Laço de recompensa honesto (DOPAMINA)

Meta: o jogo dar vontade de "só mais um caso", sendo educativo e gratuito. **Linhas vermelhas:** sem compra, sem
moeda paga, sem notificação, sem punição por ausência (a sequência pode zerar, mas nada se perde: nota, cartas,
XP e nível ficam), sem contagem regressiva nem evento que expira, sem loot "perde-tudo". Toda recompensa vem de
**aprender** (acertar a lei, achar a contradição) ou de **jogar bem** (poucos erros). Tudo é calculado no servidor,
com tetos; o cliente só informa fatos (erros, combo, tempo) que são limitados.

## 1. Auditoria: o que já existia
- **XP e nível** (`learning/gamification.py`, `player.py`): XP por caso (`tribunal.score`: base do nível + duração
  + 20/balança + 60 se perfeito); nível por curva quadrática; 9 patentes (Estagiário até Ministro) só como texto no perfil.
- **Sequência**: `Streak` com "protetores" (começava com 1 e **nunca era reposto**). Ligas e moedas existem só como
  funções puras, sem uso no jogo local. Combo existe só no simulado (`exam.grade`), não no tribunal.
- **Conquistas**: 11+ calculadas do histórico, sem progresso nem raridade. **Nota por caso**: só `melhor` (0-1) e perfeito (0 erros).
- **FSRS**: existe em `services/learning`, não ligado ao tribunal. Dicas: automáticas após 2 erros (cliente).
- **UI** (`tribunal.html`): barra de XP no perfil, `verdict()` mostra carimbo e "+N XP", menu "Conquistas" (lista plana).

## 2. Laço de recompensa
| Escala | O que o jogador sente |
|---|---|
| Segundos | acerto de prova/lei: som + combo `x3`; cartas de lei aparecem no popup (já existe `lawPopup`) |
| Caso (10-25 min) | veredicto: **nota S/A/B/C**, XP com combo, baú de autos, cartas novas, recorde |
| Sessão | desafio do dia (3 questões, ~2 min) fecha a sessão; sequência sobe; patente nova com cerimônia |
| Longo prazo | álbum de 287 cartas, selos dourados, conquistas com barra, 5 atos, patente Ministro |

## 3. Sistemas (prioridade por impacto/esforço; 1-6 implementados no backend)
1. **Nota por caso (S/A/B/C)** e recorde. Gatilho: concluir o caso. S = 0 erros; A = 1; B = 2-3; C = mais (venceu).
   Recompensa: nota, recorde pessoal (nota, erros, melhor tempo), selo dourado permanente ao tirar S, **+15 XP por
   degrau** que melhora ao rejogar. Honesto: tempo é só recorde, não entra na nota (ler devagar não é defeito); nota
   ruim nunca é regravada para baixo. Aceite: `TestPlayer.test_nota_recorde_e_bonus_de_melhora`.
2. **Combo** de acertos seguidos no julgamento. O cliente conta e envia `combo_max`; bônus = +2% do XP do caso por
   acerto, **teto +20%** (10). Quebrar o combo só zera o contador (feedback na UI), nunca tira XP. Derrota não paga bônus.
   Aceite: `test_combo_paga_com_teto_e_derrota_nao_paga`, `test_entrada_do_cliente_e_limitada`.
3. **Cartas de jurisprudência / álbum.** Gatilho: vencer o caso. Entram no álbum os dispositivos que o caso exige
   (287 no total; raridade comum/incomum/rara/épica = clássico citado em 2+ casos, ou pelo caso mais difícil que o cita).
   Caso nota S dá carta **dourada** (e promove cartas já tidas). O texto da lei só aparece nas cartas conquistadas
   (curiosidade honesta: o álbum vira revisão). Aceite: `test_cartas_so_na_vitoria...`, `test_album_esconde...`.
4. **Baú de autos** (variável moderada). Ao vencer, sempre abre: 70% "comum" (nada extra), ~25% "bom" (+15 XP),
   8-20% "raro" (+40 XP e uma carta já tida vira dourada). A chance sobe com a nota (jogar bem), mas todos têm.
   Semente = id da partida (auditável), nunca perde nada, uma vez por partida (reenviar não repete). Aceite: `test_bau_*`.
5. **Conquistas com progresso e raridade** (`progresso {atual, meta}`, `raridade`): as antigas ganham barra ("7/10");
   novas: Olho clínico (10 contradições), Inquisidor (50), Sem piscar (combo 8), Selos (5 notas S), Jurisprudência
   (25 cartas), Biblioteca completa, Uma semana de toga, Relâmpago (10 desafios do dia). Aceite: `test_conquistas_*`.
6. **Desafio do dia + folga semanal.** 3 questões do banco de 841 (básica, intermediária, avançada/especialista),
   iguais para todos, determinísticas pela data. Cada acerto +10 XP (erro +2), fechar as 3 +20 XP; conta para a sequência.
   Sem hora limite, sem "perdeu o desafio de ontem". **Folga**: +1 protetor grátis por semana (máx. 2) cobre 1 dia sem
   jogar automaticamente. Aceite: `test_dia_*`, `test_folga_*`.
7. **Patentes com cerimônia**: `progresso.patente_nova` e `perfil.proxima_patente {titulo, nivel, faltam_xp}` (backend pronto;
   a cerimônia é só UI). Aceite: `test_patente_nova_e_proxima`.
- **Fora desta rodada:** pergunta-relâmpago dentro do caso e revisão FSRS das cartas (próximo passo natural: carta errada no dia = reaparece).

## 4. Migração e persistência (`jogador.sqlite`)
Tabelas novas por `CREATE TABLE IF NOT EXISTS`: `nota_caso`, `carta`, `contador`, `dia_resposta`; coluna `jogador.protetor_semana`
via `ALTER` idempotente. Saves antigos abrem sem perda (`test_save_antigo_migra_sem_perder_dados`).

## 5. API (JSON; POST exige o cabeçalho `X-Vade: 1`)
- `POST /api/arena/tribunal/concluir` `{episodio, credibilidade, erros, marcas, combo_max?, certeiras?, segundos?}` -> o resultado de
  antes mais `nota` e `recompensas {nota, combo_max, xp_combo, xp_melhora, xp_bau, bau: comum|bom|raro, recorde{nota_anterior,
  melhorou_nota, melhorou_tempo, primeira_vez, tempo_s, selo_dourado}, cartas_novas[{chave,raridade,dourada}], carta_dourada}`.
  `xp` já inclui os bônus. `progresso` ganha `patente_nova`, `protetores`, `protetor_usado`, `recompensas`.
- `GET /api/arena/carreira`: `conquistas[]` com `progresso`/`raridade`; novo `notas {ep_id: {nota, erros, segundos, vezes}}`.
- `GET /api/arena/album`: `{cartas[{chave, raridade, ok, dourada, casos, rotulo?, texto?, norma?}], total, ok, douradas, por_raridade}`.
- `GET /api/arena/dia`: `{dia, questoes[], feitas, total, completo, xp_acerto, xp_completo, streak, protetores, dias_completos}` (sem gabarito até responder).
- `POST /api/arena/dia/responder` `{questao, resposta}` -> `{correta, gabarito, explicacao, pegadinha, fundamentos[], progresso{xp, completo, feitas, streak...}}`.
- `GET /api/arena/perfil`: novo `proxima_patente`; `protetores` agora repõe 1 por semana.

## 6. Pontos de UI para a fase de interface (`tribunal.html`)
- **Contadores no `G`** (criado em `startEpisode`, ~l.2337): `G.combo`, `G.comboMax`, `G.certeiras`, `G.t0 = Date.now()`. Acerto em
  `damage`/ramos de acerto (ex.: `lawPopup`, ~l.1962-2000): `G.combo++`; erro (`G.erros++`, l.1963): `G.combo = 0` + som/aviso "combo quebrado".
  Contradição acertada em `depoimento` (~l.2183): `G.certeiras++`. HUD: chip `x3` perto da credibilidade, cresce até x10.
- **`finish()` (~l.2269)**: enviar `combo_max:G.comboMax, certeiras:G.certeiras, segundos:Math.round((Date.now()-G.t0)/1000)`.
- **`verdict()` (~l.2273)**: sequência de revelação com `r.recompensas`: carimbo -> nota grande (S dourada) -> "+XP" somando combo/melhora ->
  baú abrindo (`bau`) -> cartas novas viradas uma a uma (cor por raridade) -> faixa "NOVO RECORDE" se `melhorou_nota/tempo`.
  Se `progresso.patente_nova`: tela de cerimônia da patente (`progresso.titulo`). Sons: `Sound.vitoria` (já), novo stinger por nota S, "virar carta", "baú".
- **Menu da carreira** (~l.2690-2723): nota (S/A/B/C) em cada capa de caso (`car.notas`), selo dourado no S; conquistas com barra e cor por
  `raridade`; novo cartão "Desafio do dia" no `hero` (`/api/arena/dia`) e seção "Álbum" (`/api/arena/album`) ao lado de Conquistas.
- **Perfil** (`#btn-avatar`, ~l.2683): tooltip com `proxima_patente`; ícone de folga (`protetores`) e aviso gentil, nunca ameaçador, na sequência.
- Sons que merecem evento: acerto encadeado (sobe de tom até x10), combo quebrado (suave, sem buzina), nota S, carta virando, baú raro, patente. Nenhum som para "ausência".
