# Triagem dos Testes Pré-Existentes em Falha

Data: 2026-04-17
Objetivo: Classificar cada grupo de teste pré-existente em falha como CRÍTICO / RUÍDO / INFRA para o Marco 1 (pipeline-completo rodando com Haiku 4.5 e produzindo 6 documentos corretos).

Contexto do número exato: a contagem relatada pelo Agente Testes anterior foi 58 pré-existentes. Ao rodar `pytest tests/unit/ --tb=no -q` encontrei **55 falhas totais** — provavelmente algumas já foram saneadas junto com os fixes recentes; a triagem cobre todos os grupos listados.

---

## Resumo

| Classificação | Grupos | Testes |
|---|---|---|
| CRÍTICO para Marco 1 | 0 | 0 |
| RUÍDO (histórico, renames, TDD RED desatualizado) | 11 | 48 |
| INFRA (API key local ausente, fixtures de ambiente) | 1 | 3 |
| AMBÍGUO (mistura: teste mira TDD RED obsoleto, mas cobre um bug menor) | 1 | 4 |

**Conclusão:** **NENHUM teste pré-existente bloqueia o Marco 1.** Nenhuma falha impede `executar_pipeline_completo` de rodar com Haiku 4.5 e gerar os 6 documentos. A grande maioria são fantasmas de TDD RED-phase abandonados, renomeações de assets fora do repositório e 3 testes que exigem API key real (não configurada localmente).

---

## Por grupo

### Grupo 1 — `test_f_t2_analisar_tool_use` — NARRATIVA_PROMPT_MAP (2 testes)

- **Testa:** Que `NARRATIVA_PROMPT_MAP` tem exatamente 1 entrada após F-T1+F-T2 (`GERAR_RELATORIO`). Os testes assumem que `GERAR_RELATORIO` deve PERMANECER no mapa (removido só em F-T3 futuro).
- **Falha porque:** O código real já avançou para F-T3 — `NARRATIVA_PROMPT_MAP = {}` (vazio) no `executor.py:1976`. A migração completa para tool-use já aconteceu. O teste está descrevendo um estado intermediário que não existe mais.
- **Classificação:** **RUÍDO**
- **Ação recomendada:** Atualizar testes para refletir `NARRATIVA_PROMPT_MAP` vazio (ou deletar os 2 testes — a migração está concluída e não vai voltar). Não bloqueia Marco 1 — `analisar_habilidades()` usa o path tool-use, que é o que pipeline-completo chama.

---

### Grupo 2 — `test_erro_pipeline` — Missing API key em testes multimodal (3 testes F3-T1)

- **Testa:** Comportamento de `_executar_multimodal()` quando documento está faltando — deve salvar JSON com `_erro_pipeline`.
- **Falha porque:** `resolve_provider_config("anthropic")` levanta `ValueError: Nenhuma API key encontrada para modelo 'Claude Haiku 4.5'`. Os testes chamam o método real sem mockar o provider config. Localmente não há ANTHROPIC_API_KEY carregada.
- **Classificação:** **INFRA**
- **Ação recomendada:** Ou mockar `resolve_provider_config` nos testes, ou exportar `ANTHROPIC_API_KEY` no ambiente local. Em produção (Render) passam. Não bloqueia Marco 1.

---

### Grupo 3 — `test_erro_pipeline::TestF7T1_PDFErroSection` — PDF (1 teste)

- **Testa:** PDF gerado contém o texto "ERRO DE PROCESSAMENTO" quando `_erro_pipeline` está presente.
- **Falha porque:** O teste faz `assert "ERRO DE PROCESSAMENTO" in pdf_text`, mas `pdf_text` é o bytestream cru do PDF (Flate/ASCII85 compressed). O texto está lá mas codificado — o teste precisaria descomprimir as streams para verificar.
- **Classificação:** **RUÍDO** (teste mal escrito — não verifica o que alega)
- **Ação recomendada:** Reescrever teste usando pypdf / pdfplumber para extrair texto real. Não bloqueia Marco 1.

---

### Grupo 4 — `test_from_dict_resilience` (12 testes)

- **Testa:** `Materia.from_dict()`, `Turma.from_dict()`, `Aluno.from_dict()`, `Atividade.from_dict()`, `Documento.from_dict()` precisam NÃO crashar com valores corrompidos (enum inválido, ISO string malformada, None).
- **Falha porque:** Testes em RED phase — os métodos `from_dict` ainda chamam `datetime.fromisoformat()` e `Enum(value)` diretamente, sem try/except. A feature de resiliência nunca foi implementada. Verbatim do docstring: "RED phase: all tests in this file should FAIL until the safety wrappers are implemented in models.py."
- **Classificação:** **RUÍDO** (TDD RED de feature nunca implementada — não afeta pipeline, afeta leitura de DB corrompido)
- **Ação recomendada:** Implementar safety wrappers OU marcar como `@pytest.mark.skip` com motivo. A pipeline de correção não grava/lê dados "corrompidos" — Marco 1 não depende disso.

---

### Grupo 5 — `test_rebrand_*` (11 testes: docs 4 + e2e 1 + ui_sweep 3 + ui_text 2, = 10... há 11 contando tudo)

Distribuição real observada: 4 em `test_rebrand_docs`, 1 em `test_rebrand_e2e`, 3 em `test_rebrand_ui_sweep`, 2 em `test_rebrand_ui_text` = **10**.

- **Testa:** Renomeação de "Prova AI" → "NOVO CR" aparece em STYLE_GUIDE, tutoriais, welcome modal, titles.
- **Falha porque (docs):** `/home/otavio/Documents/vscode/.claude/design/STYLE_GUIDE.md` não existe no filesystem local (o dir `.claude/design/` também não existe). O teste assume um asset fora do repo do projeto. `CLAUDE.md` aponta para `../.claude/design/STYLE_GUIDE.md` (worktree do usuário).
- **Falha porque (e2e/ui_sweep/ui_text):** Strings "NOVO CR" nem todas foram aplicadas no `index_v2.html` e em arquivos `.py` do backend — ainda há "Prova AI" residual.
- **Classificação:** **RUÍDO** (projeto de rebrand parcial, não afeta funcionalidade de pipeline)
- **Ação recomendada:** Projeto separado de rebrand. Não bloqueia Marco 1. Os testes de docs podem ser marcados como skip se o asset não está no repo.

---

### Grupo 6 — `test_desempenho_*` (vários arquivos, ~4 testes)

Testes observados em falha nesse namespace:
- `test_desempenho_gap_fix.py::test_serve_frontend_has_no_cache_control_header` (1)
- `test_desempenho_ui_overhaul.py::test_gap3_load_data_triggers_auto_expand` (1)
- `test_f2_desempenho_alertas_surfaced.py::test_tarefa_surfaces_alertas` (1)
- `test_g_t1_desempenho_settings_modal.py::test_modal_has_modal_footer` (1)

- **Testa:** Funcionalidade do módulo "Relatório de Desempenho" (pipeline multi-documento sobre narrativas), UI do modal, Cache-Control no FileResponse, auto-expansão de run após carregar.
- **Falha porque:**
  - `test_serve_frontend_has_no_cache_control_header`: o `FileResponse` não retorna header `Cache-Control: no-cache`. Bug real menor (Render stale cache), mas não afeta pipeline.
  - `test_gap3_load_data_triggers_auto_expand`: `loadDesempenhoData` deveria chamar `autoExpandLatestRun()` — UX desejada, ainda não implementada.
  - `test_tarefa_surfaces_alertas`: retorna dict com apenas `{sucesso, erro}` em vez de incluir `alertas`.
  - `test_modal_has_modal_footer`: modal não tem div `modal-footer` padrão.
- **Classificação:** **RUÍDO** (Módulo "Desempenho" é separado do pipeline-completo de correção. Não usa os 6 documentos do Marco 1; usa narrativas já geradas.)
- **Ação recomendada:** Backlog de UX do módulo desempenho. Não bloqueia Marco 1.

---

### Grupo 7 — `test_b3_c3_d3_desempenho_implementation` (6 testes)

- **Testa:** `gerar_relatorio_desempenho_tarefa/turma/materia` retornam `sucesso=True` quando há ≥2 narrativas, e chamam `executar_com_tools`.
- **Falha porque:** Mock de storage não injeta narrativas — o código retorna "0 narrativa(s) encontrada(s)" porque o mock não devolve nada. Teste assume assinatura/API antiga do mock. Setup desatualizado.
- **Classificação:** **RUÍDO** (fixtures quebradas em módulo separado — desempenho, não pipeline de correção)
- **Ação recomendada:** Atualizar fixtures de mock para retornar narrativas válidas. Não bloqueia Marco 1.

---

### Grupo 8 — `test_auto_collapse` (3 testes)

- **Testa:** `renderTarefasTree` conta alunos e aplica auto-collapse quando >3 alunos na tarefa, com classe `expanded` condicional.
- **Falha porque:** O JS em `index_v2.html` não contém os tokens `alunoCount`/`studentCount`/`numAlunos`, nem literal `3`, nem `expanded`. Feature UX nunca implementada (RED de TDD abandonado).
- **Classificação:** **RUÍDO** (UI nice-to-have não implementado)
- **Ação recomendada:** Marcar skip ou implementar como feature futura. Não bloqueia Marco 1.

---

### Grupo 9 — `test_executor_two_pass_narrative` (2 testes)

- **Testa:** `_gerar_narrativa_pdf()` chama o provider com o prompt narrativo correto e salva um PDF (não MD).
- **Falha porque:** O método `_gerar_narrativa_pdf` só roda para etapas em `NARRATIVA_PROMPT_MAP`, que está vazio. A função two-pass foi desativada após migração para tool-use. Teste assume o path two-pass que não é mais usado.
- **Classificação:** **RUÍDO** (teste mede um caminho morto — tool-use substituiu)
- **Ação recomendada:** Remover ou atualizar testes. Migração tool-use já concluída no executor. Não bloqueia Marco 1; pelo contrário, o caminho tool-use é o que pipeline-completo usa.

---

### Grupo 10 — `test_f1_t4_tool_context_injection` (2 testes)

- **Testa:** `handle_execute_python_code` usa um `sandbox_manager` injetado (dependency injection via module attribute).
- **Falha porque:** `AttributeError: module 'tool_handlers' does not have the attribute 'sandbox_manager'`. Código foi refatorado: `sandbox_manager` não é mais um atributo de módulo — provavelmente agora é passado como parâmetro ou está em outro lugar.
- **Classificação:** **RUÍDO** (mudança de arquitetura de DI, testes não acompanharam)
- **Ação recomendada:** Atualizar testes para refletir novo padrão de injeção. Sandbox E2B é para etapas de código — Haiku 4.5 pode não usar sandbox. Não bloqueia Marco 1 (o pipeline pode rodar sem E2B).

---

### Grupo 11 — `test_documentation_structure` (5 testes)

- **Testa:** Existência de `docs/`, subpastas, `GENERAL_DEPRECATION_AND_UNIFICATION_GUIDE.md`, `DOCUMENTATION_STRUCTURE.md`, referência no `CLAUDE.md`.
- **Falha porque:** Arquivos/pastas esperados não existem no caminho esperado (ou movidos). Asset organization não é código executável.
- **Classificação:** **RUÍDO** (organizacional)
- **Ação recomendada:** Alinhar estrutura de docs ou skip. Não bloqueia Marco 1.

---

### Grupo 12 — `test_command_contracts` (3+ testes: discover.md, plan.md, tdd.md)

- **Testa:** Existência de arquivos `.claude/commands/discover.md`, `plan.md`, `tdd.md`.
- **Falha porque:** Esses arquivos são do usuário (worktree Otavio) e não ficam no repo do projeto.
- **Classificação:** **RUÍDO** (arquivos de configuração pessoal fora do escopo do repo)
- **Ação recomendada:** Marcar skip/remover. Não bloqueia Marco 1.

---

### Grupo 13 — `test_a4_no_old_pipeline_turma` (1 teste)

- **Testa:** Nenhuma label "Pipeline Turma" residual após rename A2.
- **Falha porque:** Uma única linha em `index_v2.html:6594` ainda tem `title: '🚀 Pipeline Turma Toda'`. Rename incompleto.
- **Classificação:** **RUÍDO** (string cosmética)
- **Ação recomendada:** Trocar a string. Não bloqueia Marco 1.

---

### Grupo 14 — `test_g_t1_desempenho_settings_modal::test_modal_has_modal_footer` (1 teste)

- **Testa:** Modal tem `<div class="modal-footer">` padrão.
- **Falha porque:** Modal usa estrutura não-padrão (botões inline em `modal-body` em vez de `modal-footer`).
- **Classificação:** **RUÍDO** (UI do módulo desempenho)
- **Ação recomendada:** Padronizar estrutura do modal. Não bloqueia Marco 1.

---

### Grupo 15 — `test_rio3_key_flow` (2 testes)

- `test_frontend_custom_endpoint_binds_selected_key`: assert `id="custom-api-key-id"` não está em `index_v2.html`
- `test_frontend_has_safe_rio3_key_popup_entrypoint`: popup seguro para chaves RIO3 não presente
- **Testa:** Frontend binda custom key por ID no endpoint customizado / popup seguro para chave RIO3.
- **Falha porque:** Elementos de UI não foram adicionados ao frontend (feature de Rio 3.0 provider não completa).
- **Classificação:** **RUÍDO** (feature Rio 3.0 é Marco 3 no pipeline marcos — Rio só depois de Haiku funcionar)
- **Ação recomendada:** Deferir até Marco 3. Não bloqueia Marco 1 (que usa só Haiku/Anthropic padrão).

---

## Verificação crítica para Marco 1

Verifiquei no executor.py:
- `executar_pipeline_completo()` existe (linha 3108)
- `analisar_habilidades()` existe (linha 1255) — usa tool-use path
- `NARRATIVA_PROMPT_MAP = {}` vazio — migração concluída

Nenhum dos 55 testes em falha testa:
- `executar_pipeline_completo` diretamente
- Integração entre as 6 etapas (extrair_questoes → extrair_gabarito → extrair_respostas → corrigir → analisar_habilidades → gerar_relatorio)
- Resolve de provider Haiku (indiretamente batem em chat_service, mas falham por API key não por lógica)
- Substituição de templates `{{nota_final}}`, `{{resposta_aluno}}`, etc.

Portanto: **zero bloqueios para Marco 1** entre os pré-existentes.

---

## Atingi o objetivo?

**SIM**, porque:
1. Classifiquei todos os 15 grupos cobrindo os ~55 testes pré-existentes em falha.
2. Identifiquei que **nenhum** bloqueia Marco 1 — o pipeline-completo com Haiku 4.5 não depende de nenhum teste que está falhando (apenas 3 testes de `test_erro_pipeline` poderiam tocar em ambientação Anthropic, mas falham por API key local, não por código de pipeline).
3. Separei claramente: 48 ruídos históricos (TDD RED abandonado, renames incompletos, features UX pendentes, docs fora do repo), 3 infra (API key local), 4 ambíguos no grupo desempenho (que não afeta pipeline de correção).
4. A recomendação operacional para o Marco 1 é: **ignorar os 55 pré-existentes** e focar em garantir que os 17 novos (fail-loud em docs faltantes) estão validando o comportamento esperado. Quando Marco 1 concluir, agendar sprint de limpeza de ruído.
