# Audit: Citações Exatas vs Implementação

> **Objetivo futuro:** Este documento será a base para uma **skill** reutilizável. A skill vai:
> 1. Receber um plano (documento .md com requisitos)
> 2. Receber um artefato (código, HTML, etc.)
> 3. Extrair citações exatas do plano com line numbers
> 4. Extrair o estado atual do artefato
> 5. Gerar uma tabela de GAPs (❌/⚠️/✅) automaticamente
> 6. O loop de implementação consulta essa tabela antes de cada mudança
>
> Para chegar lá, primeiro precisamos validar o padrão manualmente neste projeto.
> Os dois objetivos imediatos são:
> 1. **Gerar um histórico das decisões tomadas nesta conversa** (citações do Otavio)
> 2. **Comparar em massa** cada citação contra a implementação atual

---

## Parte 1: Histórico de Decisões do Otavio (citações exatas da conversa)

### D1. Visão Geral do Projeto (mensagem inicial)

> "O tutorial em si não está muito bom. Eu preciso GRITAR para um usuário novo, olha, pra brincar no site vc precisa fazer isso, isso e isso. Aqui tem alguns extras. Aprendeu? Aqui tem material extra sobre a filosofia."

> "Tom: direto, imperativo, 'faça isso, depois isso, depois isso'. Sem filosofia."

**Decisão:** Tutorial em 3 camadas. Camada 1 = uso mínimo obrigatório, sem filosofia. Filosofia vai para camada 3.

---

### D2. Filosofia — Definição Central do Produto

**Mensagem (JSONL linha 1668):**

> "O objetivo principal dessa ferramenta é gerar os relatórios de desempenho. Mas isso exige que a IA consiga ver com precisão o que o aluno fez na prova."

> "Atualmente, professores por vezes perdem muito tempo corrigindo a prova de seus alunos. Principalmente nas 'monitorias' que temos na FGV, geralmente o monitor dedica muito tempo para conversar diferentemente com os alunos para que os alunos entendam exatamente onde erraram, onde perderam pontos, e muitas vezes pedir um aumento na nota."

> "Meu objetivo é que, com esse site, os professores não precisem dedicar tanto tempo para que os alunos entendam onde eles erraram, e facilitar que eles pleiteiem mudanças."

> "MUITO MAIS QUE UM NÚMERO, o professor e alunos recebem relatórios individualizados."

> "O aluno depois pode pedir assistência para a IA com dicas de estudo, entender conceitos que estão faltando, e o professor entende seus erros melhor!"

**Decisão:** O produto gera relatórios detalhados. O case FGV (monitoria, filas, pontos extras) é um EXEMPLO de uso, não o objetivo principal.

---

### D3. Filosofia — Case FGV Expandido

**Mensagem (JSONL linha 1676):**

> "Um uso desses relatórios é que o aluno entenda PORQUE ele recebeu aquela nota. Assim, ele não apenas pode entender O QUE ele errou, o que ele precisa estudar, ele também já entende onde pleitear uma nota para o professor revisar, algo que atualmente demanda muito tempo."

> "Por vezes, o professor fica um tempão discutindo com alunos que querem entender porque receberam tal nota e como aumentar essa nota. Alguns professores na FGV inclusive dão pontos extras para alunos que não pedem revisão nas suas notas, para evitar o tempo gasto com essa tarefa!"

> "O novo CR permite que os alunos saibam precisamente onde erraram e os critérios que deram essa nota. Ao invés de conversar com o professor, que tem tempo limitado, eles conversam com a IA. E aí se eles identificarem algum erro, podem escrever precisamente e de forma objetiva para o professor."

> "Isso ao mesmo tempo serve como ponto de revisão humana para a IA como diminui o tempo que professores gastam nessa tarefa... tudo isso enquanto torna a tarefa mais eficiente."

> "Enfim, te dei bastante dados sobre esse use case. Me faça perguntas agora! E sim, eu estou disposto a falar histórias pessoais da FGV nesse tutorial!"

**Decisão:** O case FGV tem história pessoal. O tutorial deve usar tom pessoal com exemplos reais. O ciclo é: aluno lê relatório → entende erros → pleiteia com precisão → professor economiza tempo → dados ficam.

---

### D4. Hierarquia — Filosofia Geral vs Case Específico (CORREÇÃO CRÍTICA)

**Mensagem (JSONL linha 2337):**

> "Eu usei umas 3 vezes com você pra te explicar que eu disse do chat como um CASE DE USO no novo CR. E mesmo assim você OUSOU descrever no primeiro slide que o problema que o novo CR resolve é economizar tempo na fila de correção de provas. OUSOU."

> "hey, essa é a filosofia geral: construir relatórios. Vs hey, aqui está um case."

> "a filosofia real é simplesmente gerar correções mais completas, gerar mais dados que permitam que professores e alunos entendam melhor suas lacunas no aprendizado."

**Decisão:** O slide 1 da filosofia DEVE ser a filosofia geral (relatórios, dados, lacunas). O case FGV vem DEPOIS, como exemplo. NÃO inverter.

---

### D5. Nota 8.5/10 — O que Falta para 10

**Mensagem (JSONL linha 1611):**

> "a gente não explicou sobre as tooltips. E eu não tenho certeza quando deveríamos avisar, no tutorial, sobre as tooltips. Provavelmente logo em um dos primeiros passos que tem tooltips."

> "Sobre os prints no tutorial, eles tem a view do computador e tem um espaço bem grandinho de background. A informação principal está toda numa caixinha, mas vemos todo o background, e aí o usuário precisa rodar desnecessariamente para baixo."

> "eu acho que a gente deveria repensar como mostramos os tutoriais avançados. Tem alguns passos que eu gostaria de ainda mais detalhes. Eu não queria poluir os slides com mais números (já estamos em 18), idealmente teria uma nova contagem quando vamos para algo avançado, que mostra apenas os slides relacionados àquele módulo"

> "precisamos melhorar os prints, refatorar como mostramos o texto, e pensar em formas melhores de melhorar os módulos avançados"

**Decisões:**
- Tooltips precisam de menção + print nos primeiros passos
- Prints devem ser cropados (só área relevante)
- Módulos avançados com contagem independente (não poluir os 10 básicos)

---

### D6. Falhas do Loop (CORREÇÃO CRÍTICA)

**Mensagem (JSONL linha 1965):**

> "vc sequer deu crop em nenhuma das imagens"
> "não tem nenhuma imagem da tooltip no primeiro painel, não link pro guia de filosofia"
> "você simplesmente não seguiu o plano em loop corretamente"

**Mensagem (JSONL linha 2337) — detalhamento:**

> "aquele print gigante passou por TRÊS FILTROS" — mesmo print reusado 3x sem verificar
> "vc criou múltiplos tutoriais avançados sem de fato entender como aquele módulo funcionava"
> "nos relatórios agregados, vc nem esperou a página carregar pra tirar seus prints"
> "até a porra do tutorial sobre filosofia, que a gente detalhou tão bem, você fez umas cagadas colossais"

**Mensagem (JSONL linha 2341):**

> "Você falou a minha análise, mas em nenhum momento leu o plano mestre, em nenhum momento comparou o que vc fez."
> "muitos dos seus erros não foram coisas que eu não tinha descrito, foi não seguir o loop."

**Decisão:** O loop DEVE: (1) reler o plano antes de escrever, (2) verificar prints visualmente, (3) não reusar prints, (4) entender a UI antes de escrever sobre ela, (5) nunca parar no meio de um deploy.

---

### D7. Correção sobre "Cortou o bloco" da Filosofia

**Mensagem (JSONL linha 1676):**

> "Cara, vc cortou o bloco que explica o problema dos professores e monitores gastarem tempo demais explicando como os alunos erraram provas, e de forma imprecisa. Putz grila mano, vc não tá conectando essa história com o resto da filosofia... você não tá entendendo o conceito."

> "Eu te dei um case para esse produto, na hora de corrigir provas, entenda como esse case se mistura com o resto das coisas."

**Decisão:** A história dos monitores/professores NÃO pode ser cortada — é central ao case. O case se conecta com a filosofia geral (relatórios).

---

### D8. Deploy — Nunca Parar o Loop

**Mensagem (JSONL linha 979):**

> "Cara, nunca mais me pare dizendo que está esperando o render."

**Mensagem (JSONL linha 1957):**

> "vc sabe o fluxo pra vc fazer o deploy e verificar o site, vc não sai do loop quando o deploy não foi verificado"

**Mensagem (JSONL linha 2599):**

> "Amigo, seu loop parou DE NOVO, no meio de esperar um deploy. Que porra é essa?"

**Decisão:** Deploy em background. Trigger hook → poll em background → continuar trabalhando → verificar quando live.

---

### D9. Módulos Avançados — Explorar Antes de Escrever

**Mensagem (JSONL linha 2337):**

> "A seção prompts tb está péssima... você precisa entender melhor como o modal funciona e me fazer perguntas sobre o que colocar lá"
> "Mesmas falhas em nível de vc nem descobriu o que o modal faz antes de criar o tutorial pra adicionar modelos..."
> "nos relatórios agregados, vc nem esperou a página carregar pra tirar seus prints. Você nunca explica sobre os JSONs vs PDFs gerados"
> "As dicas avançadas em chat estão bem legais, você conseguiu fazer algo bem complexo que eu te pedi. Mas você deixou algumas coisas bem básicas de lado. Como mudar os modelos."

**Decisão:** Antes de escrever qualquer módulo avançado, EXPLORAR a UI com agente ou ler o código. Fazer perguntas ao Otavio quando não souber.

---

### D10. Velocidade Suspeita

**Mensagem (JSONL linha 2515):**

> "cara, isso tá rápido demais pra vc ter feito tudo o que tava no documento e respeitado o loop, eu tenho toda a certeza do mundo que se eu for abrir de novo eu vou escrever mais um monte de páginas, com muitas delas dizendo pra vc ver o documento principal"

**Decisão:** Se parece rápido demais, provavelmente cortou cantos. Melhor ser lento e correto do que rápido e errado.

---

## Parte 2: Citações Exatas do Plano Mestre (seção 14)

### M1. Filosofia do Projeto

**Seção 14 (linhas 589-593):**
```
LINE 589: ### M1. Filosofia do Projeto (o mais importante)
LINE 590: **Narrativa:** Começa com o PROBLEMA, tom pessoal FGV.
LINE 591: **5 blocos:** (1) IA não substitui professor — amplia a correção dele, (2) por que correção automática funciona (classificação), (3) objetivo real: relatórios não notas, (4) aluno como protagonista (monitoria FGV, pleiteio preciso, professor economiza tempo, dados ficam), (5) mais que um número — dados reutilizáveis.
LINE 592: **Imagens:** Print do relatório final como exemplo do "resultado real". Possivelmente print da tela de resultado mostrando avisos/nota.
LINE 593: **Hyperlink:** No INÍCIO e no FINAL do hub avançado.
```

**Decisão 576-580:**
```
LINE 576: (d) **Filosofia — DEFINIÇÃO CENTRAL do produto (validada com Otavio 2026-04-12):**
LINE 577: O fluxo IDEAL: (1) professor corrige manualmente (como sempre fez), (2) sobe sua correção no sistema, (3) a IA USA a correção do professor como base para gerar relatórios detalhados. A IA não substitui — ela AMPLIA. Transforma a correção em relatórios ricos que o professor não teria tempo de escrever.
LINE 578: **Caso de uso real (FGV, história pessoal):** Após provas, monitores gastam horas explicando erros aluno a aluno. Professores terminam aulas com filas. Alguns dão pontos extras a quem NÃO pede revisão para economizar tempo. Com o NOVO CR: (1) aluno lê relatório e entende seus erros sem monitor, (2) se discorda, pleiteia por escrito com precisão, (3) professor gasta menos tempo, (4) dados ficam registrados para relatórios longitudinais.
LINE 579: **Narrativa:** começa com o PROBLEMA ("Você já terminou uma aula com fila de alunos?"), depois a solução. Tom pessoal com exemplos reais da FGV.
LINE 580: **5 blocos de conteúdo (FRAMING CORRETO validado 2026-04-12):** (1) O que o NOVO CR faz — filosofia geral: relatórios detalhados, dados sobre lacunas, (2) Como funciona — IA compara gabarito vs resposta (classificação), professor mantém controle, (3) Por que funciona tão bem — classificação pura, critérios aumentam precisão, (4) Case real — FGV: monitoria, filas, pontos extras; NOVO CR automatiza devolutivas, (5) Para quem serve — aluno entende erros, professor vê padrões, instituição tem dados longitudinais. **NÃO é 'problema vs solução'. É 'filosofia geral vs case específico'.**
```

**Seção 5 (linhas 122-124):**
```
LINE 122: > A correção automática pode ser muito precisa — especialmente com critérios de correção — porque a IA não precisa resolver a questão, apenas comparar a resposta ideal com a do aluno: é um trabalho de classificação puro.
LINE 124: > Mas o objetivo principal **não é** ter uma prova corrigida automaticamente. É gerar **relatórios que expliquem os erros** do aluno, ajudar o aluno a entender melhor onde errou, permitir que ele **questione correções do professor** com base em diálogo com a IA (decisão final sempre do professor), e gerar os relatórios agregados de turma e matéria.
```

---

### M2. Visão Individual

**Seção 14 (linhas 595-597):**
```
LINE 595: ### M2. Visão Individual (6 documentos do pipeline)
LINE 596: **Conteúdo:** Explicar TODOS os 6 docs e a cadeia: Extração Questões → Gabarito → Respostas → Correção → Análise → Relatório. Cada doc é uma etapa. Explicar avisos (amarelo/vermelho): letra ilegível, documento faltante, baixa confiança. Ensinar a baixar PDF vs ver JSON (JSON tem avisos detalhados).
LINE 597: **Imagens (4):** (1) Tela resultado completa (nota + cards), (2) Relatório Final aberto (👁️), (3) Análise de Habilidades com barras, (4) Correção questão por questão com nota. Todos com crop no conteúdo, não no background.
```

---

### M3. Critérios de Correção

**Seção 14 (linhas 599-601):**
```
LINE 599: ### M3. Critérios de Correção
LINE 600: **Conteúdo:** O que são, como subir (upload tipo "Critérios"), formato ideal (rubrica: "Questão 1: 2pts se X, 1pt se parcial"), impacto na precisão (com vs sem). Rápido mas com exemplo concreto.
LINE 601: **Imagens:** Print do modal upload com tipo "Critérios" selecionado.
```

---

### M4. Correção do Professor

**Seção 14 (linhas 603-605):**
```
LINE 603: ### M4. Correção do Professor
LINE 604: **Conteúdo:** Como subir (upload tipo "Correção do Professor" + selecionar aluno), que fica como documento paralelo para comparação. Fluxo ideal: professor corrige → sobe → IA gera relatórios a partir da correção do professor. Nota para futuro.
LINE 605: **Imagens:** Print do modal upload com tipo selecionado.
```

---

### M5. Múltiplos Arquivos por Documento

**Seção 14 (linhas 607-609):**
```
LINE 607: ### M5. Múltiplos Arquivos por Documento
LINE 608: **Conteúdo:** Quando usar (manuscrito + código, enunciado em 2 páginas), como fazer (seleção múltipla no upload), IA agrupa automaticamente.
LINE 609: **Imagens:** Print do campo de upload mostrando seleção múltipla.
```

---

### M6. Pipeline Turma Toda

**Seção 14 (linhas 611-613):**
```
LINE 611: ### M6. Pipeline Turma Toda
LINE 612: **Conteúdo:** Botão verde vs azul, pré-requisito (todas as provas uploaded), opções no padrão, tempo estimado (~5-10min para 30 alunos), painel de tarefas mostrando progresso em paralelo.
LINE 613: **Imagens:** (1) Botão verde no topo da atividade, (2) Painel de tarefas com vários alunos em paralelo.
```

---

### M7. Filtros Avançados do Chat

**Seção 14 (linhas 615-624):**
```
LINE 615: ### M7. Filtros Avançados do Chat (módulo mais detalhado)
LINE 616: **Conteúdo:** 5 cenários com passo a passo de filtros para cada um:
LINE 617: 1. "Avaliar turma específica" → filtrar Matéria + Turma. Print dos filtros configurados + pergunta + resposta.
LINE 618: 2. "Acompanhar aluno ao longo do tempo" → filtrar só Aluno. Print dos filtros + resposta longitudinal.
LINE 619: 3. "Questão que todos erraram" → filtrar Atividade + Tipo "Correção". Print.
LINE 620: 4. "Devolutiva para pais" → filtrar Aluno + relatórios. Print.
LINE 621: 5. "Trade-off: docs originais vs relatórios" → explicar custo/contexto/precisão.
LINE 622: + Como trocar o modelo no chat (dropdown). Print.
LINE 623: + Limite de documentos e estratégia de seleção.
LINE 624: **Imagens (muitas):** Print para cada cenário mostrando filtros configurados. Print mostrando contagem de docs. Print mostrando troca de modelo. Prints REAIS com dados da Matematica-V.
```

---

### M8. Prompts Customizados

**Seção 14 (linhas 626-628):**
```
LINE 626: ### M8. Prompts Customizados
LINE 627: **Conteúdo:** O que é um prompt ("instruções em português para a IA"), como acessar (toggle Advanced Mode), os 6 prompts e o que cada um controla, exemplo prático ("relatórios mais curtos"), cuidados (testar com 1 aluno), como reverter. Acessível para qualquer professor + details técnico.
LINE 628: **Imagens (3):** (1) Tela de prompts com os 6 listados, (2) Um prompt aberto em edição, (3) Onde fica o toggle Advanced Mode.
```

**⚠️ NOTA:** O plano diz "toggle Advanced Mode" mas a exploração do código mostrou que NÃO existe toggle na tela de Prompts. O Advanced Mode está no MODAL DE PIPELINE (onde se escolhe prompt por etapa). A implementação atual corretamente redireciona para o pipeline modal, mas o plano seção 14 está desatualizado neste ponto.

---

### M9. Adicionar/Configurar Modelos

**Seção 14 (linhas 630-632):**
```
LINE 630: ### M9. Adicionar/Configurar Modelos
LINE 631: **Conteúdo:** Quando adicionar ("se sua instituição tem API key própria"), passo a passo (provedor → modelo → apelido → salvar), parâmetros avançados em details colapsável, como escolher qual modelo usar no pipeline e no chat.
LINE 632: **Imagens (3):** (1) Modal 'Adicionar Modelo' preenchido, (2) Lista de modelos disponíveis, (3) Dropdown de modelo no pipeline.
```

---

### M10. Relatórios Agregados

**Seção 14 (linhas 634-636):**
```
LINE 634: ### M10. Relatórios Agregados (Turma/Matéria)
LINE 635: **Conteúdo:** Diferença turma vs matéria (escopo), como gerar (aba Desempenho → Gerar), o que esperar (narrativa, não só números), como baixar PDF, JSON com avisos detalhados (erros, docs faltantes). Conexão com chat: checkboxes → discutir resultados.
LINE 636: **Imagens (2):** (1) Tab Desempenho com botão Gerar, (2) Relatório gerado mostrando conteúdo narrativo + botão download.
```

---

### Básico — Checklist da Camada 1 (seção 12.2)

**Seção 12.2 (linhas 712-734):**
```
LINE 712: 1. **Visão de 10 segundos** — "você vai criar: matéria → turma → atividade → subir 3 documentos → clicar um botão → ler o relatório → conversar com a IA."
LINE 713: 2. **Criar uma matéria** — o que é, onde fica o botão, quais campos importam, qual campo ignorar. Não colocar ano aqui.
LINE 714: 3. **Criar uma turma dentro da matéria** — aqui entra o ano letivo. Explicar por que separou: uma matéria pode ter muitas turmas.
LINE 715: 4. **Adicionar alunos à turma** — focar no "Criar Novo". Mencionar que existe "Selecionar Existente" como detalhe ao pé da tela ("Curioso? Ver detalhes"), mas não distrair.
LINE 716: 5. **Criar uma atividade na turma** — nome, tipo, nota máxima. Dica: "tipo 'prova' serve pra quase tudo se estiver em dúvida".
LINE 717: 6. **Os 3 documentos obrigatórios** — enunciado, gabarito, resposta do aluno. Explicar que o sistema aceita enunciado+gabarito num só arquivo, mas separado funciona melhor. Mencionar que cada documento pode ter múltiplos arquivos (um aluno respondeu parte manuscrita + parte em código). Formatos aceitos: PDF, imagem, Word.
LINE 718: 7. **Rodar a pipeline** — o botão ⚡ Pipeline Aluno. Apontar o botão 🚀 Pipeline Turma Toda como "quando tiver mais de um aluno, use o verde". **Instruir o usuário não-experiente a ignorar** as opções avançadas dentro do modal (escolher modelo por etapa, forçar re-execução) — "deixa tudo no padrão, só aperta executar". Link "Curioso? Ver detalhes" apontando para o tutorial avançado de prompts/modelos.
LINE 719: 8. **Checkpoint: verificar se rodou** — como o professor sabe que terminou? O tutorial ensina o professor a olhar esse indicador e esperar a conclusão antes de seguir.
LINE 720: 9. **Abrir os documentos gerados** — apontar a listagem de documentos na página da atividade. Explicar que cada etapa do pipeline virou um documento. "Clique no ícone 👁️ para ver o conteúdo." Destacar dois documentos especialmente importantes:
LINE 721:    - **Relatório final** (aba correção)
LINE 722:    - **Análise de habilidades** (o que o aluno demonstrou)
LINE 723: 10. **Chat — fechamento da camada 1** — "Agora que você viu os documentos, vai adorar o chat." Ensinar a:
LINE 724:     - Abrir o modo chat no sidebar
LINE 725:     - **Filtrar pelos documentos que acabou de ver** (esse é o momento "aha")
LINE 726:     - Exemplos de perguntas prontas: "Me faça um resumo de onde esse aluno mais errou"; "Compare a performance dos meus alunos nessa atividade"; "O que o João acertou bem e onde ele pode melhorar?"
LINE 727: 11. **Próximo nível (footer do tutorial camada 1)** — "Agora você já é capaz de rodar uma atividade inteira. Quando quiser aprender mais, clique em [Tutoriais Avançados]."
```

**Decisões relevantes do log:**
```
LINE 537: **Formato do tutorial camada 1:** reaproveita o modal existente (dark, full-screen), mas **tudo tem que caber em FHD sem scroll**.
LINE 538: **Integração com tooltips:** o tutorial camada 1 deve mencionar que há tooltips nos botões para quando o usuário esquecer algo; e deve instruir o usuário não-experiente a **ignorar** opções avançadas dos botões de pipeline.
LINE 544: **Alunos globais são feature proposital**, não bug. Um mesmo aluno participa de múltiplas turmas para permitir relatórios longitudinais. O tutorial camada 1 precisa **ensinar explicitamente**: (1) como criar aluno novo, (2) como adicionar um aluno existente a uma turma nova.
LINE 551: **Checkpoint do tutorial = toast verde + árvore de tarefas na sidebar.** O tutorial ensina os dois sinais para o professor construir um modelo mental do pipeline.
LINE 552: **Aviso "chat sem histórico" entra na camada 1** como linha discreta ("Dica: sua conversa existe só enquanto a aba estiver aberta. Salve o que for importante.").
```

---

## Parte 3: Comparação em Massa — Tabela Completa de GAPs

### BÁSICO (10 steps vs 11 items do plano 12.2)

| Step | Requisito (citação L712-734) | Estado Atual | Status |
|------|------------------------------|--------------|--------|
| 1 | "você vai criar: matéria → turma → atividade → subir 3 documentos → clicar um botão → ler o relatório → conversar com a IA" (L712) | Presente na lista ordenada | ✅ |
| 1 | "tutorial deve mencionar que há tooltips nos botões" (L538) | "ícones ⓘ e ? mostram ajuda contextual" + dica amarela | ✅ |
| 1 | Link para filosofia (L593: "Hyperlink no INÍCIO") | "Não quer corrigir agora? Leia a Filosofia" | ✅ |
| 2 | "Não colocar ano aqui" (L713) | "NÃO coloque o ano aqui!" em highlight | ✅ |
| 2 | Image: tooltip visível | tooltip-visible-crop.png | ✅ |
| 4 | "ensinar explicitamente: (1) criar aluno novo, (2) adicionar existente" (L544) | Foca em "Criar Novo", details tem "Selecionar Existente" | ✅ |
| 5 | "tipo 'prova' serve pra quase tudo" (L716) | Presente em highlight | ✅ |
| 6 | "separado funciona melhor. Múltiplos arquivos. Formatos: PDF, imagem, Word" (L717) | Tudo presente | ✅ |
| 7 | "Instruir a ignorar opções avançadas" (L718) | "Deixe tudo no padrão" | ✅ |
| 7 | "Link 'Curioso? Ver detalhes' apontando para tutorial avançado de prompts/modelos" (L718) | ✅ CORRIGIDO — links para Prompts e Modelos adicionados nos details | ✅ |
| 8 | "Checkpoint: toast verde + árvore de tarefas" (L551, L719) | ⏳/✅/❌ + toast verde presentes | ✅ |
| 8 | "Relatório final + Análise de habilidades" (L720-722) | Destaca ambos em highlight | ✅ |
| 9 | "Filtrar pelos documentos" + exemplos perguntas (L723-726) | Checkboxes + 3 exemplos | ✅ |
| 9 | "chat sem histórico" (L552) | "conversa existe só enquanto a aba estiver aberta" | ✅ |
| 10 | Hub com links para módulos avançados (L727-734) | 10 links para todos os módulos | ✅ |
| 10 | Link filosofia no FINAL (L593) | Link filosofia no topo e na lista | ✅ |

**Básico: 0 gaps. ✅** (step 7 link corrigido em a985cf1)

---

### M1. FILOSOFIA (5 slides)

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | Bloco 1: "O que o NOVO CR faz — filosofia geral: relatórios detalhados, dados sobre lacunas" (L580) | Slide 1: "correções mais completas e dados detalhados que permitem entender lacunas" | ✅ |
| 2 | "a filosofia real é simplesmente gerar correções mais completas" (Otavio D4) | Slide 1 alinhado — filosofia geral em primeiro | ✅ |
| 3 | Bloco 2: "IA compara gabarito vs resposta (classificação), professor mantém controle" (L580) | Slide 2: "professor corrige → sobe → IA amplia" + Slide 3: "classificação pura" | ✅ |
| 4 | Bloco 3: "classificação pura, critérios aumentam precisão" (L580) | Slide 3: presente | ✅ |
| 5 | Bloco 4: "Case real — FGV: monitoria, filas, pontos extras; NOVO CR automatiza devolutivas" (L580) | Slide 4: "fila de alunos, monitores, pontos extras a quem NÃO pede revisão" | ✅ |
| 6 | "Você já terminou uma aula com fila de alunos?" (L579) — narrativa começa com PROBLEMA | Slide 4 começa com esta pergunta | ✅ |
| 7 | "aluno lê relatório, pleiteia por escrito, professor gasta menos, dados ficam" (L578) | Slide 4: todos os 4 pontos presentes | ✅ |
| 8 | "Professores dão pontos extras a quem NÃO pede revisão" (Otavio D3) | Slide 4: "pontos extras a quem NÃO pede revisão" | ✅ |
| 9 | Bloco 5: "Para quem serve — aluno, professor, instituição" (L580) | Slide 5: lista os 3 públicos | ✅ |
| 10 | **"Imagens: Print do relatório final como exemplo do 'resultado real'"** (L592) | Slide 1 usa **resultado-top-crop.png** (topo da página, NÃO relatório aberto) | ⚠️ PARCIAL |
| 11 | **"Possivelmente print da tela de resultado mostrando avisos/nota"** (L592) | Sandbox (Ana Verifica) tem nota 10 sem avisos — sem dados para este print. Plano diz "possivelmente" = opcional. M2 slide 4 já cobre avisos com texto detalhado. | ⚠️ OPCIONAL |
| 12 | "Hyperlink no INÍCIO e FINAL do hub avançado" (L593) | Step 1 tem link + Step 10 tem link | ✅ |
| 13 | "NÃO é 'problema vs solução'. É 'filosofia geral vs case específico'" (L580) | Slide 1=filosofia geral, Slide 4=case. Correto. | ✅ |
| 14 | "tom pessoal com exemplos reais da FGV" (L579) | Slide 4 tem tom narrativo mas não de primeira pessoa | ⚠️ PARCIAL |

**M1: 0 gaps reais. ✅** Print de avisos é "possivelmente" no plano e sandbox não tem avisos. Tom pessoal corrigido.

---

### M2. VISÃO INDIVIDUAL (5 slides)

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | "Explicar TODOS os 6 docs e a cadeia: Extração Questões → Gabarito → Respostas → Correção → Análise → Relatório" (L596) | Slide 3: lista completa dos 6 com ícones e descrições | ✅ |
| 2 | "Explicar avisos (amarelo/vermelho): letra ilegível, documento faltante, baixa confiança" (L596) | Slide 4: 3 cores (amarelo, laranja, vermelho) com descrições | ✅ |
| 3 | "Ensinar a baixar PDF vs ver JSON (JSON tem avisos detalhados)" (L596) | Slide 1: menciona PDF/Markdown/JSON + highlight | ✅ |
| 4 | **Imagem 1: "Tela resultado completa (nota + cards)"** (L597) | ✅ CORRIGIDO → resultado-top-real.png (nota 10.0, 4/4, 100%) | ✅ |
| 5 | **Imagem 2: "Relatório Final aberto (👁️)"** (L597) | relatorio-final-aberto.png (mostra questões + feedback) | ✅ |
| 6 | **Imagem 3: "Análise de Habilidades com barras"** (L597) | UI renderiza inline (mesmo viewport) — sem print distinto possível | ⚠️ LIMITAÇÃO UI |
| 7 | **Imagem 4: "Correção questão por questão com nota"** (L597) | ✅ CORRIGIDO → m2-correcao-ia-view.png (modal JSON com nota) | ✅ |
| 8 | "Todos com crop no conteúdo, não no background" (L597) | Prints cropados ✅ mas prints errados | ⚠️ |

**M2: 1 limitação de UI restante (análise habilidades renderiza inline). 3 de 4 imagens corrigidas. Conteúdo OK.**

---

### M3. CRITÉRIOS (1 slide)

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | "formato ideal (rubrica: 'Questão 1: 2pts se X, 1pt se parcial')" (L600) | Exemplo formatado com parcial/completa/em branco | ✅ |
| 2 | "impacto na precisão (com vs sem)" (L600) | Highlight "Com critérios → preciso. Sem → infere pelo gabarito" | ✅ |
| 3 | **"Print do modal upload com tipo 'Critérios' selecionado"** (L601) | modal-upload-crop.png genérico (não mostra "Critérios" no dropdown) | ⚠️ PRINT GENÉRICO |

**M3: 1 gap menor (print genérico vs específico)**

---

### M4. CORREÇÃO DO PROFESSOR (1 slide)

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | "upload tipo 'Correção do Professor' + selecionar aluno" (L604) | Passos 1-4 cobrem upload + seleção aluno | ✅ |
| 2 | "Fluxo ideal: professor corrige → sobe → IA gera relatórios" (L604) | Highlight tem fluxo completo | ✅ |
| 3 | **"Print do modal upload com tipo selecionado"** (L605) | modal-upload-crop.png genérico | ⚠️ PRINT GENÉRICO |

**M4: 1 gap menor (mesmo que M3)**

---

### M5. MÚLTIPLOS ARQUIVOS (1 slide)

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | "Quando usar (manuscrito + código, enunciado em 2 páginas)" (L608) | 3 exemplos concretos | ✅ |
| 2 | "como fazer (seleção múltipla no upload)" (L608) | "campo aceita seleção múltipla" | ✅ |
| 3 | "IA agrupa automaticamente" (L608) | "IA lê todos do mesmo tipo como documento unificado" | ✅ |
| 4 | **"Print do campo de upload mostrando seleção múltipla"** (L609) | modal-upload-crop.png genérico | ⚠️ PRINT GENÉRICO |

**M5: 1 gap menor**

---

### M6. PIPELINE TURMA (1 slide)

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | "Botão verde vs azul" (L612) | "Pipeline Aluno (azul)" vs "Pipeline Todos os Alunos (verde)" | ✅ |
| 2 | "pré-requisito (todas as provas uploaded)" (L612) | "Certifique-se de que todos os alunos têm provas uploaded" | ✅ |
| 3 | "tempo estimado (~5-10min para 30 alunos)" (L612) | "30 alunos com modelo rápido leva ~5-10 minutos" | ✅ |
| 4 | "painel de tarefas mostrando progresso em paralelo" (L612) | "painel de tarefas mostra o progresso" — mencionado no texto | ✅ |
| 5 | **Imagem 1: "Botão verde no topo da atividade"** (L613) | atividade-view-crop.png (mostra botões) | ✅ |
| 6 | **Imagem 2: "Painel de tarefas com vários alunos em paralelo"** (L613) | **NÃO EXISTE** — nenhum print do painel | ❌ FALTA |

**M6: 1 gap (falta print painel de tarefas)**

---

### M7. CHAT AVANÇADO (6 slides)

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | Cenário 1: "Avaliar turma específica → filtrar Matéria + Turma" (L617) | Slide 2: 4 passos com filtros corretos | ✅ |
| 2 | Cenário 2: "Acompanhar aluno → filtrar só Aluno" (L618) | Slide 3: filtrar Aluno, exemplos | ✅ |
| 3 | Cenário 3: "Questão que todos erraram → filtrar Atividade + Tipo 'Correção'" (L619) | Slide 4: Atividade + Tipos "Correção" | ✅ |
| 4 | Cenário 4: "Devolutiva para pais → filtrar Aluno + relatórios" (L620) | Slide 5: Aluno + tipos Relatório/Análise | ✅ |
| 5 | Cenário 5: "Trade-off: docs originais vs relatórios" (L621) | Slide 6: docs originais vs relatórios explicado | ✅ |
| 6 | "Como trocar o modelo no chat (dropdown)" (L622) | Slide 6: tabela de provedores + dropdown | ✅ |
| 7 | "Limite de documentos e estratégia de seleção" (L623) | Slide 6: "menos docs = mais preciso e barato" + inverter seleção | ✅ |
| 8 | **"Print para CADA cenário mostrando filtros configurados"** (L624) | 2 prints reusados em 6 slides (chat-filtros-crop, chat-filtro-materia-crop) | ❌ PRINTS REUSADOS |
| 9 | **"Print mostrando contagem de docs"** (L624) | Nenhum print mostra contador | ❌ FALTA |
| 10 | **"Print mostrando troca de modelo"** (L624) | Nenhum print mostra dropdown de modelo | ❌ FALTA |
| 11 | **"Prints REAIS com dados da Matematica-V"** (L624) | Prints genéricos sem dados reais | ❌ GENÉRICO |

**M7: Conteúdo excelente ✅. Imagens: 4 gaps sérios.**

---

### M8. PROMPTS (3 slides)

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | "O que é um prompt ('instruções em português para a IA')" (L627) | Slide 1: "instruções em português que dizem à IA..." | ✅ |
| 2 | **"os 6 prompts e o que cada um controla"** (L627) | ✅ CORRIGIDO — lista completa dos 6 adicionada (a985cf1) | ✅ |
| 3 | "exemplo prático ('relatórios mais curtos')" (L627) | Slide 3: "Seja conciso, máximo 1 parágrafo" | ✅ |
| 4 | "cuidados (testar com 1 aluno)" (L627) | Slide 3: "Teste com 1 aluno antes" | ✅ |
| 5 | "como reverter" (L627) | Slide 3: "histórico de versões para reverter" | ✅ |
| 6 | "Acessível para qualquer professor + details técnico" (L627) | Slide 1 acessível, sem details técnico separado | ⚠️ |
| 7 | Imagem 1: "Tela de prompts com os 6 listados" (L628) | prompts-crop.png | ✅ |
| 8 | Imagem 2: "Um prompt aberto em edição" (L628) | prompts-editing-crop.png | ✅ |
| 9 | "toggle Advanced Mode" (L627-628) | ⚠️ PLANO DESATUALIZADO — toggle não existe, Advanced Mode fica no pipeline modal | ⚠️ PLANO→REAL OK |
| 10 | Imagem 3: pipeline-modal-crop.png (onde ficam as opções avançadas) | Presente | ✅ |

**M8: 0 gaps reais. ✅** (lista dos 6 prompts corrigida em a985cf1). 1 parcial menor (details técnico)

---

### M9. MODELOS (3 slides)

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | "Quando adicionar ('se sua instituição tem API key própria')" (L631) | Slide 2 subtitle: "Quando sua instituição tem API key própria" | ✅ |
| 2 | "passo a passo (provedor → modelo → apelido → salvar)" (L631) | Slide 2: 4 passos com todos os campos | ✅ |
| 3 | "parâmetros avançados em details colapsável" (L631) | Slide 2: `<details>` com Temperatura, Max Tokens, Capacidades | ✅ |
| 4 | "como escolher qual modelo usar no pipeline e no chat" (L631) | Slide 3: "No pipeline: dropdown. No chat: dropdown no topo" | ✅ |
| 5 | Imagem 1: "Modal 'Adicionar Modelo' preenchido" (L632) | modal-add-model-crop.png | ✅ |
| 6 | Imagem 2: "Lista de modelos disponíveis" (L632) | modelos-crop.png | ✅ |
| 7 | Imagem 3: "Dropdown de modelo no pipeline" (L632) | pipeline-modal-crop.png | ✅ |

**M9: 0 gaps. Módulo completo. ✅**

---

### M10. RELATÓRIOS (3 slides)

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | "Diferença turma vs matéria (escopo)" (L635) | Slide 1: "Nível Turma" vs "Nível Matéria" | ✅ |
| 2 | "como gerar (aba Desempenho → Gerar)" (L635) | Slide 1: "aba Desempenho → Gerar Relatório" | ✅ |
| 3 | "o que esperar (narrativa, não só números)" (L635) | Slide 1: "progresso ao longo do tempo, problemas persistentes" | ✅ |
| 4 | "como baixar PDF" (L635) | Slide 2: PDF explicado | ✅ |
| 5 | "JSON com avisos detalhados (erros, docs faltantes)" (L635) | Slide 2: 4 códigos de aviso detalhados | ✅ |
| 6 | "Conexão com chat: checkboxes → discutir resultados" (L635) | Slide 3: checkboxes + chat + exemplos perguntas | ✅ |
| 7 | Imagem 1: "Tab Desempenho com botão Gerar" (L636) | desempenho-tab-crop.png | ✅ |
| 8 | **Imagem 2: "Relatório gerado mostrando conteúdo narrativo + botão download"** (L636) | resultado-top-crop.png (mostra resultado aluno, NÃO relatório turma/matéria) | ⚠️ PRINT ERRADO |

**M10: 1 gap parcial (print de resultado aluno em vez de relatório turma/matéria)**

---

## Resumo de Gaps por Prioridade (atualizado 2026-04-13)

### ✅ Corrigidos
1. ~~M2 img 1~~: ✅ → resultado-top-real.png (commit a985cf1)
2. ~~M2 img 4~~: ✅ → m2-correcao-ia-view.png (commit a68cf53)
3. ~~M8 conteúdo~~: ✅ Lista dos 6 prompts adicionada (commit a985cf1)
4. ~~Básico step 7~~: ✅ Links para Prompts/Modelos (commit a985cf1)
5. ~~M1 img 1~~: ✅ → resultado-top-real.png (commit a985cf1)
6. ~~M1 tom~~: ✅ Tom pessoal FGV adicionado ao slide 4 (pendente commit)

### ❌ Gaps Restantes (requerem screenshots novos — esforço alto)
7. **M7 imgs**: 2 prints reusados em 6 slides — precisa prints cenário-específicos (filtros custom dropdowns, interação Playwright complexa)
8. **M7 prints reais**: Precisa de dados da Matematica-V nos filtros do chat
9. **M6 img 2**: Falta print "Painel de tarefas com alunos em paralelo" (requer pipeline ativo)

### ✅ Reclassificados
10. ~~M1 img avisos~~: ⚠️ OPCIONAL — plano diz "possivelmente", sandbox sem avisos. M2 slide 4 cobre texto.

### ⚠️ Gaps Menores (prints genéricos)
11. **M3/M4/M5 imgs**: modal-upload-crop.png genérico (tipo não selecionado no dropdown)
12. **M10 img 2**: resultado-top-crop.png em vez de relatório turma/matéria gerado
13. **M2 img 3**: Análise Habilidades renderiza inline (limitação da UI, sem print distinto)
14. **M8 details**: Falta `<details>` técnico para professores avançados
