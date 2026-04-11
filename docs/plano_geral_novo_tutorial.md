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

### 6.5 Sistema atual de "primeiro acesso" (rodada 2 de exploração)

**Componentes:**
- **Modal HTML:** [frontend/index_v2.html:5617-5704](../frontend/index_v2.html#L5617) — `#modal-welcome`, classe `.modal-overlay.modal-welcome`. Cabeçalho: _"🧪 PROTÓTIPO"_, _"🎓 Bem-vindo ao NOVO CR"_, _"Sistema de correção automática de provas e análise educacional com IA"_. Dois botões: **🎓 Tutorial Interativo** (verde, abre o modal de tutorial) e **Começar a Usar →** (azul, só fecha). Tem checkbox "Não mostrar novamente" mas a lógica atual **sempre** persiste o dismiss (ver abaixo).

**Cadeia de chamadas no page load:**
1. `DOMContentLoaded` em [index_v2.html:7361](../frontend/index_v2.html#L7361)
2. Chama `checkFirstVisit()` em [index_v2.html:7374](../frontend/index_v2.html#L7374)
3. `checkFirstVisit()` [7328-7333](../frontend/index_v2.html#L7328):
   ```js
   function checkFirstVisit() {
     const welcomed = localStorage.getItem('novocr-welcomed');
     if (!welcomed) setTimeout(() => openWelcome(), 500);
   }
   ```
4. Se for primeira visita, `openWelcome()` [7224-7232](../frontend/index_v2.html#L7224) ativa o overlay.

**Persistência:**
- **Chave:** `localStorage.getItem('novocr-welcomed')` / `setItem('novocr-welcomed', 'true')`
- **Tipo:** `localStorage` puro (não sessionStorage, não cookie, **nenhum tracking server-side**)
- **Escrita:** `closeWelcome()` [7234-7241](../frontend/index_v2.html#L7234) **sempre** grava `'true'` ao fechar — o checkbox "Não mostrar novamente" visual não tem efeito diferente do close normal
- **Onde o close é disparado:** botões "Começar a Usar" [5699](../frontend/index_v2.html#L5699), "Tutorial Interativo" (via `closeWelcome()` na cadeia), e clique fora do overlay [7391-7392](../frontend/index_v2.html#L7391)

**"Novo dispositivo" = o quê na prática:**
- `localStorage` é por **origin + navegador + perfil**, então o welcome reaparece em:
  - Outra máquina
  - Outro navegador (Chrome ↔ Firefox) na mesma máquina
  - Modo anônimo/incógnito (flag perde ao fechar a aba)
  - Dev/prod se for URL diferente
- **Não há reconhecimento cross-device.** Usuário volta no celular = welcome aparece de novo.

**Resetar manualmente (para Otavio testar):**
```js
localStorage.removeItem('novocr-welcomed');
location.reload();
```

**Outras flags localStorage relacionadas:**
- `'novocr-view-mode'` — `'visual'` ou `'json'`, toggle entre visões de documento ([6862](../frontend/index_v2.html#L6862), [6883](../frontend/index_v2.html#L6883)). Nada a ver com tutorial.
- **Nenhuma** outra flag relacionada a tutorial/onboarding. Variáveis `currentTutorialMode`/`currentTutorialStep` em [6401-6402](../frontend/index_v2.html#L6401) são **in-memory** — fechar e reabrir o tutorial volta para o passo 0.

**Version-busting — NÃO EXISTE:** se só atualizarmos `tutorialContent`, usuários com `novocr-welcomed = true` **nunca vão ver o novo tutorial automaticamente**. Terão que clicar no botão de ajuda no sidebar. **Implicação para o banner novo:** precisamos usar uma **chave nova** (ex.: `novocr-welcomed-v2` ou `novocr-tutorial-version = 2`) para garantir que usuários recorrentes sejam reapresentados ao grito.

**Encapsulamento (o que quebra se rippar):** o sistema é totalmente encapsulado. Dependências: `modal-welcome` HTML, `checkFirstVisit/openWelcome/closeWelcome`, chamada em DOMContentLoaded, botão de ajuda (`help-btn`) com `onclick="openWelcome()"` [4558](../frontend/index_v2.html#L4558), CSS `.modal-welcome` [2154](../frontend/index_v2.html#L2154), [3436](../frontend/index_v2.html#L3436). Nenhuma outra feature depende disso.

### 6.6 Pontos de fricção e dívidas técnicas encontradas

1. **Upload aceita lista pequena de formatos** mas backend é multimodal — UI mente por omissão [index_v2.html:4778](../frontend/index_v2.html#L4778).
2. **Tipos de documento deprecated** (`CORRECAO_NARRATIVA`, `ANALISE_HABILIDADES_NARRATIVA`, `RELATORIO_NARRATIVO`) ainda no enum [backend/models.py:60-68](../backend/models.py#L60); frontend não marca.
3. **"Selecionar Existente" de aluno** é global — usuário espera que mostre só alunos da turma atual.
4. **Tab "📊 Desempenho"** existe em turma *e* atividade com escopo diferente e sem distinção visual.
5. **Fallbacks silenciosos do executor** (ex.: "Narrative PDF generation failed" → estrutura JSON) — warnings só aparecem nos logs, usuário não sabe.

---

## 7. Banner / welcome "gritão" — especificação (v1, 2026-04-11)

**Objetivo:** na primeira vez que um professor abre o site, a tela inteira precisa **gritar visualmente** que ele está diante de um protótipo novo e que, se está em dúvida sobre o que fazer, **PRECISA** ler as próximas páginas.

**Base técnica:** aproveitar o modal `#modal-welcome` e a cadeia `checkFirstVisit → openWelcome → closeWelcome` documentada em 6.5, **substituindo o conteúdo** e **usando uma chave nova** (`novocr-welcomed-v2` ou `novocr-tutorial-version`) para que usuários com a flag antiga sejam reapresentados ao grito.

**Elementos visuais (rascunho — refinar com Otavio):**
- Borda grossa **vermelha + amarela alternadas** (tipo "AVISO")
- Badge `!!!` no topo, talvez com animação pulse
- Título enorme tipo **"⚠️ PRIMEIRA VEZ AQUI? LEIA ISTO!"** (CAIXA ALTA, emojis, exclamações)
- Subtítulo curto, em vermelho, do tipo _"Se você ainda não sabe o que fazer, não feche esta janela sem ler os próximos 7 passos."_
- CTA primário **único e óbvio**: _"➡️ QUERO COMEÇAR AGORA"_ (verde, grande, pulse)
- Link secundário pequeno, no rodapé: _"já conheço, pular (não recomendado)"_
- Animação sutil de pulse/shake para chamar atenção, sem ser epilético

**Comportamento:**
- Aparece no primeiro acesso (flag nova ausente)
- Aparece também para usuários antigos (`novocr-welcomed = true` mas sem a flag nova) — a primeira vez que subirmos o banner novo, todo mundo vê.
- Close persistente (`novocr-welcomed-v2 = 'true'`). Pode ser reaberto pelo botão de ajuda no sidebar.
- Enquanto o usuário não tem nenhuma matéria criada, o **empty state do dashboard** reforça: "Você ainda não tem nenhuma matéria. Quer ver o tutorial?" (decisão menor, valida-se depois).

**Arquivos a alterar (previsão):**
- [frontend/index_v2.html:5617-5704](../frontend/index_v2.html#L5617) — conteúdo do `modal-welcome` reescrito
- [frontend/index_v2.html:7328-7333](../frontend/index_v2.html#L7328) — `checkFirstVisit()` muda a chave
- [frontend/index_v2.html:7234-7241](../frontend/index_v2.html#L7234) — `closeWelcome()` grava a chave nova
- CSS novo: classe `.welcome-scream` com borda/pulse (em [index_v2.html:2154](../frontend/index_v2.html#L2154) ou num bloco novo)

**Pontos pendentes de decisão:**
- Copy exata do título e subtítulo (usuário confirma)
- Quantas páginas o grito apresenta antes de entregar o usuário no modal do tutorial (é uma tela só com CTA, ou um mini-fluxo de 2-3 telas dentro do próprio welcome?)
- Se o modal do tutorial camada 1 abre **automaticamente** ao clicar o CTA ou se o CTA só fecha o welcome e deixa o dashboard visível com o empty state reforçado

---

## 8. Arquivamento do tutorial antigo (v1, 2026-04-11)

**Decisão:** o tutorial atual é **rippado do frontend**, mas salvo como arquivo HTML standalone para referência posterior. Marcado como `DEPRECATED`.

**Plano:**
1. Criar `docs/tutorial_arquivado_v1.html` contendo:
   - O conteúdo dos 12 passos do modo "Completo" + 4 passos do modo "Quick" (extraídos do objeto `tutorialContent` [6118-6399](../frontend/index_v2.html#L6118)).
   - As imagens em [frontend/tutorial-images-v2/](../frontend/tutorial-images-v2/) linkadas via caminho relativo.
   - Cabeçalho grande: **`DEPRECATED — conteúdo de referência, não exposto ao usuário final`**. Data do snapshot. Link para a tag `v1.3.0-pre-tutorial-rework`.
   - Nota: contém ideias de filosofia que podem ser reaproveitadas numa view "Sobre / Filosofia" futura.
2. Remover do `index_v2.html`:
   - `tutorialContent` (quick + full)
   - Funções relacionadas (`switchTutorialMode`, `renderTutorialStep`) — ou mantê-las esqueleto para o tutorial novo reusar o modal
   - Entradas do tipo "Tutorial Interativo" no welcome antigo (o "grito" novo tem seu próprio CTA)
3. **Manter** [frontend/tutorial-images-v2/](../frontend/tutorial-images-v2/) por enquanto — a pasta é usada pelo HTML arquivado; decidir depois se vai para `docs/assets/`.
4. O tutorial novo (camada 1) **reusa a infraestrutura** do modal de tutorial atual (CSS, `openTutorial`/`closeTutorial`) com conteúdo totalmente novo.
5. Depois que a camada 1 estiver estável, abrir um ticket separado para a **view de Filosofia** (reaproveitando prosa do arquivado).

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
| 2026-04-11 | **Arquivamento:** o tutorial antigo é **rippado do frontend** e salvo como arquivo HTML standalone (ex.: `docs/tutorial_arquivado_v1.html`) para Otavio/IA consultarem depois. Marcado como DEPRECIADO. Depois criaremos uma *view nova* de filosofia, mas só após a camada 1 estar clara. | Resposta direta do Otavio rodada 1. |
| 2026-04-11 | **Banner — primeira chamada:** o welcome modal atual é a base, mas a primeira chamada precisa **GRITAR visualmente** — borda vermelha e amarela, elementos piscando, exclamações. "Se é a primeira vez do professor aqui, ele PRECISA ler as próximas páginas." Depois desse grito entram as explicações do sistema base. | Resposta direta rodada 1. |
| 2026-04-11 | **Formato do tutorial camada 1:** reaproveita o modal existente (dark, full-screen), mas **tudo tem que caber em FHD sem scroll** (ponto fraco do atual). Visual é secundário — o importante é o passo a passo básico bem claro: matéria → turma → alunos → atividades + documentos base → botões para gerar relatórios → chat para consultas customizadas. | Resposta direta rodada 1. |
| 2026-04-11 | **Integração com tooltips:** o tutorial camada 1 deve mencionar que há tooltips nos botões para quando o usuário esquecer algo; e deve instruir o usuário não-experiente a **ignorar** opções avançadas dos botões de pipeline. Curiosos vão para o tutorial avançado. | Resposta direta rodada 1. |
| 2026-04-11 | **Tutoriais avançados planejados** (pós-camada-1, escopo a detalhar): documentos individuais do pipeline do aluno; modificação de prompts e modelos; adicionar novos modelos; trocar modelos na função chat; filtros avançados no chat; leitura dos relatórios automáticos (vai precisar rodada de exploração dedicada para entender cada um). | Resposta direta rodada 1. |
| 2026-04-11 | **Screenshots:** o tutorial atual tem imagens pouco explicativas. Futuramente, capturar novas imagens vai exigir um loop de altíssima qualidade (tirar → revisar → refazer). Por ora, o novo tutorial **não precisa ser muito visual** — prioridade é o texto do passo a passo. | Resposta direta rodada 1. |
| 2026-04-11 | **Branch/deploy:** commits vão direto na `main` (review do Otavio depende do site do Render, que só auto-deploya a partir da main). Antes de começar, criar um **tag de backup** (versão "pré-mudança de tutorial") como rollback point. | Resposta direta rodada 1. |
| 2026-04-11 | **Tag de backup criada e empurrada:** `v1.3.0-pre-tutorial-rework` (tags anteriores eram `v1.0.0` e `v1.2.0`). Rollback: `git checkout v1.3.0-pre-tutorial-rework`. | Executado. |
| 2026-04-11 | **Sistema de primeiro acesso investigado** (rodada 2 de exploração). Resumo na seção 6.6. Implicação: quando colocarmos o banner novo, temos que usar uma **flag nova** (ex.: `novocr-welcomed-v2`) para garantir que usuários que já marcaram a antiga como vista vejam o grito novo. | Decorrente da pergunta do Otavio sobre "como guardamos que é um novo dispositivo". |
| 2026-04-11 | **Alunos globais são feature proposital**, não bug. Um mesmo aluno participa de múltiplas turmas para permitir relatórios longitudinais (acompanhar um aluno através de matérias/anos). O tutorial camada 1 precisa **ensinar explicitamente**: (1) como criar aluno novo, (2) como adicionar um aluno existente a uma turma nova. A UI não muda. | Resposta direta do Otavio. |
| 2026-04-11 | **Relatórios longitudinais automáticos ainda não existem como pipeline**; Otavio já criou alguns manualmente via prompts de teste no chat. Implicação para o tutorial avançado: o caminho "análise cross-turma" hoje passa pelo **chat + filtros + prompts customizados**, não por um botão dedicado. Guardar esses prompts como material de referência quando formos escrever o tutorial avançado dos relatórios automáticos. | Info lateral do Otavio na mesma resposta. |

---

## 12. Copy rascunhado v1 — grito + checklist da camada 1 (2026-04-11)

> **Status:** rascunho para revisão do Otavio. Edite direto neste arquivo se quiser mudar palavras; Claude só toca no `index_v2.html` depois da sua aprovação.

### 12.1 O grito (banner de primeiro acesso)

**Tom decidido:** alerta urgente, quase assustador. Caixa alta, emojis de alerta, 3–4 exclamações no título, borda vermelha+amarela pulsando. Objetivo: **máxima chance de o usuário não fechar sem ler**.

**Layout proposto (uma tela só, cabe em FHD sem scroll):**

```
┌─────────────────────────────────────────────┐
│  🔴🟡🔴🟡🔴🟡 BORDA PISCANDO 🔴🟡🔴🟡🔴🟡  │
│                                             │
│              !!!  ⚠️  !!!                    │
│                                             │
│     PARE! PRIMEIRA VEZ AQUI?                │
│     LEIA ANTES DE FECHAR!!!                 │
│                                             │
│   Este é o NOVO CR — um protótipo de       │
│   correção e análise pedagógica com IA.    │
│                                             │
│   Se você ainda não sabe o que fazer,      │
│   NÃO feche esta janela.                   │
│   Em poucos minutos você sai daqui com     │
│   sua primeira prova analisada.            │
│                                             │
│   ┌─────────────────────────────────────┐  │
│   │ ➡️  QUERO COMEÇAR AGORA (recomendado)│  │
│   └─────────────────────────────────────┘  │
│                                             │
│       já conheço, pular (não recomendado)  │
│                                             │
│  🔴🟡🔴🟡🔴🟡 BORDA PISCANDO 🔴🟡🔴🟡🔴🟡  │
└─────────────────────────────────────────────┘
```

**Copy exato (PT-BR):**

- **Badge superior:** `!!!  ⚠️  !!!` (animação: pulse lento)
- **Título (h1, caixa alta, vermelho sobre fundo escuro):**
  > PARE! PRIMEIRA VEZ AQUI?
  > LEIA ANTES DE FECHAR!!!
- **Parágrafo 1 (normal, centralizado):**
  > Este é o **NOVO CR** — um protótipo de correção e análise pedagógica com IA.
- **Parágrafo 2 (vermelho, negrito parcial):**
  > Se você ainda não sabe o que fazer, **NÃO feche esta janela**. Em poucos minutos você sai daqui com sua primeira prova analisada.
- **CTA primário (botão verde enorme, pulse, emoji à esquerda):**
  > ➡️  QUERO COMEÇAR AGORA
- **Link secundário (rodapé, pequeno, cinza):**
  > já conheço, pular (não recomendado)

**Comportamento:**
- Aparece quando `localStorage.getItem('novocr-welcomed-v2') === null`
- Clique no CTA primário: `localStorage.setItem('novocr-welcomed-v2','true')` + fecha o banner + abre **direto** o modal do tutorial camada 1 no passo 1
- Clique no link secundário: mesma flag, fecha o banner, **não abre** o tutorial (o professor caiu de para-quedas mas sabe o que faz)
- Reabrir manualmente: botão de ajuda (📖) no sidebar (já existe, só aponta para o mesmo modal)

**CSS:** nova classe `.welcome-scream` com:
- `border: 8px solid transparent` + `background-image` animado alternando vermelho/amarelo (ou `@keyframes` na borda)
- `box-shadow: 0 0 40px red` pulsando
- Backdrop preto 90% opacidade para travar o foco
- **Não usar flash/blink intenso** — respeita usuários com sensibilidade a luz (pulse lento de 1.5s, não 200ms)

---

### 12.2 Checklist da camada 1 — o que o tutorial precisa cobrir

**IMPORTANTE:** a lista abaixo é um **checklist de conceitos**, não uma lista de páginas. A divisão em páginas/telas só vai ser decidida depois de escrevermos o texto e medirmos o que cabe em FHD sem scroll. Algumas entradas podem virar uma tela só; outras podem caber juntas; outras podem virar uma tela com um link "ver detalhes" no rodapé.

**Sequência pedagógica:**

1. **Visão de 10 segundos** — "você vai criar: matéria → turma → atividade → subir 3 documentos → clicar um botão → ler o relatório → conversar com a IA."
2. **Criar uma matéria** — o que é, onde fica o botão, quais campos importam, qual campo ignorar. Não colocar ano aqui.
3. **Criar uma turma dentro da matéria** — aqui entra o ano letivo. Explicar por que separou: uma matéria pode ter muitas turmas.
4. **Adicionar alunos à turma** — focar no "Criar Novo". Mencionar que existe "Selecionar Existente" como detalhe ao pé da tela ("Curioso? Ver detalhes"), mas não distrair.
5. **Criar uma atividade na turma** — nome, tipo, nota máxima. Dica: "tipo 'prova' serve pra quase tudo se estiver em dúvida".
6. **Os 3 documentos obrigatórios** — enunciado, gabarito, resposta do aluno. Explicar que o sistema aceita enunciado+gabarito num só arquivo, mas separado funciona melhor. Mencionar que cada documento pode ter múltiplos arquivos (um aluno respondeu parte manuscrita + parte em código). Formatos aceitos: PDF, imagem, Word. (**Nota interna:** a UI hoje só aceita esses; a divergência com o backend multimodal é um ticket separado.)
7. **Rodar a pipeline** — o botão ⚡ Pipeline Aluno. Apontar o botão 🚀 Pipeline Turma Toda como "quando tiver mais de um aluno, use o verde". **Instruir o usuário não-experiente a ignorar** as opções avançadas dentro do modal (escolher modelo por etapa, forçar re-execução) — "deixa tudo no padrão, só aperta executar". Link "Curioso? Ver detalhes" apontando para o tutorial avançado de prompts/modelos (ainda a construir).
8. **Checkpoint: verificar se rodou** — como o professor sabe que terminou? (painel de tarefas? ícone verde? timestamp? **precisamos explorar isso**: agente novo para mapear como o frontend mostra "pipeline rodou com sucesso" hoje.) O tutorial ensina o professor a olhar esse indicador e esperar a conclusão antes de seguir.
9. **Abrir os documentos gerados** — apontar a listagem de documentos na página da atividade. Explicar que cada etapa do pipeline virou um documento. "Clique no ícone 👁️ para ver o conteúdo." Destacar dois documentos especialmente importantes:
   - **Relatório final** (aba correção)
   - **Análise de habilidades** (o que o aluno demonstrou)
10. **Chat — fechamento da camada 1** — "Agora que você viu os documentos, vai adorar o chat." Ensinar a:
    - Abrir o modo chat no sidebar
    - **Filtrar pelos documentos que acabou de ver** (esse é o momento "aha" que o Otavio pediu: o filtro do chat é o que amarra tudo)
    - Exemplos de perguntas prontas: "Me faça um resumo de onde esse aluno mais errou"; "Compare a performance dos meus alunos nessa atividade"; "O que o João acertou bem e onde ele pode melhorar?"
11. **Próximo nível (footer do tutorial camada 1)** — "Agora você já é capaz de rodar uma atividade inteira. Quando quiser aprender mais, clique em [Tutoriais Avançados]." Link para:
    - Pipeline detalhada (cada etapa e seus documentos)
    - Modificação de prompts e modelos
    - Adicionar novos modelos
    - Trocar modelos no chat
    - Filtros avançados do chat
    - Relatórios agregados (turma, matéria)
    - Filosofia do projeto (será a futura "view Sobre")

### 12.3 Padrão do "Curioso? Ver detalhes"

Em cada passo da camada 1, no rodapé, pequeno, cinza, sublinhado:

> 🔍 Curioso? Ver detalhes

Quando clicado, expande uma caixa com:
- Explicações do que foi omitido do passo principal
- Links para o tutorial avançado relacionado (se existir)
- Eventualmente, pointers para as tooltips reais da UI ("esse campo tem uma dica ao passar o mouse")

**Estilo:** não substitui o passo principal. É um **opt-in** para quem quer mergulhar. Fica colapsado por padrão.

### 12.4 Pontos onde falta informação para fechar o copy

O Claude precisa **explorar mais antes** de escrever o texto final de alguns passos. Pergunta ao usuário: autorizar estas novas rodadas de exploração?

- **Passo 8 (checkpoint verificar):** como o painel de tarefas (`task-panel`) mostra que o pipeline terminou? Há ícone verde/vermelho/timestamp? É automático ou o professor tem que dar refresh? Um agente Explore resolve.
- **Passo 9 (abrir documentos):** a listagem real de documentos da atividade após a pipeline. Ordem? Ícones? Rótulos? Se o "Relatório final" está claramente identificado ou se o professor precisa saber onde procurar.
- **Passo 10 (chat + filtro):** como o filtro do chat funciona hoje? Ele filtra por matéria/turma/atividade/documento individual? Quão fácil é "filtrar pelos docs que acabei de ver"? Pode ser que a gente precise ajustar a UI do filtro ANTES de escrever o tutorial — se o filtro é ruim, explicar vira explicar um bug.
- **Tutoriais avançados:** Claude não sabe hoje o suficiente sobre cada relatório automático para documentar direito. O Otavio precisa ou detalhar isso por texto, ou autorizar agente Explore para ler código do executor e mapear cada relatório.

---

## 11. Próximos passos imediatos

1. ~~Lançar agentes Explore para mapear tutorial atual, tooltips, fluxo de criação.~~ ✅ 2026-04-11
2. ~~Consolidar achados nas seções 6.1–6.5.~~ ✅ 2026-04-11
3. **Parar e fazer as perguntas da seção 9 ao Otavio.** ← ESTAMOS AQUI
4. Incorporar respostas na seção 10 (registro de decisões) e atualizar seções 7 (banner), 8 (arquivamento) e abrir seção nova 12 "Plano de implementação camada 1" com detalhes acionáveis.
5. Só então decidir se precisamos de mais rodadas de exploração (ex.: executor/backend para entender melhor o pipeline; estados de erro; textos do Welcome modal) antes de começar a implementar.
