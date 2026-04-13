# Análise do Workflow: O que Aconteceu vs O que Deveria Ter Acontecido

> **Objetivo:** Documentar o workflow real desta conversa para identificar padrões, falhas e oportunidades de automação. Isso vai virar a base de uma ou mais skills.

---

## 1. Os Documentos que Existiram

### A. Grande Plano (`plano_geral_novo_tutorial.md`, ~950 linhas)
- **Criado quando:** Início do projeto (sessão anterior)
- **O que contém:** Filosofia (seção 5), inventário (seção 6), decisões (seção 10), copy rascunhado (seção 12), specs de módulos (seção 14)
- **Quem alimenta:** Otavio (decisões) + Claude (exploração técnica)
- **Problema:** É o documento de REFERÊNCIA, mas o loop não o consultava sistematicamente. Claude lia "a seção 14" por cima e escrevia de memória.

### B. Plano de Curto Prazo (`cuddly-dazzling-moore.md`, plan file do Claude)
- **Criado quando:** Após a primeira rodada de críticas do Otavio
- **O que contém:** Lista de tarefas imediatas (Streams A/B/C), checklist por iteração, regras do loop
- **Problema 1:** Não referenciava o grande plano com citações exatas — dizia "reordenar filosofia" mas não citava as linhas 576-580 do plano.
- **Problema 2:** Não era atualizado durante o loop — ficou estático enquanto o trabalho avançava.
- **Problema 3:** Desconectado do grande plano — se o grande plano mudasse, o curto não refletia.

### C. Decisões do Otavio (dispersas nos prompts da conversa)
- **Onde estavam:** No chat, como mensagens de texto. Algumas foram copiadas para o grande plano (seção 10), muitas não.
- **Problema:** Após compactação do contexto, as mensagens originais desapareciam. O Claude perdia acesso às palavras exatas do Otavio e trabalhava com paráfrases da memória.
- **Exemplo concreto:** Otavio disse 3 vezes que FGV é um CASE, não o objetivo. Claude continuou invertendo porque a correção verbal se perdeu entre iterações.

### D. Audit Doc (`audit_quotes_vs_implementation.md`, criado nesta sessão)
- **Criado quando:** Após a segunda rodada de críticas
- **O que contém:** Citações exatas do plano + citações do Otavio + tabela de gaps
- **Funcionou:** Sim. 14 gaps identificados, 14 corrigidos.
- **Problema:** Foi criado TARDE. Se existisse desde o início, a primeira rodada teria sido muito melhor.

---

## 2. O que Falhou e Por Quê

### Falha 1: Loop sem fonte de verdade granular
**O que aconteceu:** O loop lia "seção 14" do plano e implementava de memória.
**Por que falhou:** 950 linhas de plano não cabem na memória de trabalho. Detalhes específicos ("4 imagens DISTINTAS", "tom pessoal FGV") se perdiam.
**O que resolveu:** O audit doc extraiu as citações relevantes POR MÓDULO, tornando a comparação direta possível.

### Falha 2: Decisões do Otavio não eram persistidas como citações
**O que aconteceu:** Otavio corrigia verbalmente ("hey, filosofia geral vs case"). Claude entendia na hora, mas na próxima iteração já tinha esquecido os termos exatos.
**Por que falhou:** Mensagens do chat são efêmeras — compactação elimina o texto original. Memory files capturam a DECISÃO mas não a CITAÇÃO EXATA.
**O que resolveria:** Um documento vivo de "Decisões do Otavio" atualizado EM TEMPO REAL, não extraído post-hoc do JSONL.

### Falha 3: Plano de curto prazo desconectado do grande plano
**O que aconteceu:** O plano de curto prazo dizia "corrigir M7 imagens" sem especificar QUAIS imagens o grande plano pedia, com que dados, em que formato.
**Por que falhou:** O curto prazo era uma LISTA DE TAREFAS, não uma SPEC. Quando o Claude ia implementar, tinha que reler o grande plano — e relia superficialmente.
**O que resolveria:** O plano de curto prazo deveria CITAR o grande plano. "Corrigir M7 imagens" → "M7 L624: 'Print para cada cenário mostrando filtros configurados. Prints REAIS com dados da Matematica-V.' Estado atual: 2 prints genéricos reusados."

### Falha 4: Verificação só no final
**O que aconteceu:** O loop implementava tudo e depois verificava (ou não verificava).
**Por que falhou:** Erros se acumulavam. Quando Otavio revisava, encontrava 15 problemas de uma vez.
**O que resolveria:** Verificação a cada iteração do loop, CONTRA a tabela de gaps.

---

## 3. O Workflow que Deveria Existir

### Fase 0: Grande Plano (criação colaborativa)
```
Otavio descreve objetivo → Claude explora codebase → ambos escrevem plano
    ↓
plano_geral.md com seções: contexto, decisões, specs por módulo
    ↓
Cada spec tem: conteúdo esperado + assets esperados + citações das decisões
```

**Regra:** O grande plano é o documento de AUTORIDADE. Tudo que não está nele não existe.

### Fase 1: Documento de Decisões do Otavio (captura contínua)
```
Otavio diz algo no chat → Claude identifica: é decisão, correção, ou feedback?
    ↓
Se sim: salva IMEDIATAMENTE em decisoes_otavio.md
    - Citação exata
    - Data
    - Contexto (qual módulo/feature afeta)
    - Implicação para implementação
    ↓
Se a decisão contradiz o grande plano: ATUALIZAR o grande plano também
```

**Regra:** Decisões do Otavio têm prioridade sobre o grande plano. O plano deve ser atualizado para refletir.

### Fase 2: Plano de Curto Prazo (com citações)
```
Reler grande plano + decisões do Otavio
    ↓
Para cada tarefa do curto prazo:
    - CITAR a linha exata do grande plano que define o requisito
    - CITAR a decisão do Otavio que modifica/refina esse requisito
    - Descrever o estado atual do artefato
    - Definir critério de DONE (verificável, não subjetivo)
    ↓
plano_curto_prazo.md com: citação → estado atual → gap → critério de done
```

**Regra:** Nenhuma tarefa do curto prazo existe sem citação do grande plano.

### Fase 3: Loop de Implementação (com tabela de gaps)
```
Para cada gap no plano de curto prazo:
    1. RELER a citação exata (não confiar na memória)
    2. Implementar
    3. VERIFICAR contra a citação (o que implementei bate com o que o plano diz?)
    4. Se asset visual: ABRIR e verificar visualmente
    5. Marcar ✅ na tabela
    6. Commitar com referência ao gap
    7. Push + deploy (background, não bloquear)
    8. Próximo gap
```

**Regra:** Nunca pular a verificação. Nunca declarar "pronto" com ❌ na tabela.

### Fase 4: Review (humano)
```
Otavio revisa no site live
    ↓
Para cada feedback:
    - Claude salva como decisão em decisoes_otavio.md
    - Se contradiz plano: ATUALIZA o grande plano
    - Se é gap novo: ADICIONA na tabela
    ↓
Loop volta para Fase 3
```

---

## 4. Qual é a Hierarquia dos Documentos?

```
┌─────────────────────────────────┐
│  GRANDE PLANO (plano_geral.md)  │  ← Autoridade sobre O QUE construir
│  Atualizado por: decisões do    │
│  Otavio + achados técnicos      │
└─────────────┬───────────────────┘
              │ cita
              ▼
┌─────────────────────────────────┐
│  DECISÕES DO OTAVIO             │  ← Autoridade sobre COMO interpretar
│  (decisoes_otavio.md)           │     Prioridade sobre o grande plano
│  Atualizado: em tempo real      │     quando conflitar
└─────────────┬───────────────────┘
              │ cita ambos
              ▼
┌─────────────────────────────────┐
│  PLANO DE CURTO PRAZO           │  ← O QUE fazer AGORA
│  (plan file do Claude)          │     Cada task cita grande plano
│  Atualizado: início de cada     │     + decisões + estado atual
│  sessão ou rodada               │
└─────────────┬───────────────────┘
              │ referencia
              ▼
┌─────────────────────────────────┐
│  TABELA DE GAPS (audit.md)      │  ← VERIFICAÇÃO
│  Citação → Estado → Status      │     Atualizada durante o loop
│  ❌ → ✅ conforme implementa   │
└─────────────────────────────────┘
```

---

## 5. O que Automatizar vs O que é Manual

### Automatizar (skill/agente pode fazer):
- **Extração de citações do grande plano** — agente lê .md, extrai por seção, formata com line numbers
- **Extração de estado atual** — agente lê código, extrai conteúdo, compara com citações
- **Geração da tabela de gaps** — dado citações + estado, gerar ❌/⚠️/✅
- **Atualização da tabela** — após cada fix, marcar ✅ automaticamente
- **Deploy em background** — push + hook + poll sem bloquear

### Manual (precisa do humano):
- **Decisões de prioridade** — o que corrigir primeiro
- **Decisões de design** — quando o plano é ambíguo, perguntar ao Otavio
- **Verificação visual** — prints precisam ser avaliados qualitativamente
- **Reclassificação de gaps** — "isso é limitação da UI, não um bug" é julgamento humano

### Semi-automático (Claude propõe, Otavio confirma):
- **Captura de decisões** — Claude identifica "isso parece uma decisão" e propõe salvar
- **Atualização do grande plano** — Claude propõe edição, Otavio confirma
- **Critérios de done** — Claude propõe, Otavio ajusta

---

## 6. Skills que Emergem deste Workflow

### Skill 1: `/extract-quotes` (Extração de Citações)
- **Input:** arquivo .md + seções de interesse
- **Output:** citações formatadas com line numbers
- **Quando usar:** início de um loop, quando precisa construir a tabela de gaps

### Skill 2: `/capture-decision` (Captura de Decisão)
- **Trigger:** Otavio faz uma correção ou dá uma diretriz
- **Output:** entrada no `decisoes.md` com citação + contexto + implicação
- **Quando usar:** automaticamente quando o Claude detecta feedback do tipo decisão
- **Integração:** atualiza o grande plano se conflitar

### Skill 3: `/audit` (Comparação Plano vs Implementação)
- **Input:** plano .md + artefato (código/HTML)
- **Output:** tabela de gaps com ❌/⚠️/✅
- **Quando usar:** antes de cada loop de implementação

### Skill 4: `/plan-short` (Plano de Curto Prazo com Citações)
- **Input:** grande plano + decisões + tabela de gaps
- **Output:** lista de tarefas com citações do grande plano + critérios de done
- **Quando usar:** início de cada sessão de trabalho

### Relação entre as skills:
```
/extract-quotes → alimenta → /audit → alimenta → /plan-short → guia → /loop
                                ↑
/capture-decision → alimenta ───┘
```

---

## 7. Perguntas para o Otavio

1. **Decisões em tempo real:** Você quer que eu salve AUTOMATICAMENTE cada vez que detectar uma decisão, ou prefere que eu pergunte "isso é uma decisão, devo salvar?"

2. **Grande plano vs curto prazo:** Você quer manter a separação (grande plano nunca muda durante um loop, curto prazo é o "working doc")? Ou o grande plano pode ser atualizado durante o loop?

3. **Quantas skills:** Faz sentido ter 4 skills separadas, ou uma skill única (`/audit-loop`) que faz os 4 passos em sequência?

4. **Escopo:** Isso é só para o NOVO CR ou você quer usar em outros projetos também?
