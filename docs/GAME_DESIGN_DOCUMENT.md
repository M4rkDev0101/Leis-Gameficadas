# Game Design Document: Vade Tribunal

## 1. Visão

Vade Tribunal é um jogo educacional jurídico em português do Brasil. Mistura visual novel, investigação e
julgamentos no estilo dos jogos de tribunal, com a progressão de estudo de aplicativos como o Duolingo. O
jogador aprende Direito aplicando artigos de lei reais, conferidos contra o texto vigente, em vez de decorá-los.
Personagens, tramas, questões e todo o material visual e sonoro são originais.

## 2. Público

- Candidatos a concursos públicos e ao Exame de Ordem (OAB).
- Estudantes de Direito.
- Curiosos que gostam de narrativa jurídica e querem entender como a lei funciona na prática.

## 3. Pilares

1. **A lei é a regra do jogo.** Toda prova e todo argumento cita um dispositivo validado (`python jogar.py validar`).
2. **Aprender fazendo.** O jogador investiga, questiona e decide; a resposta certa depende do texto legal.
3. **Escolhas com peso.** Dilemas morais não têm resposta errada e deixam marcas que mudam falas e finais.
4. **Tudo original e leve.** Visual em SVG gerado por código, som sintetizado, sem dependências externas.
5. **Estudo sustentável.** XP, níveis, conquistas e revisão espaçada incentivam voltar sempre.

## 4. Loop de jogo

1. Abrir o menu da carreira e escolher o próximo caso liberado.
2. **Investigar** o local: examinar pontos da cena e conversar com as pessoas até reunir as provas obrigatórias.
3. Ir à **audiência**: ouvir depoimentos, pressionar, apresentar provas, responder escolhas e decidir protestos.
4. Receber o **veredicto**: credibilidade restante, XP, carimbo do caso e gancho para o seguinte.
5. Ver conquistas e escolhas no menu e repetir. Entre os casos, treinar com simulados e questões.

Cada caso tem cerca de 20 minutos. O progresso é salvo a cada cena, e cada caso só libera depois de vencer o anterior.

## 5. Mecânicas

### 5.1 Investigação
Cena `investigar` com um dos 12 locais desenhados em SVG (bar, delegacia, obra, mercado, loja, clínica e outros).
O jogador clica em pontos da cena (`x, y, w, h` em % do palco) e escolhe pessoas para conversar. Provas listadas em
`requer` são obrigatórias para avançar, e o validador garante que a própria cena as entregue.

### 5.2 Depoimento: pressionar e apresentar
Na cena `depoimento`, a testemunha faz afirmações. O jogador pode **pressionar** cada uma para obter mais detalhes
ou **apresentar** uma prova ou artigo dos autos do processo. Uma afirmação é contraditória e uma das provas a
derruba. Apresentar o item errado custa credibilidade.

### 5.3 Escolhas e apresentação
- `escolha`: alternativas com uma correta; o erro custa credibilidade e repete a pergunta.
- `apresentar`: o jogador escolhe nos autos a prova ou lei que responde ao argumento.

### 5.4 Decidir
Como juiz(a), o jogador decide protestos (deferido ou indeferido, por exemplo pelo CPP art. 212), prisões,
legalidade de provas e dosimetria nos atos finais. Cena `decidir`.

### 5.5 Dilemas e marcas
Escolhas com `"livre": true` não têm resposta errada. Cada opção grava uma **marca** na carreira quando o caso é
vencido (rejogar e escolher diferente troca a marca). Falas com `"se": "marca"` ou `"!marca"` e veredictos com
`variantes` mudam conforme as marcas, inclusive de atos anteriores. Cinco dilemas atravessam a campanha (Lucas,
Sofia, Valadares, Helena e o futuro do protagonista) e levam a três finais e ao epílogo "Dez anos depois".

### 5.6 Credibilidade
Cinco balanças. Cada erro custa uma; zerar derruba o caso, que recomeça do último ponto salvo. A credibilidade
restante e os erros entram no XP, calculado no servidor com limites.

### 5.7 XP, níveis e conquistas
- XP do caso: base por nível de dificuldade (básico 80, intermediário 120, avançado 170, especialista 230), mais 20
  por balança restante, mais 60 se não houve erros. Derrota rende 25.
- Títulos por nível, de Estagiário(a) a Ministro(a) (nível 45), definidos em `player.py`. XP, níveis e sequência
  diária seguem as regras de `services/learning` (`gamification.py`).
- Conquistas são calculadas do histórico, sem estado próprio: Primeiro veredicto, Sem um arranhão, Mão firme (10
  casos perfeitos), conclusão e "Impecável" de cada ato, Da toga ao veredicto final (carreira completa) e
  Consciência (cinco decisões morais).

### 5.8 Dificuldade
Cada caso tem um nível (básico, intermediário, avançado, especialista). Os simulados têm quatro dificuldades:
Treino, Padrão, Difícil e Elite, e alguns concursos exigem nível mínimo. A dificuldade dinâmica está em
`services/learning/.../difficulty.py`.

### 5.9 Simulados, questões e FSRS
Sete modelos de concurso (carreiras policiais e INSS/CEBRASPE, tribunais, TRT, Fiscal/Receita, OAB 1ª fase/FGV,
Magistratura e MP), com cronômetro, regra de pontuação da banca (no CEBRASPE, cada erro anula um acerto) e
correção comentada com o texto vigente. O banco tem 841 questões originais em 20 áreas: 70 escritas à mão e 771
geradas a partir da letra da lei. O núcleo de aprendizagem implementa o FSRS-5 para revisão espaçada.

## 6. Progressão de carreira: 5 atos, 43 casos

| Ato | Papel | Tema | Casos |
| --- | --- | --- | ---: |
| I. O Estágio | Defesa | Penal geral | 9 |
| II. A Advocacia | Advocacia cível | Consumidor, LGPD, trabalho, família | 9 |
| III. O Concurso | Promotoria | Maria da Penha, ambiental, improbidade, drogas | 9 |
| IV. A Toga | Magistratura | Preventiva, habeas corpus, provas ilícitas, dosimetria | 9 |
| V. Altavista | Magistratura | Julgamento final | 7 |

A lista de casos de cada ato está em [10-modo-carreira.md](10-modo-carreira.md). A campanha soma cerca de 11,9
horas estimadas. Cada ato abre com uma cena de promoção de cargo, e o último caso termina com epílogo e créditos.
Há também dois casos avulsos (promotor e juiz), sempre liberados.

## 7. Personagens principais

A trama gira em torno do escritório **Vasconcelos & Duarte** e da **Construtora Altavista**. O elenco completo, com
visual e voz, está em `content/tribunal.json`.

| Personagem | Papel | Personalidade e motivação |
| --- | --- | --- |
| Você | Estagiário(a) a juiz(a) | Avatar personalizável. Quer aprender o ofício e fazer a lei valer, inclusive contra quem lhe é próximo. |
| Rafael Duarte | Sócio sênior e mentor | Acolhedor e curioso, farejador de pistas (é ele quem liga o réu à Altavista). Preso, acusado de lavar dinheiro para o grupo. |
| Helena Vasconcelos | Sócia-gestora | Direta e exigente ("estagiário não serve café: estagiário trabalha"). Quer manter o escritório e a equipe de pé. |
| Dr. Otávio Lacerda | Promotor de Justiça | Confiante e combativo na acusação; recua quando a prova o desmente. |
| Dra. Beatriz Monteiro | Juíza de Direito | Firme e imparcial; exige ordem e fundamento. |
| Dra. Sílvia Prado | Advogada de defesa | Contraponto técnico ao protagonista nos casos de defesa. |
| Dr. Renato Valadares | Promotor de Justiça | Colega no Ato III; sua colaboração ou denúncia rigorosa decide se ele depõe no final. |
| Dani | Assessora do gabinete | Apoio do protagonista na magistratura. |
| Henrique Altavista | Dono da Construtora Altavista | Antagonista central; quer proteger o grupo e a imagem da empresa. |
| Dr. Augusto Brandão | Advogado da Altavista | Antagonista no julgamento final; tenta afastar o juiz por suspeição. |
| Sofia Duarte | Filha de Rafael, 9 anos | O lado humano do mentor; seu desenho aparece no epílogo conforme a escolha do Ato II. |
| Lucas Ferreira | Réu, 19 anos | Jovem que pode receber uma chance no escritório e reaparece no Ato V. |

Testemunhas, vítimas e réus dos casos (Valdir, Jorge, Ana, Bruno, Sargento Moreira e outros) completam o elenco.

## 8. Tom

Sério, mas acessível. A trama tem tensão e dilemas morais, com toques de humor nos bastidores. A linguagem é
clara, sem juridiquês gratuito; termos técnicos aparecem com o artigo que os sustenta. O jogo é informativo e não
substitui a publicação oficial das leis nem a orientação de um profissional.
