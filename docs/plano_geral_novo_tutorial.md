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

## 6. Inventário do estado atual _(preencher após Fase B)_

### 6.1 Tutorial atual
- **Arquivos:** _a descobrir_
- **Rota/acesso:** _a descobrir_
- **Conteúdo:** _a descobrir_
- **Como o usuário chega nele:** _a descobrir_

### 6.2 Tooltips existentes
_(inventário completo — localização, copy, qualidade)_

### 6.3 Tooltips faltando
_(lugares onde um usuário novo trava por falta de explicação)_

### 6.4 Fluxo de criação (matéria → turma → aluno → atividade → documentos → pipeline)
_(mapa componente-a-componente, pontos de fricção)_

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

_(Claude acumula aqui as perguntas que surgirem durante a exploração. Quando o usuário responder, a decisão migra para a seção 10.)_

- _a preencher após Fase B_

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

---

## 11. Próximos passos imediatos

1. Lançar agentes `Explore` em paralelo para mapear:
   - Tutorial atual (arquivos, rota, conteúdo)
   - Tooltips existentes (padrão, cobertura, lacunas críticas)
   - Fluxo de criação (matéria → turma → aluno → atividade → documentos → pipeline)
2. Consolidar achados nas seções 6.1–6.4.
3. **Parar** e fazer perguntas direcionadas ao Otavio (seção 9).
4. Incorporar respostas na seção 10 e avançar para a próxima fatia.
