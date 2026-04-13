# Skill: Audit Loop — Citações vs Implementação

> **Status:** Design em andamento. Baseado na experiência real do tutorial NOVO CR (2026-04-13).

## O Problema que Esta Skill Resolve

Quando um LLM implementa um plano longo (10+ requisitos), ele tende a:
1. **Ler o plano superficialmente** — pegar a ideia geral, perder detalhes
2. **Escrever de memória** — ao implementar item 7, já esqueceu os termos exatos do item 2
3. **Reusar artefatos** — mesma imagem em 3 slides, mesmo padrão em 3 módulos
4. **Declarar pronto sem verificar** — "fiz tudo" quando 40% dos requisitos não foram atendidos
5. **Não incorporar feedback do usuário** — correções dadas verbalmente se perdem entre iterações

**Resultado:** O usuário precisa revisar manualmente, encontrar as falhas, e pedir correção múltiplas vezes. Trabalho quadruplicado.

## A Solução: Audit Doc como Fonte de Verdade

Antes de implementar, criar um documento intermediário (`audit.md`) que:
1. Extrai **citações exatas** do plano com line numbers
2. Extrai **citações exatas** das mensagens do usuário (decisões, correções, feedback)
3. Compara cada citação contra o **estado atual** do artefato
4. Gera uma **tabela de gaps** com status (❌/⚠️/✅)
5. Cada iteração do loop referencia essa tabela
6. Após cada fix, a tabela é atualizada

## Como Funcionou na Prática (NOVO CR Tutorial)

### Fase 1: Sem Audit Doc (resultado ruim)

O loop era:
```
1. Ler plano (superficialmente)
2. Escrever conteúdo
3. Commitar
4. "Pronto!"
```

**Problemas encontrados pelo usuário:**
- Filosofia invertida (case FGV como objetivo, não como exemplo)
- Mesma imagem em 3 slides
- Módulos escritos sem entender a UI
- "Advanced Mode toggle" que não existe
- Prints sem crop (background inteiro visível)
- Declaração de "pronto" sem verificar deploy

### Fase 2: Com Audit Doc (resultado bom)

O loop mudou para:
```
1. EXTRAIR citações exatas do plano (com line numbers)
2. EXTRAIR citações exatas do usuário (do JSONL da conversa)
3. COMPARAR cada citação contra o código atual
4. GERAR tabela de gaps
5. Para cada gap ❌:
   a. Reler a citação exata
   b. Implementar a correção
   c. VERIFICAR visualmente (prints → Read)
   d. Marcar ✅ na tabela
   e. Commitar
6. Repetir até todos ✅
```

**Resultado:** 14 gaps identificados, 14 corrigidos, cada um verificado.

## Anatomia do Audit Doc

### Parte 1: Decisões do Usuário

Citações verbatim das mensagens do usuário, organizadas por tópico. Cada uma com:
- **Identificação**: de onde veio (JSONL line number, data, contexto)
- **Citação**: texto exato (não parafraseado)
- **Decisão**: o que isso implica para a implementação

Exemplo:
```markdown
### D4. Hierarquia — Filosofia Geral vs Case Específico

**Mensagem (JSONL linha 2337):**
> "hey, essa é a filosofia geral: construir relatórios. Vs hey, aqui está um case."

**Decisão:** Slide 1 da filosofia DEVE ser filosofia geral. Case FGV vem DEPOIS.
```

### Parte 2: Citações do Plano

Texto exato do documento de plano, com line numbers. Para cada módulo/seção:
- Requisitos de conteúdo (o que o texto deve dizer)
- Requisitos de imagem (que prints/assets são necessários)
- Decisões do log que afetam este módulo

Exemplo:
```markdown
### M7. Filtros Avançados do Chat

**Seção 14 (linhas 615-624):**
LINE 616: **Conteúdo:** 5 cenários com passo a passo de filtros para cada um:
LINE 617: 1. "Avaliar turma específica" → filtrar Matéria + Turma.
LINE 624: **Imagens (muitas):** Print para cada cenário mostrando filtros configurados.
          Prints REAIS com dados da Matematica-V.
```

### Parte 3: Tabela de Gaps

Comparação sistemática. Para cada módulo:

| # | Requisito (citação) | Estado Atual | Status |
|---|---------------------|--------------|--------|
| 1 | "Print para CADA cenário" (L624) | 2 prints reusados em 6 slides | ❌ |
| 2 | "Prints REAIS com dados" (L624) | Prints genéricos | ❌ |

Status: ❌ = diverge, ⚠️ = parcial, ✅ = correto

## Generalização: Os 5 Passos da Skill

### Passo 1: Identificar Fontes
- **Plano**: arquivo .md, PRD, spec, ticket
- **Feedback do usuário**: mensagens na conversa, JSONL de sessões anteriores
- **Artefato**: código, HTML, config, etc.

### Passo 2: Extrair Citações
Para cada fonte, extrair citações EXATAS com localização:
- Do plano: line numbers + texto verbatim
- Do usuário: timestamp/ID + texto verbatim
- Organizar por tópico/módulo (não cronologicamente)

**Técnica:** Lançar agentes haiku em paralelo para extrair citações de diferentes seções. Cada agente recebe uma seção e retorna citações formatadas.

### Passo 3: Extrair Estado Atual
Para cada módulo do plano, ler o artefato correspondente:
- Código: ler funções, conteúdo, configs relevantes
- Assets: listar imagens, verificar visualmente
- Resumir o que EXISTE (não o que deveria existir)

### Passo 4: Gerar Tabela de Gaps
Para cada citação do plano, comparar com o estado atual:
- Se bate: ✅
- Se bate parcialmente: ⚠️ com nota do que falta
- Se diverge ou falta: ❌ com descrição da divergência

**Ordenar por prioridade:** ❌ primeiro, ⚠️ depois, ✅ por último.

### Passo 5: Loop de Correção
Para cada gap ❌:
1. Reler a citação exata (não confiar na memória)
2. Implementar a correção
3. Verificar (visualmente se asset, no código se texto)
4. Atualizar tabela: ❌ → ✅
5. Commitar com referência ao gap
6. Não parar o loop para esperar deploy

## Lições Aprendidas (específicas desta experiência)

### O que funcionou
1. **Citações exatas eliminam ambiguidade** — "o plano diz X" é verificável, "eu acho que o plano queria Y" não é
2. **Tabela de gaps é accountability** — impossível declarar "pronto" com 5 ❌ na tabela
3. **Agentes haiku para extração** — baratos e rápidos para copiar texto de documentos grandes
4. **Verificação visual de prints** — Read no .png antes de integrar, não depois
5. **Atualizar a tabela após cada fix** — mantém o estado visível

### O que não funcionou (e como melhorar)
1. **Loop parava para esperar deploy** — deveria ser background poll
2. **Playwright screenshots complexos** — dropdowns customizados exigem interação específica, não genérica
3. **Plano desatualizado** (M8 "toggle Advanced Mode") — precisa de mecanismo para notar divergência plano↔realidade
4. **Sandbox sem dados ideais** — aluno com nota 10 sem avisos limita screenshots de edge cases

### Métricas desta aplicação
- **14 gaps** identificados na comparação
- **14 corrigidos** (12 diretamente, 2 reclassificados com justificativa)
- **8 commits** na fase com audit doc (vs ~10 commits na fase sem, com resultado pior)
- **24 imagens distintas** no tutorial final
- **~2 horas** de trabalho total com audit doc

## Próximos Passos para Virar Skill

1. **Definir o formato de input** — como o usuário invoca a skill (ex: `/audit plano.md artefato.html`)
2. **Template do audit doc** — frontmatter + seções padrão
3. **Automação da extração** — agente que lê plano e gera Parte 2 automaticamente
4. **Automação da comparação** — agente que lê artefato e preenche Parte 3
5. **Integração com /loop** — o loop consulta a tabela de gaps automaticamente
6. **Formato de decisões do usuário** — como capturar e organizar feedback em tempo real (não só post-hoc do JSONL)
