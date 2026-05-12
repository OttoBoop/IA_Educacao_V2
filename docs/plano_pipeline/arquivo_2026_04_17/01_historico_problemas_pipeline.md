# Historico de Problemas da Pipeline

**Data:** 2026-04-17
**Autor:** Agente Historiador (Claude Code)
**Objetivo:** Documentar o estado atual da pipeline de correcao do NOVO CR, seus padroes de erro, problemas conhecidos e inconsistencias encontradas durante auditoria do codigo-fonte e da API em producao.

---

## 1. Estado atual da pipeline

### 1.1 As 6 etapas

A pipeline de correcao do NOVO CR processa provas/atividades em 6 etapas sequenciais:

| # | Etapa | Tipo | Entrada principal | Saida (TipoDocumento) |
|---|-------|------|-------------------|----------------------|
| 1 | EXTRAIR_QUESTOES | Atividade (sem aluno) | enunciado (PDF/imagem) | EXTRACAO_QUESTOES (.json) |
| 2 | EXTRAIR_GABARITO | Atividade (sem aluno) | gabarito (PDF/imagem) | EXTRACAO_GABARITO (.json) |
| 3 | EXTRAIR_RESPOSTAS | Por aluno | prova_respondida (PDF/imagem) | EXTRACAO_RESPOSTAS (.json) |
| 4 | CORRIGIR | Por aluno | questoes + gabarito + respostas | CORRECAO (.json + .pdf) |
| 5 | ANALISAR_HABILIDADES | Por aluno | correcao | ANALISE_HABILIDADES (.json + .pdf) |
| 6 | GERAR_RELATORIO | Por aluno | correcao + analise | RELATORIO_FINAL (.json + .pdf) |

As etapas 1-2 sao executadas uma unica vez por atividade (nivel atividade). As etapas 3-6 sao executadas uma vez por aluno (nivel aluno).

Alem destas, existem 3 etapas agregadas de relatorio de desempenho (RELATORIO_DESEMPENHO_TAREFA, _TURMA, _MATERIA) que operam sobre os relatorios finais de multiplos alunos.

### 1.2 Dois caminhos de execucao

O executor (`executor.py`) suporta dois modos de execucao:

1. **Modo texto (legado):** `_executar_texto()` — Extrai texto dos documentos e envia como string para a IA. Usa o sistema `ai_registry` antigo.

2. **Modo multimodal (padrao):** `_executar_multimodal()` — Envia PDFs e imagens nativamente como anexos para a API da IA. Usa o `chat_service.provider_manager` (sistema novo). Este e o caminho padrao quando `HAS_MULTIMODAL = True`.

Para as etapas 4-6 (CORRIGIR, ANALISAR_HABILIDADES, GERAR_RELATORIO), o executor usa `executar_com_tools()` que habilita tool-use: a IA chama `create_document` (JSON) e `execute_python_code` (PDF via reportlab).

### 1.3 Endpoints duplicados

Existem **multiplos endpoints** para executar a pipeline, documentados como "UNIFICATION CANDIDATE" no proprio codigo:

| Endpoint | Arquivo | Funcao |
|----------|---------|--------|
| `POST /api/pipeline/executar` | routes_pipeline.py | Executa etapa individual |
| `POST /api/executar/etapa` | routes_prompts.py | Executa etapa com chat service |
| `POST /api/executar/pipeline-completo` | routes_prompts.py | Pipeline completo para 1 aluno |
| `POST /api/executar/pipeline-todos-os-alunos` | routes_prompts.py | Pipeline completo para todos os alunos |

A existencia de multiplos endpoints com formatos de request/response diferentes, tratamento de erro inconsistente e potenciais race conditions e um risco documentado mas nao resolvido.

### 1.4 Dependencias entre documentos

O sistema de dependencias esta definido em `models.py` no dict `DEPENDENCIAS_DOCUMENTOS`. Cada tipo de documento gerado lista seus documentos obrigatorios e opcionais:

- CORRECAO requer: EXTRACAO_RESPOSTAS + GABARITO (obrigatorios), CRITERIOS_CORRECAO + EXTRACAO_GABARITO (opcionais)
- ANALISE_HABILIDADES requer: CORRECAO (obrigatorio), CRITERIOS_CORRECAO (opcional)
- RELATORIO_FINAL requer: CORRECAO (obrigatorio), ANALISE_HABILIDADES + CRITERIOS_CORRECAO (opcionais)

**Inconsistencia encontrada:** A funcao `_preparar_contexto_json()` no executor.py implementa suas proprias verificacoes de dependencia que **nao correspondem exatamente** ao `DEPENDENCIAS_DOCUMENTOS`:
- `_preparar_contexto_json` exige `questoes_extraidas` para CORRIGIR e ANALISAR_HABILIDADES, mas `DEPENDENCIAS_DOCUMENTOS[CORRECAO]` nao lista EXTRACAO_QUESTOES como obrigatorio.
- `_preparar_contexto_json` exige `analise_habilidades` para GERAR_RELATORIO como se fosse obrigatorio (coloca em `documentos_faltantes`), mas `DEPENDENCIAS_DOCUMENTOS[RELATORIO_FINAL]` lista ANALISE_HABILIDADES como **opcional**.

Isso significa que a logica real de cascade e mais restritiva que a formal.

---

## 2. Framework de erros

### 2.1 Estrutura de erro

O framework de erros esta definido em `models.py` (linhas 118-153):

```python
# Constantes de tipo de erro
ERRO_DOCUMENTO_FALTANTE = "DOCUMENTO_FALTANTE"
ERRO_QUESTOES_FALTANTES = "QUESTOES_FALTANTES"

class SeveridadeErro(Enum):
    CRITICO = "critico"
    ALTO = "alto"
    MEDIO = "medio"

def criar_erro_pipeline(tipo, mensagem, severidade, etapa) -> dict:
    # Retorna: {tipo, mensagem, severidade, etapa, timestamp}
```

### 2.2 Tipos de erro observados

| Tipo | Constante | Quando ocorre |
|------|-----------|---------------|
| Documento faltante | `ERRO_DOCUMENTO_FALTANTE` | Etapa anterior nao gerou JSON necessario |
| Questoes faltantes | `ERRO_QUESTOES_FALTANTES` | Definido mas **nao encontrado em uso no executor** |
| Erro de parsing JSON | `_error` no dict | IA retornou resposta que nao pode ser parseada como JSON |
| Resposta vazia | `empty_response` | IA retornou string vazia |
| JSON vazio | `empty_json` | IA retornou `{}` ou `[]` |
| Erro de validacao | `_validation_warning` | JSON parseado mas nao passa na validacao Pydantic |
| Tool nao suportada | Mensagem direta | Modelo nao suporta function calling |
| Max iterations | `max_iterations_exceeded` | Loop de tools atingiu limite de iteracoes |

### 2.3 Propagacao de erros (cascade)

Quando a etapa X falha, as etapas subsequentes que dependem dela tambem falham com `ERRO_DOCUMENTO_FALTANTE`. O mecanismo funciona assim:

1. `_preparar_contexto_json()` tenta carregar cada JSON de etapa anterior
2. Se o JSON contem `_error` (parsing falhou), conta como faltante
3. Se o arquivo nao existe, conta como faltante
4. Se `docs_faltantes` nao esta vazio, a etapa cria um `_erro_pipeline` com severidade CRITICO e salva um JSON contendo apenas o erro
5. Esse JSON com erro sera detectado como invalido pelas etapas seguintes

**Resultado pratico:** Se EXTRAIR_RESPOSTAS falha para um aluno, todas as 3 etapas seguintes (CORRIGIR, ANALISAR, RELATORIO) falham em cascata. Cada uma salva um JSON de erro, gerando documentos "fantasma" no banco.

### 2.4 Sistema de avisos (_avisos)

As etapas 4-6 (tool-use) incluem dois arrays de avisos no JSON de saida:

| Campo | Escopo | Codigos |
|-------|--------|---------|
| `_avisos_documento` | Documento inteiro | ILLEGIBLE_DOCUMENT, MISSING_CONTENT, LOW_CONFIDENCE |
| `_avisos_questao` | Questao especifica | ILLEGIBLE_QUESTION, MISSING_CONTENT, LOW_CONFIDENCE |

As etapas 1-3 (prompt direto, via `prompts.py`) tambem definem esses mesmos campos nos schemas dos prompts.

---

## 3. Problemas observados

### 3.1 Falhas na atividade "Algebra Linear Avancada" (Lista0)

**Dados coletados da API em producao (2026-04-17):**

- Materia: "Algebra Linear Avancada" (id: `57861d16958965d2`)
- Turma: "2026-1" (id: `3f3ab03dfe783f30`), 63 alunos
- Atividade: "Lista0" (id: `126e8b5ad7dd6d59`), 402 documentos
- Status: 38 alunos com prova enviada, 31 corrigidos

**Anomalias detectadas:**
- 3 alunos aparecem como "corrigidos" mas **sem prova enviada** (ALICE BARROS LOURENCINI PALAORO, FABRICIO DALVI VENTURIM, RAPHAEL FELBERG LEVY). Isso sugere que o pipeline rodou mesmo sem `prova_respondida`, o que nao deveria ser possivel dada a dependencia `EXTRACAO_RESPOSTAS → PROVA_RESPONDIDA`.
- 25 alunos (40%) sem nenhuma submissao — pode ser normal (alunos que nao entregaram) mas o volume e alto.
- 7 alunos com prova enviada mas **nao corrigidos** — indica falha no pipeline em alguma etapa.

**Hipoteses sobre os 3 alunos "corrigidos sem prova":**
1. A verificacao de status usa presenca de documento CORRECAO, mas o JSON pode conter apenas `_erro_pipeline` (conta como "tem correcao" mesmo sendo erro)
2. Houve upload e posterior delecao da prova respondida
3. Bug na logica de `listar_documentos` com filtro de aluno_id

### 3.2 Avisos de documentos incompletos (_avisos nao populados)

O CLAUDE.md documenta que `_avisos_documento` e `_avisos_questao` substituiram os antigos campos `_documento_ilegivel` e `_campos_faltantes` (2026-03-15). Existem dois problemas potenciais:

1. **Schemas definidos em dois lugares:** As etapas 1-3 tem seus schemas em `PROMPTS_PADRAO` (prompts.py). As etapas 4-6 tem seus schemas em `STAGE_TOOL_INSTRUCTIONS` (executor.py). Se um schema muda, o outro pode ficar desatualizado.

2. **A IA pode ignorar os avisos:** O sistema de avisos depende da IA preencher corretamente os arrays `_avisos_documento` e `_avisos_questao`. Se a IA retorna listas vazias `[]` mesmo quando ha problemas reais (documento ilegivel, questao borrada), o frontend nao mostra nenhum alerta. Nao ha validacao automatica do conteudo desses campos — a unica verificacao e estrutural (Pydantic valida o schema, nao a semantica).

3. **Documentos antigos nao tem o campo:** Documentos gerados antes de 2026-03-15 usam os campos antigos (`_documento_ilegivel`, `_campos_faltantes`). O frontend/visualizador precisa lidar com ambos os formatos.

### 3.3 Cascade de erros e documentos fantasma

Quando o pipeline roda para todos os alunos de uma turma (`/api/executar/pipeline-todos-os-alunos`), cada aluno passa por todas as 6 etapas. Se a etapa 3 (EXTRAIR_RESPOSTAS) falha:

- Etapa 4 (CORRIGIR) salva JSON com `_erro_pipeline` → cria documento CORRECAO no banco
- Etapa 5 (ANALISAR) salva JSON com `_erro_pipeline` → cria documento ANALISE_HABILIDADES
- Etapa 6 (RELATORIO) salva JSON com `_erro_pipeline` → cria documento RELATORIO_FINAL

Resultado: o aluno aparece no sistema com 3 documentos "gerados" que na verdade sao registros de erro. O status pode mostrar "corrigido" mesmo sem correcao real. Isso explica parte da anomalia do item 3.1.

### 3.4 Parsing de JSON com fallbacks frageis

A funcao `_parsear_resposta()` (executor.py, linhas 1609-1808+) tenta 4 estrategias para extrair JSON:

1. `json.loads(resposta)` direto
2. Extrair de bloco ````json ... ````
3. Regex para encontrar `{...}` ou `[...]` no texto
4. Para `gerar_relatorio`: aceitar Markdown como valido (!)

O fallback #3 (regex greedy) pode capturar JSONs aninhados incorretamente ou misturar conteudo. O fallback #4 aceita Markdown como resposta valida para relatorios, o que pode mascarar falhas de geracao.

### 3.5 PDF fallback automatico (F7-T1)

Quando a IA chama `create_document` mas **nao** chama `execute_python_code` (nao gera PDF), o sistema automaticamente gera um PDF a partir do conteudo JSON. Isso e um workaround robusto mas:

- O PDF gerado automaticamente tem formatacao generica ("Relatorio PDF gerado automaticamente")
- O tipo do documento e hardcoded como `RELATORIO_FINAL` — se acontecer em CORRECAO ou ANALISE, o tipo estara errado
- O alerta `pdf_fallback` e registrado mas nao e facilmente visivel no frontend

### 3.6 Endpoints duplicados e inconsistencia de tratamento de erro

Os 4 endpoints de execucao de pipeline listados na secao 1.3 tem tratamentos de erro diferentes:

- `routes_pipeline.py` retorna `HTTPException(500, str(e))` generico
- `routes_prompts.py` tem tratamento mais detalhado com codigos de erro especificos

Isso significa que o mesmo tipo de falha pode retornar respostas diferentes dependendo de qual endpoint foi usado.

---

## 4. Verificacoes por arquivo

### 4.1 executor.py (149KB)

**O que faz sentido:**
- A separacao entre modo texto e multimodal e clara
- O sistema de tool-use com `create_document` + `execute_python_code` e bem estruturado
- O retry automatico para dual-output parcial (E-T2) e uma boa pratica
- O PDF fallback (F7-T1) e uma boa rede de seguranca

**Inconsistencias:**
- `_preparar_contexto_json()` implementa dependencias mais restritivas que `DEPENDENCIAS_DOCUMENTOS` em models.py (duplicacao de logica)
- A constante `ERRO_QUESTOES_FALTANTES` e importada mas nunca usada no executor
- O arquivo tem 149KB — e extremamente grande para um unico modulo Python, o que dificulta manutencao

**Ausencias:**
- Nao ha mecanismo para detectar se um JSON salvo e "real" ou e um `_erro_pipeline` sem precisar abrir e ler o arquivo
- Nao ha timeout por etapa — se a IA demora indefinidamente, o request do FastAPI e que vai dar timeout

### 4.2 routes_pipeline.py

**O que faz sentido:**
- Endpoints de download/visualizacao bem separados por funcao
- Sistema de MIME types abrangente
- Endpoint de alertas que agrega avisos de todos os documentos

**Inconsistencias:**
- 3 endpoints para acessar o mesmo documento: `/download`, `/view`, `/visualizar` — marcados como UNIFICATION CANDIDATE
- O endpoint `/api/providers/disponiveis` duplica funcionalidade de routes_prompts.py
- O endpoint de alertas (`/api/atividades/{id}/alertas`) le JSONs do disco a cada request — sem cache

**Ausencias:**
- Nenhum endpoint retorna status detalhado dos erros do pipeline (quais alunos falharam e por que)

### 4.3 models.py

**O que faz sentido:**
- Hierarquia clara: Materia → Turma → Atividade → Aluno/Documentos
- Enum TipoDocumento bem organizado por categorias (BASE, ALUNO, GERADO)
- Framework de erros simples e extensivel
- Sistema de dependencias declarativo

**Inconsistencias:**
- `verificar_dependencias()` e definida mas **nao e usada pelo executor** — o executor implementa sua propria logica em `_preparar_contexto_json()`
- Tipos DEPRECATED (CORRECAO_NARRATIVA, ANALISE_HABILIDADES_NARRATIVA, RELATORIO_NARRATIVO) ainda listados em `documentos_gerados()` — podem causar confusao em queries

**Ausencias:**
- Nao ha campo no modelo Documento para distinguir "resultado real" de "registro de erro" sem abrir o arquivo
- SeveridadeErro tem 3 niveis (CRITICO, ALTO, MEDIO) mas nao ha nivel BAIXO ou INFO — apenas 2 tipos de erro definidos

### 4.4 storage.py

**O que faz sentido:**
- Dual-backend robusto (PostgreSQL Supabase + SQLite local)
- Sistema de resolucao de caminho com fallback Supabase → local
- Funcoes `_fast` otimizadas com leituras em lote (evitam N+1)
- Build de display_name e filename sanitization

**Inconsistencias:**
- `renomear_documento()` so funciona com SQLite (nao usa `supabase_db.update`) — bug em producao
- `resolver_caminho_documento()` loga excessivamente em nivel INFO para cada resolucao — pode gerar muito ruido em logs
- `listar_documentos()` com `aluno_id` faz **duas queries** no PostgreSQL (uma com aluno_id, outra com aluno_id=None) e merge no Python — poderia ser uma unica query com OR

**Ausencias:**
- Nao ha mecanismo de limpeza para documentos fantasma (JSONs de erro)
- Nao ha indice no banco para query por tipo de documento (a query mais frequente)

---

## 5. Perguntas em aberto

1. **Os 3 alunos "corrigidos sem prova" em Algebra Linear:** E um bug no pipeline ou houve upload seguido de delecao? Precisa verificar os documentos JSON individuais desses alunos para confirmar se sao registros de erro ou correcoes reais.

2. **Os 7 alunos com prova mas nao corrigidos:** A pipeline foi executada para todos? Alguma etapa intermediaria falhou? Verificar logs do Render para esses alunos especificos.

3. **Avisos (_avisos) estao sendo populados na pratica?** Seria necessario amostrar JSONs de correcao recentes para verificar se a IA esta de fato preenchendo os campos de aviso ou retornando listas vazias.

4. **Qual endpoint o frontend realmente usa?** Com 4 endpoints de execucao, qual e o caminho critico? Isso define onde priorizar melhorias.

5. **O `ERRO_QUESTOES_FALTANTES` e dead code?** Importado no executor mas aparentemente nunca usado. Confirmar se algum outro modulo usa.

6. **`renomear_documento()` funciona em producao?** A implementacao so cobre SQLite. Como producao usa PostgreSQL (Supabase), esse metodo provavelmente nao funciona. Verificar se e usado em algum lugar.

7. **O tamanho do executor.py (149KB) e sustentavel?** Um unico arquivo com ~2500 linhas cobrindo parsing, execucao, tool-use, fallbacks e salvamento e um risco de manutencao. Deve ser fatorado?

---

## Apendice: Dados da API em producao

**Consultado em:** 2026-04-17
**Base URL:** https://ia-educacao-v2.onrender.com/api/

- Total de materias: 28
- Materia relevante: "Algebra Linear Avancada" (id: `57861d16958965d2`)
- Turma: "2026-1" (id: `3f3ab03dfe783f30`), 63 alunos, 1 atividade
- Atividade: "Lista0" (id: `126e8b5ad7dd6d59`), 402 documentos
- Documentos base: enunciado + gabarito presentes
- Alunos com prova: 38/63 (60%)
- Alunos corrigidos: 31/63 (49%)
- Alunos com prova mas sem correcao: 7
- Alunos corrigidos sem prova aparente: 3 (anomalia)
