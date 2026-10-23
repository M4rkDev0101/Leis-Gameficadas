# Game feel (juice) do Vade Tribunal

Registro: sério/tenso (drama jurídico). Impacto com peso, deformação contida, câmera curta; nada pula ou quica.
Tudo em `web/tribunal.html`: só `transform`/`opacity`, animações finitas, sem `filter`/blur animado, sem rAF, sem partículas contínuas.

## Vocabulário (evento -> efeito)
| Categoria | Evento | Efeito |
|---|---|---|
| Mudança de estado (forte) | PROTESTO!/UM MOMENTO!/AQUI ESTÁ! | balão com zoom-punch (3,4x -> 1), flash branco 180 ms, tremida 450 ms, hit-stop 120 ms, `Sound.punch` + fanfarra |
| Recompensa | contradição achada / prova certa | linhas de velocidade (douradas+brancas), zoom 1,55x no rosto "chocado", flash, tremida; na prova certa simples: linhas + tremida leve |
| Perigo | prova errada | vinheta vermelha, tremida leve (280 ms), barra de credibilidade pisca vermelha e a balança perdida "sangra" |
| Mudança de cena | tribunal <-> investigação <-> escritório | cortina escura com filete dourado (250 ms entra, 300 ms sai) + whoosh |
| Veredicto | carimbo | letras batem uma a uma (70 ms cada, tremida leve por letra), confete + papéis, XP conta até o valor (24 passos) |
Falha por regra (destituído) usa o martelo, não o efeito de impacto do balão.

## Texto
Destaques: artigos/leis (dourado), valores e prazos (azul), CAIXA ALTA (vermelho claro). Pausas: "..." 160/400 ms, "…" 380 ms, ponto final 160 ms, travessão 220 ms. Bipe por tipo de voz: juiz (serra grave + seno), feminino (triângulo agudo), masculino/narrador (quadrada).

## Controles e limites
- Opção "Efeitos de tela" (botão ✨ no topo do menu, `localStorage.tribFx`) e `prefers-reduced-motion` desligam balão-punch, hit-stop, tremida, linhas, cortina, letras, confete e contagem de XP (sobra só o flash simples e o balão estático).
- Toda tremida/zoom volta ao repouso; o hit-stop só pausa animações (a entrada de avanço continua válida; autoplay não quebra).
- Valores ajustáveis: durações nos `@keyframes` (bubblepunch, shakelite, speedln, credhurt, wipein/out, ltslam) e em `hitstop(120)`.

## Validação
Capturas em `C:/lx/tmp-juice/` (geradas por `shots.js` via CDP/Edge headless). Playwright não está instalado: o smoke-test da skill não pôde rodar; no lugar, `autoall.js` roda `autoplay.js` em todos os episódios e falha com qualquer erro de console.
