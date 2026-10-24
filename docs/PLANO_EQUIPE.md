# Plano de trabalho da equipe

Plano operacional (quem faz o quê, em que ordem, com que critério de aceite). O roadmap de produto está em
[ROADMAP.md](ROADMAP.md). Depois de um `/clear`, comece por aqui: leia este arquivo, `docs/ARCHITECTURE.md`,
`git log --oneline -15` e `git status`, e continue pela primeira tarefa que não está ✅.

## Papéis

| Papel | Quem | Escopo |
| --- | --- | --- |
| Direção técnica / arquitetura | coordenador (modelo de raciocínio) | plano, decisões, integração, revisão, commits |
| Programação | agente (modelo especialista) | motor, servidor, ferramentas, testes |
| Game design | agente | progressão, dificuldade, recompensas |
| Narrativa | agentes por ato (modelo rápido) | casos, diálogos, personagens, escolhas |
| Arte | agente (modelo especialista) | personagens, cenários, interface |
| Áudio | agente | trilha, efeitos, ambiência |
| QA | agente + coordenador | testes funcionais, visuais, gameplay, performance |

Regras: agentes não comitam (o coordenador revisa, testa e comita em commits separados: `feat:`, `fix:`,
`art:`, `audio:`, `docs:`, `refactor:`); um agente por arquivo/trecho por vez; nada vai para `main` sem
testes (`unittest`), validação jurídica (`jogar.py validar`) e jogo no navegador (`tools/autoplay.js`).

## Fila (ordem de execução)

| # | Tarefa | Responsável | Critério de aceite | Estado |
| --- | --- | --- | --- | --- |
| 1 | Documentação base (GDD, roadmap, changelog, licenças, arquitetura) | docs | 5 arquivos coerentes com o código | ✅ |
| 2 | Trilha e efeitos sintetizados (6 temas, efeitos, ambiência) | áudio | sem erros; volume equilibrado; toggles funcionam | ✅ |
| 3 | Personagens: correção rígida (olhos × óculos, camadas de cabelo, braços/mãos, avental, proporções) + galeria `?galeria=1` | arte (QA rígido) | varredura completa da galeria com ZERO defeitos, 127 visuais × 9 expressões, dentro do jogo também | 1ª passada ✅ (quepe, costeletas, cabelo longo, topete, cachos, mangas, mãos, barba, sobrancelhas); falta 2ª passada expressão por expressão em todo o elenco |
| 4 | Cenários: mesmo rigor do item 3 para tribunal (5 posições), escritório e 12 locais; galeria de cenários com os pontos de investigação desenhados por cima | arte (QA rígido) | zero defeitos; todo ponto clicável cai sobre o objeto certo; personagem legível em todos | a fazer |
| 5 | Interface: menu, título, diálogo, autos, investigação, veredicto, créditos em 1366×768, 1920×1080 e celular (375×812) | arte + QA | sem corte, sem sobreposição, contraste AA, foco visível | ✅ desktop (1366/1920); celular descartado pelo usuário |
| 6 | Dublagem local (VoiceStudio/OmniVoice): perfis + todas as falas exceto o protagonista | áudio (processo em segundo plano) | todas as falas com mp3; amostras transcritas batem com o texto; NENHUMA voz repetida (pedido do usuário) | removido pelo usuário |
| 7 | Mixagem voz × música (abaixar música durante a fala dublada; `erro()` ligado; música volta a `calma` após investigar) | áudio | nenhuma fala encoberta | ✅ (nó `musDuck`, -10 dB) |
| 8 | QA de gameplay completo: os 43 casos + avulsos, com erros propositais, game over, salvar/continuar, rejogar escolhas, conquistas, créditos | QA | nenhum travamento; salvamento e marcas corretos | parcial ✅: 46/46 episódios até o veredicto sem erro de console; game over e salvar/continuar ok (a1-pao, a3-posse, a5-excecao). Falta: rejogar escolhas, conquistas, créditos. Nota: `?ep=` recomeça e apaga o save (só o “Continuar” do menu retoma) |
| 9 | Performance: tempo de carregamento do menu (hoje ~2 s com 45 cartões), FPS das animações, tamanho do HTML | programação | menu < 1 s; animações suaves | ✅ (capas sob demanda: ~30 ms até o 1º quadro) |
| 10 | Personagens: personalidade e bio no conteúdo (campo `bio`, motivação) e na tela de autos/elenco | narrativa | todo personagem principal com bio | ✅ aba Elenco nos autos; bios sem spoiler em andamento (segredos → campo `segredo`) |
| 10b | Caso tutorial `a1-tutorial` antes do Caso 1 | narrativa + game design | ensina todas as mecânicas; passa no autoplay | ✅ |
| 11 | Game design: balanceamento de dificuldade e XP por ato; dicas após 2 erros | game design | curva revisada e documentada no GDD | ✅ (XP por duração, 6 rótulos corrigidos, dicas progressivas) |
| 12 | Instalador: incluir dublagem opcional (baixar pacote de vozes) | programação | instalação limpa funciona | ✅ código e lançador novo publicados (instalação limpa testada em 30 s); o instalador não baixa mais vozes (dublagem removida) |

## Em andamento (23/10/2026) — retomar daqui
Meta do usuário: "o melhor jogo de advogado do mundo", viciante (AAA) sem padrões predatórios. O usuário testa o jogo
pessoalmente: agentes NÃO jogam episódios (só unittest, `jogar.py validar`, carga sem erro de console).
- Já na main: desempenho (perf2), game feel (juice, docs/FEEL_TUNING.md), trilha (audio, GDD §9), recompensas backend
  (loop, docs/DOPAMINA.md), ganchos e mistério "A Carta de Paulo" (gancho, docs/NARRATIVA_GANCHOS.md), motor do Ato 6.
- Integrados em 23/10: Ato 6 "Supremo" (15 casos; epílogo e créditos no fim de a6-voto), testemunha comprada em 11
  casos dos atos 1–5, juiz Sérgio Quadros (ato 3) e Min. Ataulfo (ato 6), interface das recompensas (combo, nota S–C,
  baú, cartas, patente, álbum, desafio do dia, conquistas, argumento como cartas). Total: 59 casos, ~21,9 h.
- Próximo: aguardar os bugs que o usuário reportar; 2ª passada de arte (item 3); revisão jurídica dos pontos marcados
  em docs/NARRATIVA_GANCHOS.md (Lei 8.906, 9.296 e CPP 158-A–F fora do catálogo; perda de mandato CF 55).
- `C:/lx/wt-antivirus` (equipe/antivirus, não comitado): PyInstaller --onedir + Inno Setup, Defender limpo; falta o
  teste de instalação limpa (o jogo do usuário aberto travou o setup; um `VadeTribunal.tmp` ficou preso). Usar
  PowerShell ou MSYS_NO_PATHCONV=1 para os flags do setup.

## Frente "cada papel no seu papel" (23/10/2026, tarde) — retomar daqui
Pedidos do usuário nesta sessão (autorização total para trabalhar sozinho): (1) na Toga o jogador agia como acusação,
não como juiz; (2) "undefined" ao mostrar lei; (3) mecânicas próprias para advogado, promotor, juiz e Supremo;
(4) mais história, complexidade crescente e cenários novos condizentes; (5) histórias fora do tribunal (provocações,
perseguições) sem cansar; (6) casos de voto popular (júri) com atenção redobrada; (7) mini-dramas: personagens para
amar e odiar, quebra de confiança, decepção; (8) mais efeitos, música "de verdade", momentos de tensão;
(9) interface com cara de jogo; (10) commits sempre e tudo anotado aqui.

| # | Tarefa | Estado |
| --- | --- | --- |
| P1 | Corrigir "undefined" (pop-up de fundamento recebia prova, não lei) | ✅ |
| P2 | Motor: `audiencia`, `palavra`, `sentenca` (juiz), `protesto` (partes), `denuncia` (promotor), `plenario` (STF e júri), `tensao` e `celular` (fora do tribunal), efeito `ordem`, depoimento em modo juiz. Spec: [MECANICAS_PAPEIS.md](MECANICAS_PAPEIS.md) | ✅ testado no navegador com fixtures (`tests/papeis_fixture.py`) |
| P3 | Ato 4 (Toga): 9 casos reescritos + 3 novos (custódia, vítima/400-A, júri); arco de Rita | ✅ integrado (0c1b9bf) |
| P4 | Ato 3 (promotor): denúncia, ANPP/arquivamento, protesto, júri pela acusação, arco de Valadares, 3 casos novos | ✅ integrado (f92aec3) |
| P5 | Atos 1–2 (advogado): protesto, ética do cliente, arcos de Rafael/Sofia/Helena/Lívia, 3 casos novos | ✅ integrado |
| P6 | Ato 5 (juiz) e Ato 6 (STF): tom de juiz, plenário de ministros, traição de Teresa, 2 casos novos | ✅ integrado (52b4550) |
| P7 | Arte: 10 cenários novos com QA rígido pessoal | ✅ integrado (e357ff5); 4 correções do QA pessoal ✅; detalhe pendente: no corredor as longarinas ficam na frente da base das portas (mover para entre as portas) |
| P8 | Áudio: trilha mais rica, 8 temas novos, efeitos e ambiências | ✅ integrado (d25c942); pendente: ouvir o volume das ambiências carro e cemitério |
| P9 | Interface com cara de jogo | ✅ integrado (cd3c07e); pendentes do agente: veredicto não revisto, motivo do botão de assinar desabilitado, menu comum ainda cobre o rosto |
| P10 | Arcos de personagem/mini-dramas atravessando os atos (traição, decepção, aliados) | dentro de P3–P6, coordenado por docs/NARRATIVA_GANCHOS.md |
| P7b | QA de arte dos personagens novos (a3y*, a4z*, a6zm*, a5oficial, a7*) | amostra dos ministros ✅; varredura completa pendente |
| P11 | Ato 7 "Sem Toga": 10 episódios de 1 h+ (10,7 h), nível impossível, desvio por marca no ep. 9 | ✅ integrado; nomes ajustados contra colisões; falta jogar no navegador (servidor de preview indisponível na sessão) |
| P13 | Ato 8 "A Presidência": episódio único de 2 h (126 min) com epílogo e créditos | ✅ integrado |
| P12 | Fim do jogo movido para o Ato 8; a6-voto fecha o Ato 6 com o gancho da queda | ✅ |


Limite de uso: com 13 agentes em paralelo a cota acaba antes de qualquer um terminar. Retomar em lotes de 5 (SendMessage ao agente, que continua de onde parou). Lote 1 (24/10): toga, mp, adv, supremo, a7a. Lote 2: a7b, a7c, a7d, a7e, a8.

Estado em 24/10: 81 casos, ~40,5 h (Ato 1 2,9 h · 2 3,6 · 3 4,6 · 4 4,3 · 5 3,0 · 6 9,2 · 7 10,7 · 8 2,1). Pendentes: jogar no navegador os casos novos (o servidor de preview ficou indisponível), QA de arte dos personagens novos, detalhe do corredor, volume das ambiências carro/cemitério.

## Notas de ambiente (descobertas que custaram tempo)
- Agentes: `isolation: worktree` falha (MAX_PATH). Criar `git worktree add -b equipe/<x> C:/lx/wt-<x>` e mandar o
  agente trabalhar só lá, com porta própria (878x). Agentes Sonnet/Haiku com skills; coordenador revisa e integra.
- Testes no navegador: use 127.0.0.1 (localhost soma ~200 ms por requisição no Windows); aba oculta trava rAF.
- Windows MAX_PATH: scripts e clones em `C:/lx/`; o grafo do graphify fica em `C:/lx/vgc`.
- O executável do jogo sem console tem `sys.stderr = None` (já tratado).
