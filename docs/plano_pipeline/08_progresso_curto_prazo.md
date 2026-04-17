# Progresso de Curto Prazo — Sessao 2026-04-17

## Sucessos

### 1. Auditoria completa dos 402 documentos da atividade Lista0
- Classificamos todos os documentos: 216 bons, 183 fantasmas, 3 incompletos
- Identificamos os 10 alunos sem correcao (nao 7 como estimado inicialmente)
- Identificamos os 3 alunos fantasma e a causa raiz

### 2. Causa raiz dos alunos fantasma encontrada
**Arquivo:** [investigacao_fantasmas_templates.md](investigacao_fantasmas_templates.md)

O pipeline nao valida se o aluno tem prova antes de rodar EXTRAIR_RESPOSTAS. A IA recebe um prompt pedindo para extrair respostas de... nada. Ela obedientemente retorna todas as questoes como `em_branco: true`. O pipeline segue em cascata: CORRIGIR da nota 0/10, ANALISAR e GERAR_RELATORIO rodam normalmente sobre a nota zero.

**Fix necessario:** Adicionar checagem pre-voo em `processar_aluno_completo` verificando se existe pelo menos um documento PROVA_RESPONDIDA para o aluno antes de rodar EXTRAIR_RESPOSTAS.

### 3. Causa raiz dos templates {{nota_final}} encontrada
**Arquivo:** [investigacao_fantasmas_templates.md](investigacao_fantasmas_templates.md)

Dois problemas interagem:
- `_preparar_variaveis_texto()` (executor.py:1538) so calcula `nota_final` se `correcoes` esta no dicionario. Se a correcao nao foi carregada, a variavel nao existe.
- O prompt em `prompts.py:515` tem `"nota_final": "{{nota_final}}"` como exemplo. Quando a variavel nao e substituida, a IA copia o literal `{{nota_final}}` para o output.
- `gerar_relatorio()` (executor.py:1343) silenciosamente descarta a lista de documentos faltantes com `contexto_json.pop("_documentos_faltantes", [])`.

### 4. Entendemos que prova_respondida null NAO e bug
**Arquivo:** [investigacao_prova_respondida.md](investigacao_prova_respondida.md)

O endpoint `/api/documentos/{id}/conteudo` nao sabe ler PDFs — so le .json, .txt e .md. Os PDFs das provas estao intactos e acessiveis via `/download` e `/view`. O campo `conteudo=null` e uma limitacao do endpoint, nao um documento vazio.

### 5. Dois bugs reais corrigidos e deployados
- **commit 1eb37cb:** URL do Anthropic multimodal estava sem `/messages` quando `base_url` era fornecida pelo `ai_registry`. Fix em `anexos.py`.
- **commit 152daf9:** Mensagem de erro 400 do Anthropic era generica ("modelo pode estar indisponivel") mesmo quando o problema era falta de creditos. Agora mostra o erro real da API. Fix em `chat_service.py`.

### 6. Pipeline testada com 3 providers

**Arquivo:** [teste_haiku_eric.md](teste_haiku_eric.md)

| Provider | Modelo | Endpoint | Resultado |
|----------|--------|----------|-----------|
| Anthropic | Haiku 4.5 | pipeline-completo | FALHA — creditos insuficientes |
| OpenAI | GPT-4o (fallback) | pipeline-completo | SUCESSO — 3 etapas completaram |
| Google | Gemini 3 Flash | executar/etapa | SUCESSO (apos retry 503) — mas retornou schema vazio |
| OpenAI | GPT-5 Nano | executar/etapa | SUCESSO — mas retornou schema vazio |

**Achado critico:** O endpoint `/executar/etapa` (etapa individual) NAO substitui as variaveis de template (`{{questao}}`, `{{resposta_aluno}}`, etc.). Os modelos recebem um prompt com placeholders e respondem "nao tenho dados". O endpoint `pipeline-completo` funciona porque carrega o contexto dos documentos anteriores.

Isso explica por que os 7-10 alunos nao foram corrigidos — se alguem tentou rodar etapas individuais pela GUI, os templates nao foram preenchidos.

---

## Fracassos / Problemas Encontrados

### 1. Creditos Anthropic insuficientes
Nao conseguimos testar com Haiku 4.5 (o modelo default) porque a conta Anthropic esta sem creditos. **Acao necessaria:** recarregar creditos ou usar outro provider.

### 2. Documentos gerados SEM campos de aviso
Os 3 documentos gerados para Eric (correcao, analise, relatorio) **nao contem** `_avisos_documento`, `_avisos_questao`, nem `_avisos_stage`. O sistema de avisos nao esta funcionando na pratica — confirma a hipotese do Doc 02.

### 3. Schema da correcao usa formato antigo
A correcao gerada usa o formato flat (`nota`, `feedback`) em vez do formato STAGE_TOOL_INSTRUCTIONS (`nota_final`, `questoes[]`). O modelo seguiu o PROMPTS_PADRAO, nao o STAGE_TOOL_INSTRUCTIONS — exatamente o drift que o Doc 02 identificou.

### 4. Redundancia massiva de documentos base
Cada execucao do pipeline recria extracao_questoes e extracao_gabarito. Resultado: 29+27=56 copias identicas. Desperdiça tokens e espaco.

### 5. Testes async falham por falta de API key local
Os 3 testes F3-T1 que usam `executor._executar_multimodal()` precisam de API key do Anthropic mesmo localmente. Nao sao testes unitarios isolados.

### 6. Endpoint /executar/etapa nao substitui variaveis de template
Quando se roda uma etapa individual (ex: so "corrigir"), o endpoint nao carrega questoes, gabarito e respostas do aluno no prompt. O modelo recebe `{{questao}}`, `{{resposta_aluno}}` literais. O `pipeline-completo` funciona porque faz o carregamento completo. Isso e provavelmente a causa dos 10 alunos nao corrigidos.

---

## Proximos Passos Imediatos

1. Rodar pipeline para Eric com Gemini 3 Flash e GPT-5 Nano
2. Verificar se esses modelos geram campos `_avisos_*`
3. Apresentar lista de 183 fantasmas para aprovacao de delecao
4. Aplicar fixes para os problemas encontrados (fantasmas, templates)

---

## Atualizacao 2026-04-17 (final da sessao): Fixes aplicados + teste empirico

### Fixes commitados (commits a632883, 5737611)

- `/executar/etapa` agora carrega contexto dos documentos anteriores (template vars substituidas corretamente)
- `/executar/etapa` retorna HTTP 400 explicito se documentos pre-requisito estao faltando
- `corrigir()`, `analisar_habilidades()`, `gerar_relatorio()` nao descartam silenciosamente `_documentos_faltantes`
- Pre-flight check para `PROVA_RESPONDIDA` antes de `EXTRAIR_RESPOSTAS` (previne alunos fantasma)
- Fallback `nota_final = "N/A"` quando correcoes ausente (previne `{{nota_final}}` literal)
- `create_document` injeta defaults `_avisos_documento`, `_avisos_questao`, `_avisos_stage` com atomic write
- `models.json` flags corrigidos: Sonnet 4.5 agora tem function_calling=true, Gemini 2.5 Flash Lite=false

### Teste empirico de `/executar/etapa` apos fix

Ver [teste_executar_etapa_corrigido.md](teste_executar_etapa_corrigido.md)

**Resultado: SUCESSO**

- **Cenario 1 (Henrique, docs OK):** HTTP 200, sucesso=true, JSON com nota 5.72/10, feedback especifico a Algebra Linear. **Zero templates `{{...}}` literais** na saida. Fix confirmado.
- **Cenario 2 (Luisa, sem prova):** HTTP 400 com mensagem clara: "Documentos necessarios nao encontrados: respostas_aluno (execute 'extrair_respostas' primeiro)". Fast-fail correto.

### Ressalvas identificadas (follow-up necessario)

1. **Gemini 3 Flash em 503 overload** no momento do teste — path Google nao foi validado empiricamente. Teste via GPT-5 Nano valida a mudanca no server-side.
2. **`_avisos_*` nao apareceram no JSON do GPT-5 Nano** — o modelo nao incluiu esses campos mesmo com a injecao do handler. Investigar: a injecao funciona para tool-use path, mas `/executar/etapa` pode nao passar pelo handler.
3. **`arquivos_gerados: []`** — endpoint nao persiste documento de correcao. Precisa confirmar se e by-design (preview) ou gap.

### Rodada de agentes bem-sucedida

- Rodada 1 (paralelo): 3 agentes Impl-Endpoint + Impl-Seguranca + Impl-Avisos aplicaram fixes
- Rodada 2 (paralelo): 3 agentes Rev revisaram e encontraram 5 issues de qualidade
- Rodada 2.5 (paralelo): 3 agentes Patch aplicaram correcoes dos revisores
- Rodada 3: Agente Testes identificou 17 regressoes intencionais (novo comportamento loud)
- Rodada 3.5 (paralelo): Classificador (58 pre-existentes, 0 criticos), Atualizador (17 testes voltaram a passar), Historiador (leu prompt log)
- Rodada 4 (paralelo): Test-Etapa SUCESSO, Test-Pipeline rodando

**Total: 12 agentes em 5 rodadas, com ciclo completo Impl → Rev → Patch → Test → Triage → Verify**
