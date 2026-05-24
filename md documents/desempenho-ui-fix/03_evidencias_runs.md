# 03 — Evidências dos runs por provider

> **Status:** ⏸️ AGUARDANDO fix UI deployar
> **Política:** cada run é gravado AQUI antes de iniciar o próximo. Custo é capturado via `/api/cost-samples/<task_id>` e anotado.

---

## Setup comum

- **Matéria/turma/atividade:** Álgebra Linear Avançada → 2026-1 → Lista0 (38 alunos, ids preservados via `_recover_supabase.py`)
- **Nível:** "Desempenho da turma" (cascade: 38 alunos × 6 etapas + 1 desempenho-tarefa = 229 calls)
- **force_reexec:** false (default — skip alunos com RELATORIO_FINAL existente)
- **Captura de custo:** `curl -s https://ia-educacao-v2.onrender.com/api/cost-samples/<task_id> | jq`

---

## Run 1: Anthropic — claude-haiku-4-5-20251001

- **Iniciado em:** _pendente_
- **task_id:** _pendente_
- **Status:** ⏸️
- **Duração:** _pendente_
- **Calls bem-sucedidas / total:** _pendente_
- **Custo total $:** _pendente_
- **Custo por etapa:**
  - EXTRAIR_QUESTOES: $_
  - EXTRAIR_GABARITO: $_
  - EXTRAIR_RESPOSTAS: $_
  - CORRIGIR: $_
  - ANALISAR_HABILIDADES: $_
  - GERAR_RELATORIO: $_
  - desempenho-tarefa: $_
- **Erros observados:** _pendente_
- **Notas:** _pendente_

---

## Run 2: OpenAI — gpt-5-nano

- **Iniciado em:** _pendente_
- **task_id:** _pendente_
- **Status:** ⏸️
- **Duração:** _pendente_
- **Calls bem-sucedidas / total:** _pendente_
- **Custo total $:** _pendente_
- **Custo por etapa:** _pendente_
- **Erros observados:** _pendente_
- **Notas:** _pendente_

---

## Run 3: Google — gemini-3-flash-preview

- **Iniciado em:** _pendente_
- **task_id:** _pendente_
- **Status:** ⏸️
- **Duração:** _pendente_
- **Calls bem-sucedidas / total:** _pendente_
- **Custo total $:** _pendente_
- **Custo por etapa:** _pendente_
- **Erros observados:** _pendente_
- **Notas:** _pendente_

---

## Notas operacionais

- Se um provider falhar uma etapa, registrar erro COMPLETO (stacktrace, request_id) aqui antes de tentar outro
- Não fazer fallback silencioso pra outro provider (P0)
- Atualizar `04_matriz_provider_custo.md` após cada run, não no final
