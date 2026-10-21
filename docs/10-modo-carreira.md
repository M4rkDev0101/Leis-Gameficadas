# 10. Modo Carreira: "Vade Mecum"

Uma campanha única, de estagiário(a) a juiz(a), com cerca de 30 casos e uma trama que atravessa
todos eles. Cada caso ensina um bloco do Direito que cai em prova, e cada mecânica sai de um
dispositivo real, conferido contra o texto vigente pelo comando `validar`.

## Estrutura de um caso (~20 min)

1. **Abertura** no escritório, na promotoria ou no gabinete: o problema e a pressão da história.
2. **Investigação**: explorar 1 a 3 locais, examinar pontos da cena e conversar com pessoas.
   Algumas provas são obrigatórias para seguir.
3. **Audiência**: depoimentos (pressionar ou apresentar prova), protestos, escolhas de tese.
4. **Veredicto** e gancho para o próximo caso.

Credibilidade: 5 balanças. Erros custam uma. Zerou, o caso recomeça do último ponto salvo.
O progresso é salvo a cada cena (dá para fechar o jogo e continuar).

## A trama

O escritório **Vasconcelos & Duarte** aceita você como estagiário(a). Caso a caso, aparecem os
rastros de um mesmo grupo: a **Construtora Altavista**, de **Henrique Altavista**, e seu advogado,
**Dr. Augusto Brandão**. Quando Rafael Duarte, seu mentor, é preso acusado de lavar dinheiro para a
Altavista, você precisa escolher um caminho: passa no concurso do Ministério Público, investiga
o grupo por dentro do sistema e, já juiz(a), preside o julgamento final, sem poder favorecer ninguém,
nem o seu antigo mentor.

| Ato | Papel | Tema jurídico | Casos |
| --- | --- | --- | --- |
| I — O Estágio | Defesa | Penal geral: furto × roubo, insignificância, legítima defesa, flagrante, estelionato, júri | 6 |
| II — A Advocacia | Advocacia cível | Consumidor, LGPD, responsabilidade civil, trabalho, família | 6 |
| III — O Concurso | Promotoria | Maria da Penha, ambiental, improbidade, drogas, organização criminosa | 6 |
| IV — A Toga | Magistratura | Prisão preventiva, habeas corpus, provas ilícitas, dosimetria | 6 |
| V — Altavista | Magistratura | O julgamento final, em vários dias de audiência | 4 a 6 |

## Mecânicas por ato

- **Ato I**: depoimento, apresentar prova, escolha de tese; investigação em locais simples.
- **Ato II**: perícias e documentos; prazos (quem perde prazo perde o caso).
- **Ato III**: como promotor(a), decidir o que denunciar; colaboração premiada.
- **Ato IV**: decidir protestos, deferir ou negar prisão, controlar a legalidade das provas.
- **Ato V**: tudo junto, com escolhas que mudam os depoimentos dos dias seguintes.

## Estado

| Ato | Casos | Situação |
| --- | --- | --- |
| I — O Estágio | O Celular da Rua Augusta · O Pão e a Lei · Ponto Final · Três Dias no Escuro · O Golpe do Pix · O Júri | ✅ jogável |
| II a V | — | em produção |

A duração mostrada no jogo é uma estimativa conservadora (`tribunal.estimate_minutes`): leitura a
~170 palavras por minuto, ~25 s por decisão e ~40 s por ponto de investigação, sem contar erros,
releitura dos autos e retomadas. O Ato I soma cerca de 53 minutos por essa conta.

## Formato da cena de investigação

```json
{"tipo": "investigar", "local": "bar", "titulo": "Bar do Zé",
 "intro": [falas],
 "pontos": [{"id": "camera", "nome": "Câmera", "x": 76, "y": 8, "w": 12, "h": 14, "falas": [{"q": "voce", "t": "…", "recebe": ["video"]}]}],
 "conversas": [{"q": "valdir", "titulo": "Perguntar a Valdir", "falas": [falas]}],
 "requer": ["video"], "proxima": "a3"}
```

`x, y, w, h` estão em % do palco (16:10) e batem com o desenho do local em `locationBG`. O validador
exige que toda prova de `requer` seja entregue por um ponto ou conversa da própria cena.
