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

## Notas de ambiente (descobertas que custaram tempo)
- Agentes: `isolation: worktree` falha (MAX_PATH). Criar `git worktree add -b equipe/<x> C:/lx/wt-<x>` e mandar o
  agente trabalhar só lá, com porta própria (878x). Agentes Sonnet/Haiku com skills; coordenador revisa e integra.
- Testes no navegador: use 127.0.0.1 (localhost soma ~200 ms por requisição no Windows); aba oculta trava rAF.
- Windows MAX_PATH: scripts e clones em `C:/lx/`; o grafo do graphify fica em `C:/lx/vgc`.
- O executável do jogo sem console tem `sys.stderr = None` (já tratado).
