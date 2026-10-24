# Ato VII — "Sem Toga" (bíblia do ato)

Pedido do usuário (23/10/2026): "a Altavista conseguiu nos tirar do Supremo através de alguma denúncia, ou porque atuamos
como advogado sem ter licença; agora temos que reconquistar a confiança — algo literalmente à margem do impossível,
cada episódio com pelo menos 1 h, 10 episódios, extremamente complexo e difícil".

## Premissa (e por que ela é juridicamente honesta)
No Ato 6 o(a) protagonista pediu "licença da toga" e advogou para as famílias, voltando à toga só como juiz(a)
instrutor(a) convocado(a). **Isso é vedado**: o juiz não pode exercer outro cargo ou função "ainda que em
disponibilidade, salvo uma de magistério" (CF, art. 95, parágrafo único, I), e o Estatuto da OAB declara a advocacia
incompatível com a magistratura (Lei 8.906 fora do catálogo: tratar só na narrativa, sem citar artigo). A falha foi
real, de boa-fé, empurrada por aliados e pela urgência — e a Altavista a encontrou.

Consequências que o jogador enfrenta:
1. **Disciplinar:** reclamação no CNJ (CF, art. 103-B, § 4º, III), afastamento cautelar, processo administrativo
   disciplinar com contraditório (CF, art. 5º, LV; Lei 9.784, arts. 2º, 3º, 38, 44, 46), julgamento em sessão pública e
   motivada (CF, art. 93, X).
2. **Processual:** a defesa de Otto pede a nulidade da condenação porque o(a) protagonista atuou como assistente
   (CPP, arts. 268 e 271). A resposta jurídica é fina: **não há nulidade sem prejuízo** (CPP, art. 563), a parte não
   pode arguir nulidade a que deu causa (art. 565), e não se anula ato que não influiu na verdade (art. 566). O MP era
   o titular; a prova não dependeu do assistente. Mas o jogador precisa PROVAR isso ato por ato.
3. **Pessoal:** imprensa, dinheiro acabando, amigos que somem, quem fica, quem trai.

## Regras de design do ato (valem para os 10 episódios)
- `"ato": "ato7"`, `"nivel": "impossivel"` (decisões com relógio de 40 s por padrão; dicas quase cortadas; XP base 300).
  Use `"tempo"` menor (15–25 s) nos momentos de pressão real.
- **Duração: no mínimo 60 min por episódio** pela estimativa do motor (`tribunal.estimate_minutes`; meça e registre).
  Ordem de grandeza: ~6.000–8.000 palavras de fala, 35–50 decisões, 3 investigações com 4–6 pontos cada.
- **Estrutura em 3 atos internos** com checkpoints naturais (o jogo salva por cena): (I) golpe e investigação,
  (II) confronto principal, (III) virada e decisão final. Cada episódio tem **ao menos 2 reviravoltas**, **1 cena fora
  do tribunal com `tensao`** e **1 com `celular`**, e **1 mini-drama** (afeto, traição, decepção ou perdão).
- Dificuldade "à margem do impossível", mas justa: provas falsas parecidas com as verdadeiras (`analisar`),
  testemunhas que mentem bem (`veracidade` com sinais sutis), depoimentos com 2–3 contradições (`exige`), acareações,
  argumentos com alternativas muito próximas, plenários com 4–6 votos a conquistar, `audiencia`/`protesto` com
  incidentes disfarçados entre falas regulares. Nunca uma resposta que dependa de adivinhar: tudo dedutível dos autos.
- Papel por episódio: `investigado` (1–7: afastado(a), sem toga e sem carteira; defende-se sozinho(a) no PAD, o que a lei
  permite — Lei 9.784, art. 3º, IV; não pode advogar para ninguém; magistério é permitido) e `juiz` (8–10, depois da
  volta, sob vigilância: "atenção redobrada").
- Mecânicas por papel: ver [MECANICAS_PAPEIS.md](MECANICAS_PAPEIS.md). O investigado usa `protesto`, `depoimento`
  (no PAD a defesa inquire), `plenario` (sessões do CNJ: `"total": 15`, maioria 8; ou STF), `analisar`, `investigar`,
  `acareacao`, `argumento`, `intuicao`, `blefe`, `tensao`, `celular`, `escolha` livre. O juiz, as de juiz.
- Locais: use os novos (custodia, stf, promotoria, garagem, carro, casa, corredor, praca, cafe, cemiterio) e os antigos.
- Marcas do ato: prefixo `a7_`. Escolhas livres importantes mudam falas nos episódios seguintes e o epílogo.

## Elenco do ato (ids em `content/ato7.json`; recorrentes nos outros atos)
- **Cons. Marina Paiva** (`a7marina`) — conselheira relatora do PAD no CNJ. Dura, justa, ex-defensora pública. Começa
  convencida da sua culpa; o jogador conquista o respeito dela, não a simpatia.
- **Min. Edgar Lobo** (`a7edgar`) — Corregedor Nacional. Político, preocupado com a imagem do Judiciário; quer um
  exemplo. Antagonista institucional, não vilão: tem um momento humano (o filho dele também errou de boa-fé).
- **Dr. Saulo Prado** (`a7saulo`) — advogado do autor da reclamação. Elegante, cruel na medida exata, ótimo de tribuna.
- **Ronan Teles** (`a7ronan`) — presidente do "Instituto Transparência Viva", testa de ferro que assina a reclamação.
- **Joana Ribas** (`a7joana`) — jornalista investigativa. Primeiro publica o dossiê contra você; depois descobre que foi
  usada e vira aliada relutante (quebra de confiança ao contrário).
- **Tainá Rocha** (`a7taina`) — aluna do curso noturno onde você passa a dar aula (magistério é permitido). Mãe solo,
  caso trabalhista dela vira o coração do episódio 5. A pessoa que faz o jogador lembrar por que entrou no Direito.
- Recorrentes: Dani (traição dolorosa: foi ela quem cuidava do seu token de assinatura digital), Helena (culpa: foi a
  ideia dela você "ajudar só desta vez"), Rafael (presente que agora protege VOCÊ), Sofia, Clara, Kenji (perito),
  Teresa (`a6teresa`, PGR), Min. Helga (`a6helga`), Min. Ataulfo (`a6ataulfo`), Hugo Freitas Lopes (`a6yhugo`,
  advogado de Otto), Delegado Nery (`a6nery`), **Bento Carvalho** (`bento`, o escrivão discreto do Ato 1 — o arquivista
  que anotou a sua vida desde o primeiro caso e a vendeu), Lívia, Brandão, Henrique (da cela).


## Continuidade vinda do Ato 6 (integrada em 24/10)
- **Teresa traiu** (`a6z-virada`, marca `a6z_teresa_traiu`; escolha livre `a6z_levou_helga` / `a6z_deu_prazo` /
  `a6z_usou_teresa`). No Ato 7 ela continua sendo a subprocuradora responsável pela ação de Otto: é ela quem tem de
  defender a condenação (ep. 2) e quem denuncia no fim (ep. 10). O(a) protagonista precisa trabalhar com quem o(a)
  traiu — mini-drama obrigatório: desconfiança, um momento em que ela explica por que fez (sem se absolver) e uma
  reconstrução de confiança, que pode ou não acontecer conforme as escolhas. Use `se` com as marcas acima.
- Bento Carvalho é o id `bento` (escrivão do Ato 1). Ele aparece de relance no Ato 6.
- Sementes plantadas no Ato 6: foto 114 no caderno de Nery (tribuna), token de assinatura com Dani (`a6-grampo`).

## Os 10 episódios
| # | id · título | papel | núcleo jurídico | drama / gancho |
| --- | --- | --- | --- | --- |
| 1 | `a7-queda` · A Queda | investigado | Reclamação no CNJ, afastamento cautelar, CF 95 § ún. I, CF 103-B § 4º III, CF 5º LV; defesa pessoal na sessão (`plenario` 15 conselheiros: você não evita o afastamento, mas conquista o direito a um PAD regular em vez da punição sumária) | Abre na festa da vitória de a6-voto; o celular explode (`celular`); manchete de Joana; Helena some; carro na garagem (`tensao`); fecho: "Ministro Ataulfo pediu vista do seu caso — e almoçou com Hugo." |
| 2 | `a7-nulidade` · Sem Prejuízo | investigado | HC/revisão da defesa de Otto (CPP 647, 621) pela nulidade; CPP 563, 565, 566, 268, 271: você não pode advogar — monta para Teresa a prova de que nenhum ato seu influiu (`analisar` ato a ato, `argumento`), e assiste ao plenário do STF (`plenario` colegiado stf, Teresa sustenta com as suas notas) | Rafael te abriga; Sofia desenha você "sem a capa preta"; fecho: os metadados mostram petições com a SUA assinatura digital em horários em que você presidia audiência no STF. |
| 3 | `a7-token` · A Assinatura | investigado | Falsidade ideológica (CP 299), fraude processual (CP 347), perícia digital com Kenji; cadeia de custódia | Suspeita cai em Helena (pista falsa bem construída); confronto doloroso com ela; perseguição de carro (`tensao`); fecho: o token estava com Dani. |
| 4 | `a7-pad` · Defesa Pessoal | investigado | Instrução do PAD no CNJ: Lei 9.784 arts. 2º, 3º, 38, 44, 46; você inquire testemunhas (`depoimento`), `protesto` contra perguntas de Saulo, acareação Ronan × ex-assessor; denunciação caluniosa (CP 339) | Marina começa a hesitar; Joana percebe que foi usada; fecho: Ronan recebe depósito do mesmo pré-pago da Altavista. |
| 5 | `a7-giz` · Giz e Quadro | investigado | Magistério permitido (CF 95 § ún. I) e o limite: você NÃO pode advogar para Tainá; tem de orientá-la a procurar a Defensoria e a reunir prova (CLT na medida do catálogo); ameaça e coação (CP 344) | Episódio mais humano e mais fora do tribunal: aula noturna, praça com manifestantes, pedra na janela, Tainá ameaçada; perseguição a pé; fecho: Dani aparece na porta da sua casa chorando. |
| 6 | `a7-dani` · Lealdade | investigado | Coação no curso do processo (CP 344), falso testemunho (CP 342), abuso de autoridade (LAA 27) do delegado Nery; acareação Dani × Nery; colaboração | Dani foi coagida por Nery (dívida e ameaça ao irmão). Escolha livre: perdoar/proteger ou entregar (marca `a7_perdoou_dani`); as duas têm custo. Fecho: Nery menciona "o arquivista". |
| 7 | `a7-sessao` · Quinze Votos | investigado | Julgamento do PAD no plenário do CNJ (CF 93, X; motivação; proporcionalidade da pena): `plenario` total 15, maioria 8, com 6–7 votos a conquistar; Edgar quer o exemplo | O episódio mais difícil do ato. Resultado narrativo fixo (censura e retorno), mas o caminho exige tudo. Momento humano de Edgar. Fecho: a toga volta — "com uma câmera apontada para cada decisão sua". |
| 8 | `a7-volta` · A Volta | juiz | De volta à vara sob vigilância: Hugo provoca a sua suspeição (CPP 254) e testa cada decisão; `audiencia` com incidentes armados para você errar; `palavra`; `sentenca` impecável | "Atenção redobrada": a defesa quer que você erre a favor OU contra; a decisão certa é a fria. Fecho: o executor da morte de Paulo Seixas é preso — e o júri cai na sua vara. |
| 9 | `a7-juri` · O Executor | juiz | Júri presidido por você: CPP 252–254 (você decide se é suspeito: depende das marcas — se ficou íntimo(a) de Clara, o certo é declarar a suspeição e o episódio segue por outro caminho), 466, 468, 477, 478, 483, 492; incomunicabilidade dos jurados | Clara na plateia; um jurado é abordado na garagem (`tensao`); você precisa dissolver o conselho ou não (497). Fecho: o executor diz um nome: "o escrivão". |
| 10 | `a7-raiz` · A Raiz | juiz (instrução) | Desfecho: Bento Carvalho, o arquivista que anotou a sua vida desde o Ato 1 e vendeu o dossiê a Hugo/Ataulfo, financiado por Henrique da cela; denunciação caluniosa (CP 339), corrupção, organização criminosa; Teresa denuncia, você instrui, Helga relata | Clímax com tudo: plenário, acareação final, sentença. Momento humano de Bento ("eu só anotava; ninguém nunca me perguntou nada"). Epílogo da carreira inteira e créditos (`"final": true`). |

## Divisão do trabalho
Cinco roteiristas, dois episódios cada, arquivos próprios: `ato7a.json` (1–2), `ato7b.json` (3–4), `ato7c.json`
(5–6), `ato7d.json` (7–8), `ato7e.json` (9–10). Elenco comum em `ato7.json` (só o coordenador altera; personagem novo
de um episódio vai no arquivo do roteirista com prefixo `a7a…`, `a7b…` etc.). Ordens: 1 a 10.
Continuidade: cada roteirista lê esta bíblia inteira e as linhas dos episódios vizinhos; ganchos de fecho de um
episódio são a abertura do seguinte. Marcas que atravessam episódios: `a7_perdoou_dani`, `a7_confiou_joana`,
`a7_ajudou_taina_certo`, `a7_intimo_clara` (consolar Clara no cemitério em 5 ou 6), `a7_culpou_helena`.
