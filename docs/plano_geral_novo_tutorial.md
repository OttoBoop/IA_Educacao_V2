# Plano Geral — Novo Tutorial do NOVO CR

> **Documento vivo.** Atualizado a cada rodada de exploração e decisão entre usuário (Otavio) e Claude Code. Mudanças significativas são registradas em "Registro de decisões" no fim do arquivo.

---

## 0. Como ler este documento

Este arquivo é a fonte única de verdade para a reformulação do módulo de tutorial do NOVO CR. Ele descreve:

- **Mudanças grandes / principais** — reestruturações de arquitetura, novas seções, novos componentes, fluxos inteiros. Recebem sua própria subseção numerada em "Objetivos principais".
- **Explicações menores** — ajustes de copy, tooltips pontuais, pequenas melhorias de UX descobertas durante a auditoria. Vão para "Objetivos secundários" como itens de lista.

Toda pergunta aberta fica em "Perguntas abertas" até ser respondida; assim que a resposta chegar, a decisão migra para "Registro de decisões" com data.

---

## 1. Contexto do problema

O módulo de tutorial atual do NOVO CR (deploy: https://ia-educacao-v2.onrender.com) é muito centrado em **filosofia do projeto**. Isso tem dois efeitos ruins:

1. Um usuário novo abre o tutorial, vê texto denso sobre propósito e princípios, e sai sem saber **o que fazer para começar a usar a ferramenta**.
2. A ferramenta tem tooltips espalhadas em várias partes, mas:
   - Não é óbvio para usuários novos que elas existem.
   - Em alguns lugares críticos elas simplesmente não existem.

O tutorial atual **não pode ser removido** — ele contém material de filosofia que precisa permanecer acessível. Ele deve ser **arquivado** (ainda acessível, mas fora do caminho do usuário novo).

---

## 2. Objetivos principais

### 2.1 Refazer o tutorial em camadas

Estrutura em três camadas, cada uma opcional em relação à seguinte:

#### Camada 1 — Uso mínimo obrigatório

O usuário sai desta camada com **uma atividade analisada**. Passos:

1. Criar **matéria**
2. Criar **turma**
3. Adicionar **alunos** (novos ou já existentes)
4. Criar **atividade**
5. Enviar os **3 documentos-chave**:
   - Enunciado
   - Gabarito
   - Resposta do aluno
6. Rodar a **pipeline** (aluno individual)
7. Abrir o **relatório**

Tom: direto, imperativo, "faça isso, depois isso, depois isso". Sem filosofia.

#### Camada 2 — Melhorias opcionais

Só depois de concluir a camada 1:

- Critérios de correção (o professor define o que no gabarito dá quantos pontos)
- Correção final do professor (substitui a correção automática)
- Múltiplos arquivos por documento (ex.: aluno respondeu parte manuscrita + parte em código)
- Pipeline "turma toda" (roda tudo para todos os alunos de uma vez)

#### Camada 3 — Recursos avançados

Só no fim:

- Visão chat — conversar com a IA sobre qualquer conjunto de documentos
- Visão prompt — modificar prompts das pipelines
- Relatórios agregados (turma, matéria)
- Filosofia do projeto (link para o tutorial antigo arquivado)

### 2.2 Banner grandão na entrada

Um banner visível na entrada do site que **chama o usuário novo para o tutorial camada 1**. Detalhes (local, copy, CTA, comportamento dismiss/persistente) a definir após explorar o frontend.

### 2.3 Arquivar o tutorial antigo (não remover)

O conteúdo de filosofia continua acessível. A entrada no menu principal desaparece ou migra para "Sobre" / "Filosofia". O novo tutorial linka para ele explicitamente na camada 3.

### 2.4 Auditoria sistemática e expansão de tooltips

- Inventário completo: onde existem, onde faltam.
- Critério para "tooltip obrigatória" vs "tooltip supérflua".
- Sinalização visual universal para usuários novos de que uma tooltip existe (ex.: ícone ⓘ consistente).
- Definir se haverá um "tour guiado" no primeiro uso explicando que tooltips existem.

---

## 3. Objetivos secundários

_(a ser preenchido durante a auditoria — ajustes de copy, pequenas melhorias descobertas pelo caminho)_

- [ ] _pendente_

---

## 4. Modelo mental do produto (base do tutorial)

Vocabulário simplificado a usar no tutorial camada 1:

| Termo | Definição curta |
|-------|----------------|
| **Matéria** | A disciplina ou contexto analisado (ex.: "Cálculo 1", "Matemática — 9º ano"). Pode ser dada para múltiplas turmas. |
| **Turma** | Grupo específico dentro de uma matéria. |
| **Aluno** | Estudante vinculado a uma turma (pode ser reaproveitado entre turmas). |
| **Atividade** | Prova, teste, lista ou trabalho aplicado à turma. Aceita entrada multimodal: manuscrito escaneado, PDF, XLSX, Jupyter, código (.py, .html, .r…). |
| **Documentos obrigatórios** | Enunciado, gabarito e resposta do aluno. O sistema aceita enunciado+gabarito unificados, mas separado dá melhor performance. Cada tipo pode ter múltiplas submissões. |
| **Documentos opcionais** | Critérios de correção, correção final do professor. |
| **Pipeline (nível atividade)** | Dois botões: "pipeline aluno" (um aluno) e "pipeline turma toda" (todos). Extrai questões do enunciado, encontra a resolução ideal pelo gabarito, faz correção automática (se não houver a do professor), gera relatórios em PDF. |
| **Níveis de relatório** | Atividade, aluno, turma, matéria. |
| **Visão chat** | Professor ou aluno conversa com IA filtrando documentos, gera relatórios customizados. |
| **Visão prompt** | Permite modificar os prompts das pipelines para casos específicos. |

**Mensagem-chave para o tutorial (copy de referência):**

> Com os três documentos principais (enunciado, gabarito, resposta do aluno), o sistema já consegue corrigir e gerar relatórios. Os documentos complementares servem para refinar a análise.

---

## 5. Filosofia do projeto (vai para o tutorial antigo arquivado e para a camada 3)

> A correção automática pode ser muito precisa — especialmente com critérios de correção — porque a IA não precisa resolver a questão, apenas comparar a resposta ideal com a do aluno: é um trabalho de classificação puro.
>
> Mas o objetivo principal **não é** ter uma prova corrigida automaticamente. É gerar **relatórios que expliquem os erros** do aluno, ajudar o aluno a entender melhor onde errou, permitir que ele **questione correções do professor** com base em diálogo com a IA (decisão final sempre do professor), e gerar os relatórios agregados de turma e matéria.

---

## 6. Inventário do estado atual (Fase B — rodada 1, 2026-04-11)

### 6.1 Tutorial atual

**Tudo vive no `index_v2.html`** (client-side puro, nenhum endpoint de backend serve conteúdo de tutorial):

- [frontend/index_v2.html:6118-6399](../frontend/index_v2.html#L6118) — objeto JS `tutorialContent` com **dois modos**:
  - **"⚡ 3 Passos Essenciais"** (quick, 4 passos, default ao abrir)
  - **"📚 Completo (12 passos)"** (full)
- [frontend/index_v2.html:5707-5736](../frontend/index_v2.html#L5707) — markup do `#modal-tutorial` (overlay full-screen, max-width 900px, 85vh)
- [frontend/index_v2.html:2404-2663](../frontend/index_v2.html#L2404) — CSS (`.modal-tutorial`, `.tutorial-*`) auto-contido, usa variáveis do tema (`--primary`, `--bg-card`, etc.)
- [frontend/index_v2.html:7243-7326](../frontend/index_v2.html#L7243) — funções `openTutorial()`, `closeTutorial()`, `switchTutorialMode()`, `renderTutorialStep()` e navegação
- [frontend/tutorial-images-v2/](../frontend/tutorial-images-v2/) — **14 screenshots anotados** (`01-dashboard.png` … `14-resultados.png`, ~3.8 MB)

**Entradas/acessos:**
- Sidebar: botão de ajuda (📖) [index_v2.html:4558](../frontend/index_v2.html#L4558) → `onclick="openWelcome()"`
- Modal "Welcome" [index_v2.html:5696-5698](../frontend/index_v2.html#L5696) tem botão "Tutorial Interativo"
- Footer: link "📖 Ver tutorial completo" [index_v2.html:6828](../frontend/index_v2.html#L6828)
- **Primeiro acesso:** `checkFirstVisit()` [index_v2.html:7328-7333](../frontend/index_v2.html#L7328) abre o Welcome automaticamente, usando `localStorage.getItem('novocr-welcomed')`

**Conteúdo — tom atual:**

O **quick mode** já tenta dar um passo a passo, mas o passo 1 abre com "O NOVO CR **não é só um corretor automático**" seguido de um bloco `tutorial-highlight` de filosofia — exatamente o problema que Otavio descreveu. O passo 2 trata de estrutura (Matéria → Turma → Atividade), o passo 3 fala do pipeline conceitualmente, o passo 4 fala de chat.

O **full mode** tem 12 passos; o passo 1 é puro "🎯 A Filosofia do NOVO CR" (4 princípios). Os passos 2–7 correspondem ao caminho prático (criar matéria, turma, alunos, atividade, upload, pipeline). O passo 8 é configurar IA, o 9 visualizar resultados, 10 chat, 11 "aluno também usa o chat".

**Idioma:** PT-BR puro.

**Visual:** modal dark theme, tabs no topo, conteúdo scrollável, rodapé com dots de progresso + prev/next. Classes `.tutorial-*` próprias.

**Arquivável sem quebrar?** Sim, acoplamento é mínimo:
- Nenhum backend envolvido
- Dependências: cadeia `openWelcome()` → `openTutorial()` ([index_v2.html:5696](../frontend/index_v2.html#L5696)) e a flag `novocr-welcomed` ([index_v2.html:7329](../frontend/index_v2.html#L7329))
- Overlay click-to-close [index_v2.html:7386-7399](../frontend/index_v2.html#L7386) é compartilhado com o welcome modal

**Design guides:** os arquivos `../.claude/design/STYLE_GUIDE.md` e `../.claude/design/UI_ELEMENT_CATALOG.md` citados no `CLAUDE.md` **não existem no repo**. O tutorial já usa as variáveis de tema consistentes, então não há bloqueio visual.

### 6.2 Tooltips existentes

**Dois padrões coexistem:**
- `data-tooltip` + `data-tooltip-pos` (CSS `::before`/`::after`, custom, cobrindo ~44 elementos)
- `title="..."` nativo do browser (~34 elementos — não descobrível, só dispara no hover cego)
- `.tooltip-icon` (ⓘ 16×24 px, `cursor: help`) e `.section-help` (? 28×28 px em cabeçalhos) — os dois affordances visuais usados hoje

**Onde estão cobertos hoje (bom):**

| Área | Exemplo | Referência |
|------|---------|-----------|
| Sidebar nav | "Converse com a IA sobre seus documentos e provas" | [index_v2.html:4498](../frontend/index_v2.html#L4498) |
| Sidebar settings | "Configure API Keys e modelos de IA. ⚠️ Área técnica" | [index_v2.html:4549](../frontend/index_v2.html#L4549) |
| Upload modal (tipo de documento) | "Cada tipo tem um propósito no pipeline…" | [index_v2.html:4747](../frontend/index_v2.html#L4747) |
| Modal Executar Etapa | Título, stage select, prompt select | [index_v2.html:4908-4933](../frontend/index_v2.html#L4908) |
| Modal Pipeline Completo | Título + prompt | [index_v2.html:4975](../frontend/index_v2.html#L4975), [5013](../frontend/index_v2.html#L5013) |
| Modal Configurar Modelo | Nome, provider, max tokens, temperature, reasoning effort, features | [5429-5569](../frontend/index_v2.html#L5429) |
| Seção "?" headers | Dashboard, Matéria, Turma, Atividade, Providers, Chat | [7507](../frontend/index_v2.html#L7507), [8190](../frontend/index_v2.html#L8190), [8275](../frontend/index_v2.html#L8275), [8383](../frontend/index_v2.html#L8383), [8696](../frontend/index_v2.html#L8696), [8822](../frontend/index_v2.html#L8822) |
| Botões de pipeline na atividade | "Execute uma etapa específica…", "Corrige automaticamente a prova de um aluno…", "…TODOS os alunos…" | [8393-8396](../frontend/index_v2.html#L8393) |
| Prompts page | "O que são prompts?" | [frontend/prompts.js:88](../frontend/prompts.js#L88) |
| Chat | Minimizar, Inverter seleção, Limpar conversa | [frontend/chat_system.js:113](../frontend/chat_system.js#L113), [138](../frontend/chat_system.js#L138), [311](../frontend/chat_system.js#L311) |

### 6.3 Tooltips faltando (buracos críticos para usuário novo)

Cobertura de campos de formulário: **~30%** (40 de 131 campos). Os buracos concentram-se exatamente nos modais de **criação inicial** — o caminho da camada 1.

| Prioridade | Campo | Onde |
|------------|-------|------|
| **ALTA** | "Nome da Matéria" (modal criar matéria) | [index_v2.html:4599](../frontend/index_v2.html#L4599) |
| MÉDIA | "Descrição" da matéria | [4603](../frontend/index_v2.html#L4603) |
| MÉDIA | "Nível de Ensino" | [4607](../frontend/index_v2.html#L4607) |
| **ALTA** | "Nome da Turma" | [4633](../frontend/index_v2.html#L4633) |
| MÉDIA | "Ano Letivo" | [4637](../frontend/index_v2.html#L4637) |
| MÉDIA | "Período" | [4641](../frontend/index_v2.html#L4641) |
| **ALTA** | "Nome da Atividade" | [4662](../frontend/index_v2.html#L4662) |
| MÉDIA | "Tipo" de atividade (prova/trabalho/exercício/outro) | [4666](../frontend/index_v2.html#L4666) |
| MÉDIA | "Nota Máxima" | [4675](../frontend/index_v2.html#L4675) |
| MÉDIA | "Nome Completo" do aluno | [4713](../frontend/index_v2.html#L4713) |
| MÉDIA | "Matrícula" | [4717](../frontend/index_v2.html#L4717) |
| **ALTA** | **Distinção entre "documentos obrigatórios" vs "opcionais"** na activity view | não há label/tooltip explícita |
| **ALTA** | **"Modo de identificação"** no upload em lote | [4863](../frontend/index_v2.html#L4863) |
| **ALTA** | "Forçar re-execução" (checkbox pipeline) | [5042](../frontend/index_v2.html#L5042) |
| ALTA | Toggles do chat ("all/filtered/manual") — o usuário precisa adivinhar | chat_system.js |

**Helper reutilizável:** o CSS `[data-tooltip]::before` já faz tudo — **zero custo** para adicionar uma tooltip nova (uma linha HTML). Não há dependência de tippy/popper/etc.

**Onboarding:** **não há** tour guiado (nenhum intro.js/shepherd/driver). O Welcome modal fala das **features** mas **não explica que há ⓘ/? clicáveis pelo app** — essa é provavelmente a maior causa de "tooltip existe mas usuário novo não sabe".

### 6.4 Fluxo de criação (matéria → turma → aluno → atividade → documentos → pipeline → relatório)

**Entrada no app:** [frontend/index_v2.html:8137](../frontend/index_v2.html#L8137) `showDashboard()` — dashboard + cards de estatísticas (`/api/estatisticas`) + grid de matérias (`/api/materias`). Sidebar mostra árvore Matérias → Turmas → Atividades.

**Criar Matéria:** modal [4591-4622](../frontend/index_v2.html#L4591), fields `nome` (req), `descricao`, `nivel` (dropdown). Função `criarMateria()` [10083-10097](../frontend/index_v2.html#L10083) → **POST `/api/materias`** [backend/main_v2.py:431](../backend/main_v2.py#L431).

**Criar Turma:** modal [4625-4651](../frontend/index_v2.html#L4625), fields `nome` (req), `ano_letivo`, `periodo`. `criarTurma()` [10099](../frontend/index_v2.html#L10099) → **POST `/api/turmas`** [main_v2.py:486](../backend/main_v2.py#L486).

**Adicionar Aluno:** modal [4688-4734](../frontend/index_v2.html#L4688) com **2 tabs**:
- **Selecionar Existente** — busca é **global** (todos os alunos já criados), não filtra pela turma. Isso é confuso.
- **Criar Novo** — `nome`, `matricula`, `email`.

`criarAluno()` [10131](../frontend/index_v2.html#L10131) faz **2 chamadas**: POST `/api/alunos` cria globalmente [main_v2.py:542](../backend/main_v2.py#L542), POST `/api/alunos/vincular` liga à turma [main_v2.py:574](../backend/main_v2.py#L574). **Alunos são reutilizáveis entre turmas** — confere com a filosofia do tutorial.

**Criar Atividade:** modal [4654-4685](../frontend/index_v2.html#L4654), fields `nome` (req), `tipo` (prova/trabalho/exercicio/outro), `nota_maxima` (default 10). `criarAtividade()` [10115](../frontend/index_v2.html#L10115) → **POST `/api/atividades`** [main_v2.py:596](../backend/main_v2.py#L596).

**Upload de documentos:** modal [4737-4793](../frontend/index_v2.html#L4737). Dropdown de 5 tipos:
- `enunciado` 📄
- `gabarito` ✅
- `criterios_correcao` 📋
- `prova_respondida` 👤 (exige selecionar um `aluno_id`)
- `correcao_professor` 🧑‍🏫

Input aceita **apenas** `.pdf,.docx,.doc,.png,.jpg,.jpeg` [index_v2.html:4778](../frontend/index_v2.html#L4778) — mas o backend suporta muito mais (`.py`, `.xlsx`, Jupyter, etc. via `anexos.py`). **Divergência UI ↔ backend a esclarecer.** Input tem `multiple`, então dá para mandar vários arquivos de uma vez para o mesmo tipo. `uploadDocumento()` → **POST `/api/documentos/upload`** [main_v2.py:648](../backend/main_v2.py#L648).

**Pipeline — 3 botões na atividade** [index_v2.html:8393-8396](../frontend/index_v2.html#L8393):
1. **⚙️ Executar Etapa** — stage único, abre `modal-execucao` [4903](../frontend/index_v2.html#L4903)
2. **⚡ Pipeline Aluno** (azul) — aluno individual, abre `modal-pipeline-completo` [4970](../frontend/index_v2.html#L4970) mode='aluno'
3. **🚀 Pipeline Todos os Alunos** (verde) — mesmo modal, mode='turma'

Modal completo tem override por etapa em accordion, checkbox "Forçar re-execução".

**Relatórios:** após rodar, botão "Ver Resultado" [8420](../frontend/index_v2.html#L8420) em `showResultadoAluno()` [11230](../frontend/index_v2.html#L11230) → **GET `/api/resultados/{atividade_id}/{aluno_id}`**. Tipos de relatório listados [6430-6436](../frontend/index_v2.html#L6430):
- `relatorio_final` (individual)
- `relatorio_narrativo` (deprecated)
- `relatorio_desempenho_tarefa`
- `relatorio_desempenho_turma`
- `relatorio_desempenho_materia`

Agregados de turma/matéria via tab "📊 Desempenho" [8289](../frontend/index_v2.html#L8289). **Atenção:** essa tab existe tanto no nível turma quanto no nível atividade e o comportamento é diferente — sem nenhum aviso visual.

**Chat e Prompts:** chat sempre visível no sidebar [4497](../frontend/index_v2.html#L4497). **Prompts está escondido** atrás de um toggle "Advanced Mode" (classe `.technical-item`, body class `show-technical`) [56](../frontend/index_v2.html#L56) + [8673](../frontend/index_v2.html#L8673) — confere com o plano de colocar Prompts na camada 3.

### 6.5 Pontos de fricção e dívidas técnicas encontradas

1. **Upload aceita lista pequena de formatos** mas backend é multimodal — UI mente por omissão [index_v2.html:4778](../frontend/index_v2.html#L4778).
2. **Tipos de documento deprecated** (`CORRECAO_NARRATIVA`, `ANALISE_HABILIDADES_NARRATIVA`, `RELATORIO_NARRATIVO`) ainda no enum [backend/models.py:60-68](../backend/models.py#L60); frontend não marca.
3. **"Selecionar Existente" de aluno** é global — usuário espera que mostre só alunos da turma atual.
4. **Tab "📊 Desempenho"** existe em turma *e* atividade com escopo diferente e sem distinção visual.
5. **Fallbacks silenciosos do executor** (ex.: "Narrative PDF generation failed" → estrutura JSON) — warnings só aparecem nos logs, usuário não sabe.

---

## 7. Banner — especificação _(pendente)_

- **Local:** _a definir_
- **Copy (PT-BR):** _a definir_
- **CTA:** _a definir_
- **Comportamento:** _a definir_ (dismiss persistente? reaparece para novos usuários? cookie?)
- **Arquivos a alterar:** _a descobrir na Fase B_

---

## 8. Arquivamento do tutorial antigo _(pendente)_

- **Localização atual do conteúdo:** _a descobrir_
- **Nova localização (rota/arquivo):** _a definir_
- **Como será linkado a partir do novo tutorial:** _a definir_

---

## 9. Perguntas abertas

### Rodada 1 — após o inventário (2026-04-11)

**Sobre arquivamento do tutorial atual:**

1. **Onde mora o conteúdo arquivado?** Opções:
   - (a) Ficar dentro do próprio `modal-tutorial`, mas como um terceiro tab "📚 Filosofia (material antigo)" — mantém tudo num lugar só.
   - (b) Virar uma rota/view separada tipo "Sobre / Filosofia" acessível pelo rodapé ou por um link no fim do novo tutorial.
   - (c) Extrair o objeto `tutorialContent` inteiro para um arquivo JS separado (ex.: `frontend/tutorial_archive.js`) e o novo modal só importar os passos novos.
2. **O que fazer com os 14 screenshots** em `frontend/tutorial-images-v2/`? Todos permanecem (só relinkados na versão arquivada) ou vamos **gerar screenshots novos** para o novo tutorial camada 1 (mais curto, só os 7 passos)?
3. **A flag `localStorage 'novocr-welcomed'`** deve ser **resetada** quando o tutorial novo for publicado, para que usuários recorrentes vejam o novo welcome? Ou usar uma flag nova (ex.: `novocr-welcomed-v2`) para garantir que ninguém perca o tour refeito?

**Sobre o banner:**

4. **Onde exatamente o banner deve aparecer?**
   - (a) Faixa no topo do dashboard (acima dos cards de estatísticas)
   - (b) Card grande ocupando o espaço do grid de matérias **enquanto não existir nenhuma matéria criada** (empty state transformado em banner)
   - (c) Modal overlay bloqueando a tela no primeiro acesso (como o welcome atual faz)
   - (d) Uma combinação (ex.: modal no 1º acesso + faixa persistente no topo até o usuário completar a camada 1)
5. **Deve ser dismissable?** Se sim, ele volta a aparecer em sessões futuras ou desaparece para sempre?
6. **Deve desaparecer automaticamente** depois que o usuário completar a camada 1 (detectável checando se existe pelo menos uma matéria + turma + atividade com 3 documentos)? Ou continua aparecendo até dismiss manual?

**Sobre a camada 1 (uso mínimo obrigatório):**

7. **Formato do novo tutorial:** o modal atual (dark, full-screen, tabs, dots de progresso) serve para a camada 1? Ou você quer algo mais leve, tipo um **checklist lateral persistente** (sidebar step-by-step que fica visível enquanto o usuário faz as ações de verdade no app)?
8. **O tutorial camada 1 deve ser interativo** (destacando os botões reais da UI com `driver.js`/`shepherd.js`) ou continua sendo só um modal explicativo com screenshots como é hoje?
9. **Sobre o passo "Adicionar aluno"** — hoje a tab "Selecionar Existente" busca globalmente. No tutorial camada 1, recomendo mostrar **só o caminho "Criar Novo"** para não confundir o usuário novo. Concorda? Ou você quer explicar as duas opções já no tutorial inicial?
10. **Sobre a divergência de formatos no upload** — `.pdf,.docx,.doc,.png,.jpg,.jpeg` na UI vs backend multimodal. O tutorial deve:
    - (a) Só falar dos formatos que a UI aceita hoje (e depois abrir um ticket separado para expandir a UI)
    - (b) Ser honesto sobre a multimodalidade e **como parte do trabalho** corrigir o `accept` do input
    - (c) Mencionar que "outros formatos podem ser experimentados" sem prometer

**Sobre tooltips:**

11. **Hint global de descoberta:** você topa adicionarmos um **passo explícito no novo welcome/tutorial camada 1** dizendo algo como _"Ao longo do app você vai ver ícones ⓘ e ? — passe o mouse ou clique para ver ajuda contextual"_? Isso resolveria o maior problema de descoberta por ~zero custo.
12. **Padronização:** hoje convivem `title=""` nativo (não descobrível) e `data-tooltip` custom (descobrível com ⓘ). Posso migrar os `title=""` dos lugares críticos para `data-tooltip` com ícone? Isso é trabalho de varredura — quer que eu faça isso **durante** o tutorial ou em um passo separado?
13. **Prioridade ALTA** na seção 6.3: nome da matéria, nome da turma, nome da atividade, distinção obrigatório/opcional, modo de upload em lote, força re-execução. Essas todas entram na fase de implementação do tutorial, certo? Tem alguma que você quer adiar?

**Sobre arquitetura geral:**

14. **O arquivo `index_v2.html` está gigantesco** (>12.000 linhas). As mudanças deveriam tentar **extrair o módulo do tutorial para um arquivo próprio** (`frontend/tutorial_v2.js` ou similar), ou você prefere que eu edite in-place para minimizar risco?
15. **Testes:** o CLAUDE.md insiste em rodar `pytest` e validar no deploy live. Para mudanças principalmente de frontend (tutorial + tooltips), você quer que eu:
    - (a) Rode a suíte full antes de cada commit
    - (b) Rode só a suíte `tests/ui/` + smoke tests
    - (c) Commite e valide no `/journey` depois
16. **Deploy:** o CLAUDE.md diz "auto-deploys on push to main" e "tarefa só está completa após verificação live". Enquanto estamos construindo, você quer que os commits vão direto pra `main` (arriscado, vai pro ar toda hora) ou numa **branch de feature** tipo `tutorial-rework`?

---

## 10. Registro de decisões

| Data | Decisão | Contexto |
|------|---------|----------|
| 2026-04-11 | Reposiório clonado em `/home/otavio/Documents/vscode/prova-ia-v2`. | Primeira configuração. |
| 2026-04-11 | Documento vivo criado em `docs/plano_geral_novo_tutorial.md`. | Decidido durante o plan mode. |
| 2026-04-11 | Tutorial será reestruturado em 3 camadas (mínimo obrigatório / opcional / avançado). | Herdado da conversa do Otavio com o ChatGPT; validado no plano. |
| 2026-04-11 | Tutorial antigo será **arquivado**, não removido (contém filosofia do projeto). | Decisão direta do Otavio. |
| 2026-04-11 | Claude commita localmente a cada mudança sem perguntar, mas não dá push automático. | Resposta do Otavio na rodada de perguntas iniciais. |
| 2026-04-11 | Regra de iteração: após cada fatia de exploração, Claude **para** e volta ao usuário com perguntas antes de seguir. | Pedido explícito do Otavio após a primeira proposta de plano. |
| 2026-04-11 | Fase B rodada 1 executada: 3 agentes Explore mapearam tutorial atual, tooltips e fluxo de criação. Achados consolidados nas seções 6.1–6.5 e 16 perguntas abertas registradas na seção 9. | Primeira rodada do loop explorar-parar-perguntar. |

---

## 11. Próximos passos imediatos

1. ~~Lançar agentes Explore para mapear tutorial atual, tooltips, fluxo de criação.~~ ✅ 2026-04-11
2. ~~Consolidar achados nas seções 6.1–6.5.~~ ✅ 2026-04-11
3. **Parar e fazer as perguntas da seção 9 ao Otavio.** ← ESTAMOS AQUI
4. Incorporar respostas na seção 10 (registro de decisões) e atualizar seções 7 (banner), 8 (arquivamento) e abrir seção nova 12 "Plano de implementação camada 1" com detalhes acionáveis.
5. Só então decidir se precisamos de mais rodadas de exploração (ex.: executor/backend para entender melhor o pipeline; estados de erro; textos do Welcome modal) antes de começar a implementar.
