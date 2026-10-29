# Cenários em imagem — prompts para gerar com IA

O jogo carrega o fundo de cada local de `services/arena/src/vade_arena/web/cenarios/<nome>.webp` (ou `.png`/`.jpg`).
Enquanto um arquivo não existe, aquele local usa o desenho antigo em código (ou um parecido, para os locais novos).
Quando os 42 arquivos estiverem na pasta, o código de desenho dos cenários é removido.

## Regras para todas as imagens

- **Formato:** 16:10, 1920×1200 (mínimo 1280×800; o palco do jogo é 16:10), `.webp`, `.png` ou `.jpg`, nome exatamente como na tabela.
- **Enquadramento:** câmera na altura dos olhos, de frente. O personagem é desenhado por cima, em pé no **centro**,
  da cintura para cima, com a cabeça entre 25 % e 55 % da altura: deixe o **terço central livre** (sem poste, planta,
  luminária ou objeto na frente). O chão aparece nos 20 % de baixo.
- **Proibido:** pessoas, rostos, texto legível, logotipos, marcas, bandeiras ou brasões reais de órgãos públicos.
- **Licença:** use um gerador cujos termos permitam uso comercial e guarde a ferramenta/data em `docs/ASSET_LICENSES.md`.
- **Mesmo estilo em todas:** gere todas com o mesmo bloco de estilo (abaixo) e, se a ferramenta permitir, a mesma seed
  ou imagem de referência de estilo (use a primeira aprovada como referência das demais).

**Bloco de estilo (colar no início de todos os prompts):**

> 2D visual novel background, hand-painted anime illustration, clean lineart, soft cel shading, rich warm cinematic
> lighting, detailed but uncluttered, eye-level straight-on camera, 16:10, empty space in the center for a character,
> visible floor at the bottom, no people, no text, no logos, no watermark

**Negativo (se a ferramenta aceitar):** people, person, face, text, letters, logo, watermark, signature, flag, blurry,
photo, 3d render, fisheye, tilted camera

## Tribunal (o jogo desenha a bancada na frente)

Nestas cinco, o jogo sobrepõe uma bancada de madeira nos ~30 % de baixo: a parte inferior pode ser só piso/parede.

| Arquivo | Prompt (depois do bloco de estilo) |
|---|---|
| `defesa` | Brazilian courtroom seen from the defense side, wood-paneled wall with soft blue accent, tall window with blinds on the left, framed law diplomas, warm afternoon light |
| `acusacao` | Brazilian courtroom seen from the prosecution side, wood-paneled wall with dark red accent, bookshelf with thick law codes, closed door on the right, warm light |
| `testemunha` | Witness stand area of a courtroom, wooden wall panels, a simple wooden railing, clock on the wall, neutral warm light |
| `juiz` | Judge's elevated bench in a Brazilian courtroom, high wooden backrest, generic golden scales-of-justice emblem on the wall (no real coat of arms), dark red curtains, solemn light |
| `escritorio` | Small law office at dusk, desk with stacked case files and a lamp, bookshelf full of law books, window with city lights, cozy warm light |

## Locais

| Arquivo | Prompt (depois do bloco de estilo) |
|---|---|
| `bar` | Simple neighborhood bar in São Paulo at night, tiled counter, bottles on shelves, plastic tables, warm yellow light |
| `mercado` | Supermarket aisle, shelves of generic unbranded products, bright fluorescent light |
| `ponto` | City bus stop at night, metal shelter, street lamp, wet asphalt reflecting lights |
| `delegacia` | Brazilian police station front desk, old computer, filing cabinets, bulletin board with blank papers, cold fluorescent light |
| `apartamento` | Small modest apartment living room, worn sofa, TV on a rack, window with apartment buildings outside, evening light |
| `obra` | Construction site, unfinished concrete building, scaffolding, wheelbarrow, sand piles, late afternoon light |
| `rua` | Busy downtown street in a Brazilian city, old buildings, sidewalk, parked cars, dusk light |
| `parlatorio` | Prison visiting booth, glass partition with metal counter and phone handsets, grey concrete walls, harsh light |
| `gabinete` | Judge's chambers, large wooden desk with files, leather chair, bookshelves, window with blinds, sober light |
| `juri` | Jury box in a courtroom, two rows of empty wooden chairs, wood panel wall, solemn light |
| `loja` | Small electronics shop interior, glass counter, shelves with generic devices, bright light |
| `clinica` | Small medical clinic consultation room, examination bed, white cabinets, clean bright light |
| `custodia` | Small hearing room for custody hearings, simple table, monitor for video conference, grey walls, neutral light |
| `stf` | Supreme court plenary, semicircular dark wood bench with high-backed chairs, modernist architecture, generic emblem, grand solemn light |
| `promotoria` | Public prosecutor's office, desk with stacks of case files, computer, bookshelf, institutional beige walls |
| `garagem` | Underground parking garage at night, concrete pillars, flickering fluorescent lights, painted floor lines |
| `carro` | Interior of a car at night seen from the back seat towards the front, dashboard glow, city lights through the windshield |
| `casa` | Cozy family living room at night, sofa, coffee table, lamp, family photos without faces |
| `corredor` | Long courthouse corridor, wooden benches between closed office doors, marble floor, tall windows |
| `praca` | Public square in front of a modernist courthouse, trees, benches, bright day |
| `cafe` | Small coffee shop, espresso machine on the counter, chalkboard menu without readable text, warm morning light |
| `cemiterio` | Brazilian cemetery at dusk, white tombs, cypress trees, overcast sky |
| `presidio` | Prison cell block gallery, row of barred cells, concrete walls, cold harsh light |
| `hospital` | Hospital room, empty bed with monitors, curtain divider, window, soft clinical light |
| `senado` | Senate committee hearing room, curved panel of seats with microphones on a raised bench, blue carpet, large screen, formal light |
| `imprensa` | Press conference room, empty podium with many microphones, camera tripods, plain backdrop without logos |
| `hotel` | Hotel room at night, made bed, nightstand lamp, closed curtains, city glow |
| `elevador` | Inside an office elevator, brushed steel doors closed, button panel, mirror, overhead light |
| `cartorio` | Brazilian notary office, service counter with numbered windows, file cabinets, stamps, fluorescent light |
| `aeroporto` | Airport departure hall, large windows with an airplane outside, rows of seats, flight board with blurred text |
| `sala_de_aula` | Law school classroom, chalkboard, rows of desks, professor's desk, daylight from windows |
| `defensoria` | Public defender's office service room, simple desk with files, plastic chairs, notice board with blank papers |
| `laboratorio` | Forensic laboratory, workbench with microscope and evidence bags, computer with analysis screens, cool light |

## Como entregar

Coloque os arquivos em `services/arena/src/vade_arena/web/cenarios/` (ou em qualquer pasta e avise). Para conferir o
que falta: `python -I -c "import os;print(sorted(set('defesa acusacao testemunha juiz escritorio bar mercado ponto delegacia apartamento obra rua parlatorio gabinete juri loja clinica custodia stf promotoria garagem carro casa corredor praca cafe cemiterio presidio hospital senado imprensa hotel elevador cartorio aeroporto sala_de_aula defensoria laboratorio'.split())-{f.rsplit('.',1)[0] for f in os.listdir('services/arena/src/vade_arena/web/cenarios')}))"`
