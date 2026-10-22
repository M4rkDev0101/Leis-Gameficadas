# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). O projeto ainda não publica versões
numeradas; as versões abaixo foram reconstruídas do histórico do git e agrupam commits por marco.

## [Não lançado]

### Adicionado
- Documentação do projeto: GDD, roadmap, changelog, licenças de assets e arquitetura.
- Ferramenta `escalar_vozes.py` para escalar as vozes da dublagem por gênero e idade (em andamento).
- Trilha sintetizada com sequenciador próprio: temas principal, investigação, julgamento, pressão, vitória e calma,
  com crossfade; efeitos novos (autos, prova, carimbo, passos, porta, tremor) e ambiência por local.

### Alterado
- Personagens redesenhados: sombreamento em 2 tons, olhos com brilho, sobrancelhas por expressão, poses com
  braços e mãos, detalhes de roupa, cabelos novos, rugas para personagens grisalhos, respiração e susto animados.
- Interface com identidade visual única: logotipo, caixa de diálogo, autos em pergaminho e cartões da carreira.

## [0.6.0] - 2026-10-22

### Adicionado
- Dublagem opcional com ElevenLabs: exportação do roteiro, geração retomável e áudio no jogo (`9bf4a15`).

### Corrigido
- Jogo aberto pelo atalho: o servidor não escreve no stderr quando ele não existe (`f869356`).

### Alterado
- Instalador: atualização por `fetch` + `reset`, que se conserta sozinha se uma atualização anterior foi
  interrompida (`4b3ea1b`).

## [0.5.0] - 2026-10-21

### Adicionado
- Modo história completo: 43 casos (~11,9 h), dilemas morais e finais alternativos (`d8a071e`).
- Escolhas morais com consequências, aberturas de ato, conquistas e créditos (`174ee73`).

### Alterado
- Sala de audiência e escritório redesenhados: madeira, luz, plateia, bandeiras e janela em arco (`5937391`).

## [0.4.0] - 2026-10-21

### Adicionado
- Modo Carreira completo: Ato V (Altavista), documentação e README (`e6bc528`).
- Ato IV (A Toga), com 6 casos de magistratura (`79915e2`).
- Ato III (O Concurso), com 6 casos de promotoria (`17207a1`).
- Ato II (A Advocacia), com 6 casos (`394af54`).
- Ato I, com 6 casos, investigação e progresso salvo (`7594e44`).

### Alterado
- Cenários de investigação redesenhados: profundidade, luz, texturas e detalhes nos 12 locais (`7919615`).

## [0.3.0] - 2026-10-21

### Adicionado
- Instalador publicado pelo GitHub Actions e README do modo Tribunal (`76cb544`).
- Modo Tribunal: simulação de audiência jogável e instalador automático (`d951e7b`).

## [0.2.0] - 2026-10-21

### Adicionado
- Banco com 841 questões em 20 áreas e 3 novos concursos (`e37b99d`).
- Simulados no formato de concursos reais e casos de advogado, promotor e juiz (`a947cfa`).

## [0.1.0] - 2026-10-21

### Adicionado
- Fundação do Vade: importador do acervo, núcleo de aprendizagem e painel de atualização (`7bc56ba`).
