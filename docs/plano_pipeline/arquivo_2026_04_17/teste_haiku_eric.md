# Teste Pipeline - Eric Manoel Ribeiro de Sousa (Haiku 4.5)

**Data:** 2026-04-17
**Atividade:** 126e8b5ad7dd6d59 (Lista0 - Álgebra Linear Avançada - 2026-1)
**Aluno:** 660e9421b246ad3f (Eric Manoel Ribeiro de Sousa)
**Model ID solicitado:** 588f3efe7975 (Claude Haiku 4.5)

---

## Status Inicial

| Etapa | Status |
|-------|--------|
| extrair_questoes | OK |
| extrair_gabarito | OK |
| extrair_respostas | OK |
| corrigir | pendente |
| analisar_habilidades | pendente |
| gerar_relatorio | pendente (tinha versão anterior sem dependências) |

**Observação:** Muitos documentos duplicados de extracao_questoes e extracao_gabarito (~20 cópias de cada).

---

## Tentativa 1: Pipeline Completo com model_id=588f3efe7975

**Resultado:** FALHOU
**Erro:** `Erro API Anthropic: 400 - Modelo 'claude-haiku-4-5-20251001' pode estar indisponível ou com ID incorreto.`

**Análise:** O model_id `588f3efe7975` resolve para o modelo `claude-haiku-4-5-20251001` na Anthropic API, mas esse identificador foi rejeitado com HTTP 400. Pode estar depreciado ou incorreto.

## Tentativa 2: Pipeline Completo sem model_id (default provider)

**Resultado:** FALHOU
**Erro:** HTTP 404 na API Anthropic
**Causa raiz:** Bug em `backend/anexos.py` linha 734 — `_enviar_anthropic` usava `self.base_url` diretamente como URL de POST, sem concatenar `/messages`. O `ai_registry` popula `base_url = "https://api.anthropic.com/v1"`, que NÃO inclui `/messages`.

**Fix aplicado:** Commit `1eb37cb` — agora `_enviar_anthropic` sempre garante que a URL termina em `/messages`.

## Tentativa 3: Etapas individuais com provider=claude-sonnet

**Resultado:** FALHOU (mesmo bug de URL, HTTP 404)

## Tentativa 4: Etapas individuais com provider=openai-gpt4o (fallback)

**Resultado:** SUCESSO (3/3 etapas)

| Etapa | Sucesso | Provider | Modelo | Tokens In | Tokens Out | Tempo (ms) | Doc ID |
|-------|---------|----------|--------|-----------|------------|------------|--------|
| corrigir | OK | openai | gpt-4o | 92,639 | 291 | 15,729 | 53642cb495a0be3b |
| analisar_habilidades | OK | openai | gpt-4o | 66,068 | 412 | 14,786 | 38998862379fd325 |
| gerar_relatorio | OK | openai | gpt-4o | 60,634 | 492 | 11,450 | 186a822b5ce1db5c |

---

## Verificação dos Documentos Gerados

### Correção (53642cb495a0be3b)

- **JSON válido:** Sim
- **Campos:** nota, nota_maxima, percentual, status, feedback, pontos_positivos, pontos_melhorar, erros_conceituais, habilidades_demonstradas, habilidades_faltantes
- **nota_final:** N/A (campo é `nota: 1.43`)
- **questoes[]:** AUSENTE (formato não-padrão)
- **_avisos_documento:** AUSENTE
- **_avisos_questao:** AUSENTE
- **_avisos_stage:** AUSENTE
- **Modelo usado:** gpt-4o (metadata não incluída no JSON do documento)

**Problema:** O formato do JSON não segue o schema esperado (STAGE_TOOL_INSTRUCTIONS). Falta o array `questoes[]` com nota/feedback por questão e os campos de avisos `_avisos_*`.

### Análise de Habilidades (38998862379fd325)

- **JSON válido:** Sim
- **Campos:** aluno, resumo_desempenho, nota_final, nota_maxima, percentual_acerto, habilidades (dominadas/em_desenvolvimento/nao_demonstradas), recomendacoes, pontos_fortes, areas_atencao
- **habilidades:** Sim, em 3 categorias com evidência
- **_avisos_documento:** AUSENTE
- **_avisos_questao:** AUSENTE
- **_avisos_stage:** AUSENTE

### Relatório Final (186a822b5ce1db5c)

- **JSON válido:** Sim
- **Campos:** conteudo (markdown), resumo_executivo, nota_final, aluno, materia, atividade
- **Conteúdo:** Relatório markdown completo com seções de desempenho, habilidades e recomendações
- **_avisos_documento:** AUSENTE
- **_avisos_questao:** AUSENTE
- **_avisos_stage:** AUSENTE

---

## Bugs Encontrados

### BUG 1: URL Anthropic Multimodal (CORRIGIDO)
- **Arquivo:** `backend/anexos.py`, `_enviar_anthropic()`
- **Problema:** `url = self.base_url or "https://api.anthropic.com/v1/messages"` — quando `base_url` é `https://api.anthropic.com/v1` (truthy), usava essa URL SEM `/messages`
- **Fix:** Commit `1eb37cb` — detecta se URL já termina em `/messages`, senão concatena

### BUG 2: Créditos Anthropic insuficientes (NÃO é modelo inválido)
- **Problema:** A conta Anthropic no Render não tem créditos suficientes
- **Erro real:** "Your credit balance is too low to access the Anthropic API"
- **Impacto:** Nenhum modelo Anthropic (Haiku, Sonnet, Opus) funciona no Render
- **Status:** Requer recarga de créditos na conta Anthropic

### BUG 2b: Mensagem de erro wrapper é enganosa (CORRIGIDO)
- **Arquivo:** `backend/chat_service.py`, linha 984
- **Problema:** O erro "Modelo 'X' pode estar indisponível ou com ID incorreto" ocultava a causa real (créditos insuficientes)
- **Fix:** Commit `152daf9` — agora mostra o corpo real da resposta da API para erros 400

### BUG 3: Documentos duplicados
- **Problema:** Eric tem ~20 cópias de extracao_questoes e extracao_gabarito
- **Impacto:** Todos os duplicados são enviados como anexos na chamada multimodal (~50 arquivos!), desperdiçando tokens e potencialmente causando erros de tamanho
- **Status:** Não corrigido — necessita investigação

### BUG 4: Campos _avisos_* ausentes
- **Problema:** Nenhum dos 3 documentos gerados contém `_avisos_documento`, `_avisos_questao` ou `_avisos_stage`
- **Causa provável:** O STAGE_TOOL_INSTRUCTIONS pode não estar sendo injetado corretamente no prompt, ou o modelo está ignorando esses campos opcionais
- **Status:** Não investigado

---

## Tentativa 5: Haiku pós-deploy do fix de URL

**Resultado:** FALHOU
**Erro real:** `"Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."`
**HTTP:** 400 (invalid_request_error)

**Diagnóstico final:** O modelo `claude-haiku-4-5-20251001` é VÁLIDO — o erro 400 original era por saldo insuficiente de créditos na Anthropic API, NÃO por modelo inválido. A mensagem wrapper do sistema ("Modelo pode estar indisponível ou com ID incorreto") ocultou o erro real.

---

## Resumo

| Item | Status |
|------|--------|
| Pipeline com Haiku | FALHOU (créditos Anthropic insuficientes + bug de URL corrigido) |
| Pipeline com GPT-4o (fallback) | OK (3/3 etapas) |
| Fix URL Anthropic | Commitado e deployando |
| Documentos gerados | JSON válido, mas sem campos _avisos_* |
| Formato correcao | Não segue schema esperado (falta questoes[]) |
