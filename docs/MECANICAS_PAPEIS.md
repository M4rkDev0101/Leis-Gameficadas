# Mecânicas por papel — cada um age como age num tribunal de verdade

Pedido do usuário (23/10/2026): na Toga ele "atuava mais como acusação do que como juiz". Regra de design daqui em
diante: **a mecânica de cada cena tem de ser o que aquele papel faz na vida real**. O validador (`tribunal.py`,
`_validar_juiz`) recusa uma mecânica no papel errado.

## Quem faz o quê (e o que NÃO faz)

| Papel | Faz | Não faz | Mecânicas |
| --- | --- | --- | --- |
| Advogado(a) de defesa | investiga, interroga a testemunha da outra parte, protesta, apresenta provas, negocia, sustenta oralmente | decidir; mentir (blefe tem preço) | `depoimento` (pressionar/apresentar), `protesto`, `apresentar`, `investigar`, `convocar`, `acareacao`, `argumento`, `blefe`, `plenario` (júri e STF) |
| Promotor(a) (MP) | decide se denuncia, arquiva ou propõe acordo (CPP, arts. 28 e 28-A); monta a denúncia (art. 41); inquire; protesta; pode pedir absolvição (fiscal da lei) | acusar sem prova; usar prova ilícita | `denuncia`, `depoimento`, `protesto`, `plenario` (júri), `escolha` |
| Juiz(a) | preside: dá e tira a palavra, admite ou barra perguntas (art. 212), mantém a ordem (arts. 251 e 794), protege vítima e testemunhas (art. 400-A), complementa a inquirição só nos pontos obscuros (art. 212, par. único), decide incidentes e sentencia de forma fundamentada (art. 381; CF, art. 93, IX) | produzir prova no lugar da acusação (art. 3º-A); "encurralar" a testemunha; decidir por medo ou simpatia | `audiencia`, `decidir`, `palavra`, `sentenca`, `depoimento` em modo juiz (botões "Esclarecer" e "Confrontar com os autos", sem "UM MOMENTO!"/"AQUI ESTÁ!") |
| Juiz(a) presidente do júri | dirige os debates e intervém em abuso (art. 497, III); barra referências proibidas (art. 478); garante a incomunicabilidade dos jurados; formula os quesitos (art. 483) | votar; dizer aos jurados o que decidir | `audiencia`, `palavra` (art. 477), `escolha` (quesitos), `sentenca` (art. 492) |
| STF (advogado na tribuna ou juiz(a) instrutor(a)) | sustentação oral; memoriais; responder à dúvida de cada ministro (precedente, competência, modulação); instrução delegada em ação penal originária | votar como ministro | `plenario` (colegiado "stf"), `audiencia` (instrução), `argumento` |
| Todos, fora do tribunal | vida pessoal, provocações, ameaças, perseguições | — | `tensao`, `celular`, `investigar`, `escolha` livre |

## Formatos (JSON das cenas)

Todas aceitam `falas` (antes), `local` e `proxima`. Erro custa 1 de credibilidade e repete a decisão, como nas demais.

### `audiencia` (juiz) e `protesto` (advogado/promotor)
As falas correm uma a uma. Em cada uma o jogador escolhe **Seguir** (Enter) ou **Intervir/Protesto** (X).
Intervir numa fala regular = cerceamento (dano). Seguir num incidente = omissão (dano, e a fala se repete).
```json
{"tipo": "audiencia", "titulo": "Inquirição do cabo", "linhas": [
  {"q": "a4tulio", "e": "normal", "t": "Cabo, a que horas o senhor chegou?"},
  {"q": "a4tulio", "e": "apontando", "t": "O réu entregou a senha por vontade própria, não foi?",
   "incidente": {"pergunta": "Como o juízo intervém?", "chamada": "Um instante, doutor.",
                 "fundamentos": [{"chave": "CPP#art-212", "trecho": "não admitindo o juiz aquelas que puderem induzir a resposta"}],
                 "omissao": [{"q": "a4rita", "t": "(sussurrando) Excelência, a pergunta induz a resposta…"}],
                 "opcoes": [{"t": "Indefiro: é indutiva. Reformule.", "certa": true, "falas": […]},
                            {"t": "Deixo responder.", "falas": […]}]}}],
 "erro_interromper": […], "acerto": […], "proxima": "s8"}
```
Regras: ao menos uma fala regular e um incidente; o juiz (`voce`) não é orador; todo incidente tem fundamento legal.
Em `protesto` as opções são **fundamentos do protesto** e as falas da opção trazem a decisão do juiz (personagem).

### `palavra` (juiz) — conceder a palavra
```json
{"tipo": "palavra", "titulo": "Alegações finais orais", "ordenar": true, "passo": 5,
 "oradores": [{"q": "a4tulio", "papel": "Acusação (MP)", "tempo": 20},
              {"q": "a4assist", "papel": "Assistente de acusação", "tempo": 10},
              {"q": "brandao", "papel": "Defesa", "tempo": 30}],
 "fundamentos": [{"chave": "CPP#art-403/par-2", "trecho": "…"}], "acerto": […], "erro": […], "erro_ordem": […]}
```
`tempo` exato, ou faixa `min_ok`/`max_ok` (ex.: 20–30 quando a prorrogação é facultativa). Com `ordenar`, a ordem
do JSON é a correta e a tela começa embaralhada. Referências: art. 403 (20 + 10; corréus individual; assistente 10 e a
defesa ganha +10), art. 411, § 4º; júri art. 477 (1h30, réplica 1h; mais de um réu: +1h e réplica dobrada).

### `sentenca` (juiz) e `denuncia` (promotor) — peça em partes
```json
{"tipo": "denuncia", "titulo": "Denúncia", "partes": [
  {"nome": "Classificação do crime", "opcoes": [{"t": "…", "certa": true, "fundamentos": […]}, {"t": "…", "falas": […]}]},
  {"nome": "Materialidade", "provas": ["laudo"], "erro": [{"q": "narrador", "t": "Isso não prova que o crime ocorreu."}]},
  {"nome": "Autoria", "provas": ["video"], "pergunta": "Que peça aponta quem foi?", "erro": […]}],
 "acerto": […]}
```
Partes com `provas` (só na denúncia) abrem os autos; prova falsa conta como `usou_falsa`. Sentença: relatório,
fundamentação (art. 155: só prova do contraditório), dispositivo (art. 386 para absolver), dosimetria se houver.

### `plenario` — STF (11 ministros) ou júri (`"colegiado": "juri"`, 7 jurados, maioria 4)
```json
{"tipo": "plenario", "colegiado": "juri", "titulo": "Conselho de Sentença", "votos_fixos": {"favor": 3, "contra": 2},
 "ministros": [{"rotulo": "Jurada 2", "preocupacao": "Franze a testa quando ouve falar do laudo.", "voto": "indeciso",
                "argumentos": [{"t": "…", "certa": true, "falas": […]}, {"t": "…", "falas": […], "endurece": true}]}],
 "acerto": […]}
```
No STF cada ministro é um personagem (`q`) e a preocupação é jurídica. No júri ninguém fala com jurado à parte: o
jogador lê a **reação** de cada um durante os debates (`rotulo`) e responde com o argumento certo, em linguagem leiga.
`votos_fixos` + ministros = total; a maioria tem de ser alcançável.

### `tensao` — fora do tribunal, escolha no susto
```json
{"tipo": "tensao", "local": "rua", "tempo": 7, "padrao": 1, "pergunta": "Um carro escuro te segue…",
 "hesitou": "Você hesitou…", "opcoes": [{"t": "Entrar no posto iluminado", "cred": 1, "falas": […]},
                                         {"t": "Acelerar para casa", "marca": "seguido_ate_casa", "falas": […]}]}
```
Sem opção certa: cada escolha tem consequência (`cred` de -2 a +1, `marca` para a história). Tempo de 3 a 20 s; ao
esgotar vale `padrao`. Coração acelerando, vinheta vermelha e música de pressão. Use com moderação (1 por caso, no máximo).

### `celular` — mensagens (provocação, ameaça, recado, notícia)
```json
{"tipo": "celular", "contato": "Número desconhecido", "status": "online",
 "mensagens": [{"de": "ele", "t": "Belo discurso hoje, doutora."}, {"de": "voce", "t": "Quem é?"}],
 "opcoes": [{"t": "Não responder e registrar ocorrência", "marca": "registrou_ameaca", "falas": […]},
            {"t": "Responder", "envia": "Quem é você?", "retorno": [{"de": "ele", "t": "Um admirador."}], "cred": -1}],
 "depois": […]}
```
`opcoes` é opcional (sem ela o jogador só lê e guarda o celular). `se` nas mensagens condiciona a marcas.

## Efeito novo
`"fx": "ordem"` — balão dourado "ORDEM!" com martelo: a intervenção do juiz. Nas falas do jogador-juiz, `ummomento`
vira `ordem` e `tomaisso` vira `martelo` automaticamente (juiz não grita "um momento" para a testemunha).

## Música por cena
Qualquer cena aceita o campo opcional `"musica"` (só o cliente lê; o validador ignora chaves extras):
```json
{"tipo": "dialogo", "local": "cemiterio", "musica": "luto", "falas": […]}
```
A música troca (crossfade no próximo compasso) ao entrar na cena e vale para tudo que a cena tocar (inclusive o que seria
"calma", "julgamento" ou "pressao"), até a próxima cena trocar de música. Temas: `perseguicao` (pulsante), `traicao`
(piano e cordas, lento), `luto` (cemitério), `plenario` (STF, solene), `juri` (grave e tenso), `noite` (casa/carro,
solitário), `vitoria_amarga` (conquista com custo), `audiencia` (discreto), além de `principal`, `calma`,
`investigacao`, `julgamento`, `interrogatorio`, `pressao`, `abertura`, `supremo`. Sem o campo valem os padrões:
`tensao` = perseguicao; `plenario` = plenario (STF) ou juri (`"colegiado": "juri"`); `audiencia`/`protesto` = audiencia;
`celular` em `casa`/`carro` = noite (a música abaixa a cada vibração). Ambiências de som por `local` (carro: motor e
chuva; cemiterio: vento e sino distante; praca: multidão; garagem, casa, corredor, cafe, custodia) entram sozinhas.
