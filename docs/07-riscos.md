# 7. Riscos técnicos e mitigação

Ordenados por impacto × probabilidade.

| # | Risco | Impacto | Mitigação |
| --- | --- | --- | --- |
| 1 | **IA erra o Direito** (alucinação de artigo, pena, prazo, súmula inexistente) | crítico: o aluno erra a prova por causa do produto e perde a confiança | ancoragem obrigatória com citações por chave natural; verificador automático (citação existe, trecho é literal, 2º modelo resolve a questão sem gabarito); selo "revisado" só com revisão humana; denúncia com 1 clique e SLA; métrica de erro por 1.000 itens publicada internamente; bloquear geração em texto de qualidade baixa |
| 2 | **Texto desatualizado** (lei alterada ontem) | alto | sync por webhook + diff; materiais e questões do dispositivo alterado vão para "revisar" na hora; aviso ao usuário; data do texto visível ("texto de 21/10/2026, fonte: Câmara") |
| 3 | **Erros de conversão do acervo** (OCR, numeração, tachados) | alto | nota de qualidade por norma; corpus de regressão com os casos reais (já com 37 testes); relatório de avisos por importação; links para a fonte oficial; o README do acervo já avisa que não substitui o DOU, e nós também avisamos |
| 4 | **Direitos sobre questões de concurso** | alto (jurídico) | questões geradas são nossas; para históricas, usar só provas publicadas pelas bancas com análise jurídica prévia, guardando metadados e o vínculo a dispositivos (estatística de incidência é dado factual); parcerias/licenças com bancos de questões; nunca raspar sites de terceiros |
| 5 | **Custo de IA** foge do controle | alto | geração antecipada em batch (mais barata) + cache por (dispositivo, tipo, nível, banca); Haiku em tarefas simples; prompt caching dos textos legais; cotas por plano; painel de custo por usuário e por recurso |
| 6 | **Escala de eventos** (bilhões de linhas) | médio | arquivos de eventos mensais, UUIDv7, projeções reconstruíveis, arquivamento em Parquet, DuckDB para analytics |
| 7 | **Sync offline com conflitos** | médio | event sourcing (fatos imutáveis + replay por HLC); idempotência por id; só preferências usam LWW; testes de propriedade com interleavings aleatórios |
| 8 | **Trapaça nos rankings** | médio | servidor recalcula XP; limites de plausibilidade (tempo mínimo por questão, volume/hora); detecção de anomalia; ligas sem prêmio monetário |
| 9 | **Gamificação que atrapalha o aprendizado** (farm de XP, maratona sem retenção) | médio | XP ponderado por dificuldade e por revisão no prazo; teto diário suave; combo com teto; métricas de retenção real como norte do produto, não só engajamento |
| 10 | **Divergência entre FSRS do servidor e do cliente** | médio | vetores de referência compartilhados no CI (`vectors.json`); versão do algoritmo gravada no evento |
| 11 | **Dependência de um único acervo/mantenedor** | médio | licença MIT permite fork; espelho próprio; o pipeline aceita outras fontes (`FsSource`, LexML, Planalto); monitorar a saúde do upstream |
| 12 | **Mudanças de formato no upstream** | médio | parser tolerante + avisos; testes com amostra real a cada release; alarme quando a taxa de avisos/falhas subir num commit |
| 13 | **Taxonomia errada** (artigo no tema errado) | baixo-médio | origem e confiança por vínculo; revisão editorial dos temas dos concursos curados; correções dos usuários |
| 14 | **LGPD / dados pessoais** | médio | minimização, consentimento para ranking público, exportação/exclusão, PII isolada, DPO, região de dados no Brasil |
| 15 | **Prompt injection** via texto de norma ou de usuário | baixo | conteúdo entra como dado delimitado; o modelo não tem ferramentas de escrita no fluxo do tutor; saída validada |
| 16 | **Windows/infra de desenvolvimento** (nomes de arquivo inválidos no acervo) | baixo | leitura via object store do git (já implementado) |
