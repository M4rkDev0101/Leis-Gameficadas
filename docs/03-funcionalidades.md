# 3. Funcionalidades

Fase: **MVP** (lançamento), **V1** (≈ 6 meses), **V2** (≈ 12 meses), **ENT** (Enterprise). Ver o roadmap em `06-roadmap.md`.

## 3.1 Tela inicial

| Bloco | Conteúdo | Fase |
| --- | --- | --- |
| Continuar | último dispositivo/sessão com "faltam 6 cartões" e botão único | MVP |
| Meta diária | anel de progresso (XP ou minutos), editável: 10/20/30/60 min | MVP |
| XP, nível, streak | contador, chama de sequência com protetores, aviso "acaba hoje" | MVP |
| Revisões do dia | contagem FSRS de vencidos + "em risco" (R < 80%) | MVP |
| Missões do dia/semana | 3 diárias + 1 semanal, com recompensa em XP e moedas | V1 |
| Liga | posição na liga semanal, zona de promoção/rebaixamento, tempo restante | V1 |
| Últimas leis | 5 últimas normas com % de domínio | MVP |
| Tempo estudado e estatísticas | hoje / 7 dias / heatmap compacto | MVP |
| Alertas legislativos | "Art. 157 do CP alterado pela Lei 15.517/2026, revisar" | V1 |

## 3.2 Navegação e estudo

**Árvore de conteúdo:** Área do Direito → Disciplina → Tema → Subtema → Norma → (Parte/Livro/Título/
Capítulo/Seção) → Artigo → Parágrafo/Inciso/Alínea/Item. Duas portas de entrada:
- **por norma** (estrutura legal, do parser), como num vade-mecum;
- **por tema** (taxonomia de estudo): "Direito Penal › Crimes contra o patrimônio › Roubo".

**Página do dispositivo** (abas):

| Aba | Fonte | Fase |
| --- | --- | --- |
| Texto | parser: texto vigente, rubrica, notas, penas destacadas, revogado/vetado riscado | MVP |
| Resumo IA | batch, verificado | MVP |
| Explicação IA | 3 níveis (do zero / intermediário / avançado) + analogia + exemplo | MVP |
| Flashcards | gerados (lacuna, pergunta-resposta, "qual a pena?") + criados pelo usuário | MVP |
| Questões | geradas por banca/tipo + históricas quando houver | MVP (geradas) / V1 (históricas) |
| Pegadinhas | trocas típicas de banca: prazo, pena, competência, "salvo"/"exceto", vetado/revogado | V1 |
| Jurisprudência | súmulas/teses ligadas (`referencia_legal`) + explicação IA | V1 |
| Histórico | linha do tempo das alterações (notas + versões) | V1 |
| Mapa mental | gerado (JSON → render), editável | V1 |
| Casos práticos | casos concretos com perguntas | V2 |
| Comentários | comunidade moderada + notas pessoais (estilo Obsidian, com backlinks) | V2 |

**Modos de estudo:** Leitura ativa (o texto aparece aos poucos com perguntas de recuperação entre
blocos), Lição (≈ 5 min: 2 cartões novos + 6 revisões + 4 questões intercaladas), Revisão (fila
FSRS), Treino livre (por tema/banca/dificuldade), Desafio, Simulado.

## 3.3 Questões

Tipos: múltipla escolha (A–E), certo/errado (CEBRASPE, com penalidade opcional por erro),
verdadeiro/falso, complete a frase, ordenação, relacionar colunas, arrastar respostas, discursiva.

| Recurso | Fase |
| --- | --- |
| Geração por dispositivo, estilo de banca (CEBRASPE, FGV, FCC, VUNESP, AOCP, IBFC, CONSULPLAN, Quadrix, ESAF histórico) | MVP: CEBRASPE + FGV + FCC; V1: demais |
| Comentário por alternativa citando o dispositivo | MVP |
| Classificação 🟢🟡🔴⚫ dinâmica (`vade_learning.difficulty`) | MVP (regras) / V1 (calibrada por TRI) |
| Banco de questões históricas (banca, ano, órgão, cargo) ligado a dispositivos | V1 |
| Correção de discursiva com rubrica, nota e "o que faltou citar" | V1 |
| Denúncia de erro + fila editorial | MVP |

## 3.4 Flashcards e revisão espaçada

FSRS-5 (`services/learning`): botões Errei/Difícil/Bom/Fácil com a próxima data visível,
retenção-alvo configurável (padrão 90%), registro de tempo, acertos, erros, lapsos e retenção prevista.
Respostas de questões também viram revisões (`grade_from_answer`). Otimização dos pesos por usuário
com ≥ 1.000 revisões (V1). Cartões são agrupados por dispositivo: "dominar o art. 157" significa
todos os cartões do artigo com R ≥ 90% e estabilidade ≥ 21 dias.

## 3.5 Gamificação

| Elemento | Regra-base | Fase |
| --- | --- | --- |
| XP | por dificuldade (10/15/25/40), combo até 2x, bônus de revisão no prazo, XP de esforço ao errar, teto diário suave | MVP |
| Níveis | curva quadrática (`xp_for_level`) + títulos ("Estagiário", "Bacharel", "Doutrinador"…) | MVP |
| Streak | data local, protetores de sequência, marcos de 7/30/100/365 dias | MVP |
| Conquistas/badges | ex.: "Constitucionalista" (CF 100% dominada), "Madrugador", "Sem erro no Art. 5º" | V1 |
| Missões | diárias (3), semanais (1), de evento | V1 |
| Moedas e loja | protetores de sequência, skins, avatares, temas, molduras; **nada que compre vantagem em ranking** | V1 |
| Ligas | Bronze → Prata → Ouro → Platina → Diamante → Mestre → Grão-Mestre; 30 por liga; sobem 7, descem 5 | V1 |
| Rankings | amigos, nacional, por concurso, por UF | V1 |
| Desafio | cronômetro, vidas (3), combo, multiplicador de XP | V1 |
| Boss Fight | o chefão é uma prova inteira: barra de vida do chefe = nota de corte; derrota = plano de reforço | V2 |
| Eventos e temporadas | temporada de 8–10 semanas com tema ("Mês do Penal"), passe sazonal cosmético | V2 |
| Duelos 1x1 com amigos | assíncronos | V2 |

## 3.6 Análise do usuário

Pontos fortes e fracos por área/tema/dispositivo (taxa de acerto ajustada pela dificuldade);
**artigos esquecidos** (R < limiar); **probabilidade de esquecer** cada conteúdo (1 − R, direto do
FSRS); leis pouco estudadas em relação ao peso no edital; áreas críticas (peso alto × domínio
baixo); **previsão de desempenho**: nota esperada no simulado do concurso alvo = Σ peso × P(acerto)
por tópico, com intervalo de confiança. MVP: fortes/fracos + esquecidos. V1: previsão.

## 3.7 Mapa de progresso

Grade com CF, CP, CC, CPP, CPC, CLT, CTN, CDC, LGPD, Maria da Penha, Drogas, ECA, Estatuto da
Pessoa Idosa, Licitações, Improbidade, 8.112 etc. (catálogo em `classify.KNOWN`), mais "Demais leis".
Cada uma com % = dispositivos dominados ÷ dispositivos estudáveis (sem revogados/vetados),
ponderada pela incidência. Drill-down até o artigo. MVP.

## 3.8 Concursos, plano de estudos e Radar

- **Seleção de concurso/cargo** (PF, PRF, PCMG, TJMG, INSS, TRT, Receita, MP, BB, Caixa…), com
  banca, data, edital. Catálogo curado no MVP (≈ 20 concursos); V1 com ingestão de editais por IA
  (edital PDF → tópicos → mapeamento a temas/dispositivos → revisão humana).
- **Plano personalizado:** entrada = cargo, concurso, banca, horas/semana, data da prova, nível
  (teste de nivelamento de 15 min). Saída = cronograma semanal com disciplinas prioritárias
  (peso × fraqueza × incidência), questões/dia, revisões FSRS reservadas, simulados quinzenais,
  treinos discursivos. Replaneja sozinho quando o usuário atrasa. MVP: versão por regras; V1: otimizada.
- **Radar de Concurso:** assuntos e artigos mais cobrados (por banca, cargo, período), tendência
  (crescimento nos últimos 3 anos), peso no edital, probabilidade de cobrança, prioridade sugerida.
  Depende do banco histórico (V1). No MVP, o Radar mostra o peso do edital e as heurísticas editoriais.

## 3.9 Simulado real

Quantidade real de questões, tempo, pesos, regras da banca (CEBRASPE: uma errada anula uma certa),
dificuldade calibrada; análise pós-prova (por disciplina, por dispositivo, tempo por questão,
"chutes"); comparação com a nota de corte histórica quando houver. V1.

## 3.10 Busca inteligente

Filtros: número da lei, artigo ("art 157 cp", "5º LXXIII CF"), tema, palavra, expressão exata,
órgão, UF, município, ano, tipo, situação (vigente/revogada), ementa. Atalhos por sigla e nome
popular ("LGPD", "Maria da Penha"). Sem acento e com tolerância a erro. Resultados agrupados
(Dispositivos | Normas | Jurisprudência). Busca semântica ("quais artigos tratam de legítima
defesa?"). MVP: FTS + siglas + parser de citações; V1: semântica.

## 3.11 Modo IA (professor)

Explica do zero ou em nível avançado, adapta ao nível do aluno, cria exemplos e analogias, compara
conceitos ("furto × roubo" com tabela lado a lado e os dispositivos), corrige discursivas e avalia
justificativas, cria pegadinhas, indica o que estudar depois (a partir do grafo + fraquezas). Sempre
com citações clicáveis. MVP: explicar, comparar, perguntar sobre um dispositivo. V1: correção de
discursiva, recomendações. V2: tutor proativo (planeja a sessão).

## 3.12 Estatísticas

Tempo estudado, questões respondidas, taxa de acerto, leis concluídas, artigos dominados, XP
diário, calendário, heatmap anual (estilo GitHub), curvas de retenção, distribuição de dificuldade. MVP (básicas) / V1 (completas).

## 3.13 Enterprise (B2B)

Turmas para cursinhos e órgãos, painel do professor, trilhas customizadas, SSO (SAML/OIDC),
relatórios por aluno, API, white-label, conteúdo próprio do cliente. ENT.
