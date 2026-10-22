# Licenças de assets

Inventário de tudo o que o jogo usa além do código. Regra do projeto: preferir material gerado por código, que
é obra original do próprio projeto. Licenças externas verificadas em 2026-10-22.

| Asset | Origem | Licença | Observação |
| --- | --- | --- | --- |
| Personagens, cenários, ícones e carimbos | SVG gerado por código (`characterSVG`, `background`, `desk`, `locationBG` em `web/tribunal.html`) | Obra original do projeto | Não há imagens, sprites nem arquivos de arte externos. |
| Efeitos e música (blips, protesto, martelo, dano, acerto, vitória, temas "calma" e "tensa") | Sintetizados em tempo real com WebAudio (objeto `Sound`) | Obra original do projeto | Nenhum arquivo de áudio é distribuído com o jogo. |
| Roteiro, personagens e textos dos casos | `content/tribunal.json` e `content/ato*.json` | Obra original do projeto | Nomes e tramas fictícios. |
| Banco de questões | `content/questoes.json` e `content/geradas.json` | Obra original do projeto | Reproduz o formato das bancas, não copia provas. As geradas derivam da letra da lei. |
| Leis e súmulas (texto do acervo) | Repositório [ctresb/leis](https://github.com/ctresb/leis), importado para o catálogo SQLite | Scripts do acervo sob MIT; os textos são atos oficiais sem proteção autoral (Lei nº 9.610/98, art. 8º, I), segundo o README do acervo | O acervo avisa que os textos são conversões automáticas, informativas, e não substituem o Diário Oficial. Não é redistribuído neste repositório: o instalador o baixa. |
| Fontes | Fontes do sistema do usuário (Georgia, Times New Roman, serifa e monoespaçada genéricas) | Licenças do sistema operacional | Nada é embutido nem baixado. |
| Dublagem local (planejada) | Geração local com VoiceStudio/OmniVoice ([k2-fsa/OmniVoice](https://huggingface.co/k2-fsa/OmniVoice)) | Código Apache 2.0; modelo pré-treinado CC-BY-NC | CC-BY-NC proíbe uso comercial. O autor proíbe clonagem de voz sem autorização. Use só vozes próprias ou autorizadas e confira a licença antes de distribuir. |
| Dublagem opcional (ElevenLabs) | Arquivos `<id>.mp3` gerados na conta do próprio usuário com `tools/vozes.py` | Termos de serviço da ElevenLabs e do plano da conta | Os áudios ficam fora do repositório (`%LOCALAPPDATA%\VadeTribunal\vozes` ou `VADE_VOZES`). Confira se o plano permite o uso pretendido. |
| Ícone do instalador | Gerado por `instalador/gerar_icone.py` | Obra original do projeto | |
| Python e PyInstaller (dentro do `VadeTribunal.exe`) | Compilação pelo GitHub Actions | Python: PSF License. PyInstaller: GPL-2.0 com exceção para executáveis gerados | Confira os termos do PyInstaller ao redistribuir o `.exe` fora deste fluxo. |

## Como adicionar um asset novo

1. Prefira gerar por código (SVG ou WebAudio). Nesse caso, basta registrar o item na tabela como obra original.
2. Se precisar de um arquivo externo, use só material cuja licença permita uso, modificação e redistribuição
   (CC0, CC-BY, MIT, SIL OFL etc.). Evite CC-BY-NC, "uso pessoal" e fontes sem licença clara.
3. Guarde a fonte (URL), o autor e a versão da licença; inclua a atribuição exigida neste arquivo ou numa pasta
   `licencas/`.
4. Adicione uma linha à tabela acima com Asset, Origem, Licença e Observação.
5. Não comite chaves de API, áudios de contas pagas nem material de terceiros sem a licença registrada.
6. Use o prefixo do tipo no commit (`art:`, `audio:` ou `docs:`) e cite este arquivo na descrição.
