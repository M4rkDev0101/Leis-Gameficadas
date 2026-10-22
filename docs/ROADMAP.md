# Roadmap

Organizado por marco, sem datas fixas. O roadmap de produto de longo prazo (MVP → V1 → V2 → Enterprise) está
em [06-roadmap.md](06-roadmap.md); este documento trata do jogo Vade Tribunal.

## Feito

### Marco 1: fundação (acervo e aprendizagem)
- Importador do acervo ctresb/leis (parser estrutural, precedentes, qualidade, classificação, SQLite + FTS) e painel
  "Verificar atualização".
- Núcleo de aprendizagem: FSRS-5, XP, níveis, sequência, ligas, moedas e dificuldade dinâmica.
- Esquema SQLite multiusuário de progresso e eventos mensais.

### Marco 2: arena
- Simulados em 7 modelos de concurso e 4 dificuldades, com regra de pontuação por banca.
- Banco de 841 questões em 20 áreas, com validação contra a lei vigente.
- Casos de advogado, promotor e juiz.

### Marco 3: Modo Tribunal e carreira
- Audiência jogável (depoimento, pressionar, apresentar, protesto, credibilidade, veredicto).
- Modo Carreira em 5 atos e 43 casos (~11,9 h), com investigação em 12 locais.
- Dilemas morais com marcas, finais alternativos, conquistas, abertura de ato, epílogo e créditos.
- Cenários redesenhados (sala de audiência, escritório e locais de investigação) e sons sintetizados.

### Marco 4: distribuição
- Instalador `VadeTribunal.exe` (PyInstaller) publicado pelo GitHub Actions, com atualização do jogo e do acervo.
- Dublagem opcional com ElevenLabs: exportação do roteiro, geração retomável e áudio no jogo.

## Em andamento

- Escalação das vozes da dublagem por gênero e faixa etária (`tools/escalar_vozes.py`, ainda não commitado).
- Documentação do projeto (GDD, arquitetura, changelog, licenças de assets).

## Próximo

### Dublagem local
- Gerar as falas localmente com o VoiceStudio/OmniVoice, sem custo por caractere, no mesmo formato de arquivo
  (`<id>.mp3`, id = `sha1("personagem|texto")[:12]`) lido pelo jogo.
- Antes de distribuir, conferir a licença do modelo (CC-BY-NC) e a origem das vozes de referência.

### Trilha e efeitos
- Ampliar a música procedural (hoje "calma" e "tensa") com temas por ato e por cena de clímax.
- Mais efeitos sonoros sintetizados, mantendo a regra de obra original.

### Arte de personagens
- Novas expressões e poses para o gerador SVG de bonecos, mais variedade de cabelos e roupas e retratos de
  destaque para os personagens centrais da trama.

### QA
- Ampliar os testes automáticos do cliente (hoje o `tools/autoplay.js` joga os 43 casos de ponta a ponta).
- Revisão jurídica do conteúdo e verificação periódica de artigos alterados pelo acervo.

### Mobile
- Ajustar a interface do `tribunal.html` para toque e telas pequenas; avaliar empacotamento como PWA.

### Multiusuário
- Hoje o progresso fica em um `jogador.sqlite` local. O esquema multiusuário e os eventos (`db/sqlite`) já existem;
  falta expor `services/api`, contas e sincronização.
