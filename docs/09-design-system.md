# 9. Identidade visual e design system

## 9.1 Conceito

**Nome de trabalho: Vade.** Vem de *vade-mecum* ("vai comigo"), o livro que todo concurseiro
carrega. Promessa: **"a lei seca, viva"**.

Duas personalidades em tensão controlada:
- **Leitura séria**, inspirada em Notion, Obsidian e Linear: o texto legal é sagrado. Tipografia
  serifada, muito respiro, zero distração, citações exatas.
- **Prática como jogo**, inspirada em Duolingo, Chess.com e Brilliant: cor, movimento, recompensa
  imediata e sensação de progresso.

A regra: **quanto mais perto do texto da lei, mais calma a interface; quanto mais perto da prática,
mais viva.**

Mascote: **Capi**, uma capivara de toga. É brasileira, simpática, meme-friendly e nada parecida
com a coruja do Duolingo. Aparece em vitórias, em sequências em risco e em estados vazios, nunca
sobre o texto legal.

## 9.2 Cores (dark-first)

Tokens semânticos; os componentes nunca usam hex direto.

| Token | Dark | Light | Uso |
| --- | --- | --- | --- |
| `--bg` | `#0E1116` | `#FAFAF7` | fundo |
| `--surface` | `#161B22` | `#FFFFFF` | cartões |
| `--surface-2` | `#1F2630` | `#F2F2EE` | elevado, hover |
| `--border` | `#2A3340` | `#E2E2DC` | divisores |
| `--text` | `#E8ECF2` | `#16181D` | texto |
| `--text-muted` | `#9AA6B6` | `#5D6470` | secundário |
| `--primary` (Anil) | `#6C8CFF` | `#3D5BD9` | ações, links, foco |
| `--success` (Mata) | `#34C47C` | `#167A49` | acerto |
| `--danger` (Urucum) | `#FF6B5E` | `#B8321F` | erro |
| `--xp` (Ipê) | `#F5B700` | `#8A6300` | XP, moedas, conquistas |
| `--streak` (Brasa) | `#FF8A2B` | `#AD4F00` | sequência |
| `--law-ink` | `#D9DEE7` | `#22252B` | texto legal (contraste levemente menor, leitura longa) |
| `--revoked` | `#8B96A5` | `#626973` | revogado/vetado (sempre com risco e rótulo) |

**Dificuldade:** 🟢 Básico `--success` · 🟡 Intermediário `--xp` · 🔴 Avançado `--danger` ·
⚫ Especialista `#0A0A0D` com anel prateado `#C9D1D9` (no dark mode, o preto precisa do contorno).

**Ligas:** Bronze `#C07A45` · Prata `#AEB8C4` · Ouro `#F2C14E` · Platina `#7FD1C7` · Diamante
`#6EC1FF` · Mestre `#B07CFF` · Grão-Mestre `#FF5C8A`, com gradiente animado só nas três últimas.

Acessibilidade: todos os tokens acima foram medidos contra `--bg`, `--surface` e `--surface-2` e passam de
4,5:1 (AA) nos dois temas (o menor é 4,78:1). No tema claro, as cores vivas do escuro (ex.: `#F5B700`) só
podem ser **preenchimento** com texto escuro por cima, nunca texto sobre fundo claro (ficariam em 2,6:1); acerto/erro **nunca só por cor** (ícone ✓/✗ +
texto + som opcional); paleta testada para daltonismo (verde/vermelho também diferem em luminância).

## 9.3 Tipografia

| Papel | Fonte | Por quê |
| --- | --- | --- |
| Interface | **Inter** (variável) | legível em tamanhos pequenos, números tabulares para placares |
| Texto legal | **Source Serif 4** | serifa para leitura longa e a sensação de vade-mecum; diferencia a lei da interface |
| Citações e chaves | **JetBrains Mono** | `CP art. 157, §2º, II` e atalhos |

Escala (rem): 0.75 · 0.875 · 1 · 1.125 · 1.25 · 1.5 · 2 · 2.5 · 3.5. Texto legal em 1.125rem /
1.7, largura máxima de 68ch.

## 9.4 Espaço, forma e profundidade

Grade de 4 px; espaçamentos 4·8·12·16·24·32·48·64. Raios: 6 (inputs), 12 (cartões), 20 (sheets),
999 (pílulas). Sombras quase ausentes no dark (elevação por `--surface-2` + borda); no light,
sombras suaves em duas camadas. Ícones Lucide, traço de 1,75.

## 9.5 Movimento

- **Calmo na leitura:** só fades de 120 ms.
- **Vivo na prática:** springs (`stiffness 400, damping 28`). Acerto: o cartão sobe 4 px, o ✓
  desenha o traço e o XP voa até a barra. Erro: tremida horizontal de 6 px e o sheet vermelho com a
  explicação. Combo ≥ 5: chama na borda. Subir de nível: tela cheia com confete (1,2 s, pulável).
- Tudo respeita `prefers-reduced-motion` (troca por fades).

## 9.6 Componentes principais

| Componente | Descrição |
| --- | --- |
| **Dispositivo** | renderiza a árvore do parser: recuo por nível (art → § → inciso → alínea), rótulo em mono, rubrica como sobretítulo, notas como chips ("Redação: Lei 15.397/2026") que abrem a linha do tempo, revogado/vetado riscado com selo; seleção de trecho → "criar flashcard" / "perguntar à IA" |
| **Abas do dispositivo** | Texto · Resumo · Explicação · Flashcards · Questões · Pegadinhas · Jurisprudência · Histórico · Mapa |
| **Paleta de comandos ⌘K** | estilo Linear/Arc: entende "art 157 cp", "5º LXXIII", "LGPD 7", siglas, temas; ações ("revisar agora", "simulado PF") |
| **Flashcard** | flip 3D; 4 botões FSRS com a próxima data ("Bom · 11 d"); atalhos 1–4 |
| **Questão** | múltipla escolha (A–E com atalhos), Certo/Errado com dois botões grandes (C/E), lacuna, arrastar, colunas; cronômetro opcional |
| **Sheet de feedback** | bottom sheet verde/vermelho com a explicação, o dispositivo citado e "Continuar" (Enter) |
| **Barra de XP e anel da meta** | anel animado na home; barra de nível com o próximo título |
| **Chama da sequência** | número + chama; estado "em risco" pulsa; protetores visíveis |
| **Insígnia de liga** | escudo com a cor da liga; zona de promoção/rebaixamento na tabela |
| **Mapa de domínio** | treemap de cada norma (tamanho = nº de dispositivos × incidência, cor = domínio); drill-down até o artigo |
| **Heatmap** | calendário anual estilo GitHub |
| **Chat do professor** | respostas com chips de citação clicáveis (abrem o dispositivo ao lado); seletor de nível |
| **Barra de vida do chefe** | Boss Fight: HP do chefe = nota de corte; vidas do jogador; combo |
| **Estados vazios** | Capi + uma ação clara |

## 9.7 Layout

- **Desktop:** barra lateral estreita (Início, Estudar, Revisar, Desafios, Concursos, Estatísticas,
  Liga, Perfil) + conteúdo central + painel direito contextual (IA, jurisprudência, notas), como o
  split view do Arc/Obsidian.
- **Mobile:** barra inferior com 5 itens; sessões de prática em tela cheia; gestos (deslizar para
  avaliar o flashcard, opcional).
- **Modo foco:** esconde tudo exceto o texto legal e o cartão atual.

## 9.8 Voz e tom

Direta, encorajadora, nunca infantil com o Direito. Comemora esforço ("Errar o art. 157 hoje
evita errar na prova"). Termos jurídicos corretos sempre, com linguagem simples ao lado. Sem
culpa na sequência perdida ("Recomeçar também é constância").
