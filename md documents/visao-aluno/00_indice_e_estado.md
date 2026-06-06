# 00 — Loop Operacional: Visao Do Aluno

**Leia este arquivo primeiro em toda retomada.**
**Log vivo:** [05_log_operacional.md](05_log_operacional.md)

## Painel Do Loop

| Campo | Estado |
|---|---|
| Objetivo | Criar uma visao onde se escolhe um aluno e se ve apenas o que pertence a ele. |
| Proximo passo | Loop 6: base longitudinal por aluno. |
| Primeiro patch | Fechado: backend/UI da visao aluno + base/leitura/geracao aluno-turma por provider + deploy Render + smoke remoto. |
| Nao fazer sem novo loop | Provider real caro, portal autenticado. |
| Regra critica | A unidade e `aluno_id + turma_id`, nao `aluno_id + materia_id`. |

## Por Que A Regra Critica Existe

Aluno pode repetir materia e entrar em multiplas turmas da mesma materia. Materia
agrupa visualmente; turma separa trajetorias.

## Estado Atual Do Codigo

- A interface geral ainda e uma visao unica/admin-like.
- `Aluno` ja suporta multiplas turmas via `AlunoTurma`.
- `storage.get_turmas_do_aluno()` ja retorna turmas do aluno com materia.
- `showAluno()` agora e o MVP da visao aluno e consome `/api/alunos/{aluno_id}/visao`.
- Desempenho atual e agregado: tarefa, turma, materia.
- Base de leitura aluno-turma existe em `GET /api/desempenho/aluno/{aluno_id}/turma/{turma_id}`.
- Geracao deterministica aluno-turma existe em `POST /api/executar/pipeline-desempenho-aluno-turma`.
- Falta desempenho longitudinal por **aluno**.

---

## Tarefa Atual: MVP

Status: **fechada em 2026-06-05**.

Implementado apenas leitura e UI basica:

- `GET /api/alunos/{aluno_id}/visao`
- Tela do aluno com:
  - materia;
  - turmas separadas;
  - atividades da turma;
  - status dos docs do aluno por atividade.

## Depois Do MVP

- `relatorio_desempenho_aluno_turma`
- `relatorio_desempenho_aluno_longitudinal`
- `POST /api/executar/pipeline-desempenho-aluno-turma`
- `POST /api/executar/pipeline-desempenho-aluno-longitudinal`

---

## Contrato Do Endpoint MVP

```text
GET /api/alunos/{aluno_id}/visao
```

Deve retornar:

- aluno;
- materias agrupadas;
- turmas do aluno dentro de cada materia;
- atividades de cada turma;
- status dos documentos daquele aluno em cada atividade:
  - prova respondida;
  - correcao;
  - analise de habilidades;
  - relatorio final.

Nao pode:

- misturar duas turmas da mesma materia;
- trazer documento de outro aluno;
- tratar relatorio agregado de turma/materia como relatorio individual;
- fingir longitudinal quando a base e pequena.

---

## Checklist Executavel

- [x] Criar endpoint `/api/alunos/{aluno_id}/visao`.
- [x] Testar aluno em duas turmas da mesma materia.
- [x] Testar aluno sem documentos.
- [x] Testar que documento de outro aluno nao entra.
- [x] Atualizar `showAluno()` para usar esse endpoint.
- [x] Renderizar materia > turma > atividade > status.
- [x] Atualizar este log com evidencia do que passou/falhou.

Primeiro loop ficou apenas no MVP de leitura/UI. Pipelines ficam para o Loop 2.

Evidencia principal:

```text
cd backend
/home/otavio/Documents/vscode/.venv/bin/python -m pytest tests/integration/test_visao_aluno_endpoint.py tests/unit/test_visao_aluno_frontend.py -q
8 passed, 1 warning in 0.90s
```

---

## Loop 2: Relatorio Aluno-Turma

Status: **fechado em 2026-06-05** como base de leitura/diagnostico.

Objetivo: criar a base tecnica para gerar desempenho individual de um aluno em
uma turma especifica, sem misturar repetencias.

- [x] Mapear a pipeline de desempenho atual.
- [x] Definir contrato de leitura para aluno-turma.
- [x] Implementar `GET /api/desempenho/aluno/{aluno_id}/turma/{turma_id}`.
- [x] Garantir que a base usa apenas atividades/documentos daquele aluno na turma.
- [x] Bloquear ou sinalizar quando nao houver base minima.
- [x] Atualizar log com evidencia real.

Evidencia principal:

```text
cd backend
/home/otavio/Documents/vscode/.venv/bin/python -m pytest tests/integration/test_visao_aluno_endpoint.py tests/unit/test_visao_aluno_frontend.py tests/integration/test_desempenho_aluno_turma_endpoint.py tests/unit/test_desempenho_api_endpoints.py -q
39 passed, 1 warning in 2.14s
```

Ainda nao foi feito: provider/geracao real e longitudinal automatico.

---

## Loop 3: Gerar Relatorio Aluno-Turma

Status: **fechado em 2026-06-05** com geracao deterministica v1, sem provider caro.

Objetivo: criar o primeiro fluxo que gera um relatorio individual de desempenho
para um aluno em uma turma especifica, usando apenas as atividades daquele aluno
naquela turma.

- [x] Decidir se `relatorio_desempenho_aluno_turma` entra agora em `TipoDocumento`.
- [x] Implementar `POST /api/executar/pipeline-desempenho-aluno-turma`.
- [x] Reusar a regra de base minima de `GET /api/desempenho/aluno/{aluno_id}/turma/{turma_id}`.
- [x] Salvar metadata com `scope`, `aluno_id`, `turma_id`, `materia_id` e `atividade_ids`.
- [x] Bloquear geracao quando nao houver `relatorio_final` do aluno na turma.
- [x] Adicionar testes sem provider real caro.
- [x] Atualizar log com evidencia real.

Evidencia principal:

```text
cd backend
/home/otavio/Documents/vscode/.venv/bin/python -m pytest tests/integration/test_visao_aluno_endpoint.py tests/unit/test_visao_aluno_frontend.py tests/integration/test_desempenho_aluno_turma_endpoint.py tests/unit/test_desempenho_api_endpoints.py -q
41 passed, 1 warning in 1.41s
```

Ainda nao foi feito: provider LLM para aluno-turma e longitudinal automatico.

---

## Loop 4: Deploy Render E Smoke Remoto

Status: **substituido em 2026-06-05**.

Objetivo: colocar a visao do aluno e a geracao aluno-turma no Render e testar
contra dados reais, sem servidor local.

- [x] Commit `5297c45` publicado em `origin/main`.
- [x] Render deploy `dep-d8hj5itckfvc73avqktg` ficou `live`.
- [x] `/api/deploy-info` confirmou `commit=5297c45` e `source=RENDER_GIT_COMMIT`.
- [x] `GET /api/alunos/{aluno_id}/visao` testado com Alvaro.
- [x] `GET /api/desempenho/aluno/{aluno_id}/turma/{turma_id}` testado com Alvaro + turma `2026-1`.
- [x] `POST /api/executar/pipeline-desempenho-aluno-turma` gerou doc `49b70d1dba0b8f22`.
- [x] Segunda chamada do POST retornou `skipped: true`, sem duplicar.
- [x] Smoke visual remoto com Playwright passou e gerou screenshot em `logs/render-visao-aluno-alvaro-clean-2026-06-05.png`.

Revisao critica: o documento `49b70d1dba0b8f22` **nao e aceite de produto**.
Ele continha a frase `conteudo nao extraido automaticamente`, portanto era
apenas prova de persistencia/escopo, nao relatorio de desempenho.

Evidencia principal:

```text
https://ia-educacao-v2.onrender.com/api/deploy-info
commit=5297c45

Aluno: ALVARO JOEL TICONA MOTTA
Materia: Algebra Linear Avancada
Turma: 2026-1
Atividades: Lista0, Prova 01
Docs do aluno: 33
Relatorio aluno-turma: 49b70d1dba0b8f22
```

Ainda nao foi feito: longitudinal automatico.

---

## Loop 5: Hotfix Relatorio Aluno-Turma Com Leitura Real

Status: **fechado em 2026-06-05** no site oficial.

Objetivo: remover a geracao deterministica/placeholder e exigir leitura real do
documento por provider de IA.

- [x] Commit `0e0d38e` publicado em `origin/main`.
- [x] Render deploy `dep-d8hjmps8aovs73dendtg` ficou `live`.
- [x] `/api/deploy-info` confirmou `commit=0e0d38e`.
- [x] `POST /api/executar/pipeline-desempenho-aluno-turma` agora usa provider `analyze_document`.
- [x] Placeholder `conteudo nao extraido automaticamente` foi removido do caminho de sucesso.
- [x] Se o provider nao ler o documento, o endpoint falha em vez de salvar relatorio falso.
- [x] Relatorio antigo `deterministica_v1` nao bloqueia regeneracao.
- [x] Smoke remoto com `force_reexec=true` gerou doc `8f1c49f009189df1`.
- [x] Documento novo tem `ia_provider=openai`, `ia_modelo=gpt-4o`, `tokens_usados=3203`.
- [x] Download novo salvo em `logs/downloads/relatorio_desempenho_aluno_turma_8f1c49f009189df1.md`.

Evidencia principal:

```text
Relatorio aluno-turma: 8f1c49f009189df1
Geracao: provider_document_read_v1
Provider: openai / gpt-4o
Tokens: 3203
Conteudo: sintese pedagogica, nota 5.35/10, pontos fortes,
areas de melhoria, recomendacoes e evidencias por questao.
Frases proibidas: ausentes.
```

Ainda nao foi feito: longitudinal automatico.

---

## Loop 5.1: Contrato Multi-IA Para Aluno-Turma

Status: **implementado em 2026-06-06**.

Objetivo: alinhar a visao do aluno ao contrato geral do programa: qualquer
documento pode ser processado por uma ou varias IAs escolhidas explicitamente,
sem fallback silencioso.

- `model_id` e o campo canonico.
- `provider_id` continua aceito como legado.
- `model_ids` permite gerar comparativo multi-IA no mesmo `aluno_id + turma_id`.
- `source_document_ids` permite escolher quais `relatorio_final` do aluno entram
  no relatorio aluno-turma.
- Metadata nova registra `requested_model_id`, `resolved_provider`,
  `resolved_model`, `source_document_ids` e `selection_mode`.
- Novo endpoint generico: `POST /api/executar/documento-multi-ia`.

Regra preservada: a unidade continua sendo `aluno_id + turma_id`, nunca
`aluno_id + materia_id`.

---

## Loop 6: Longitudinal Por Aluno

Objetivo: combinar relatorios aluno-turma anteriores do mesmo aluno em ordem
temporal, respeitando repetencia e turmas diferentes na mesma materia.

- [ ] Implementar leitura `GET /api/desempenho/aluno/{aluno_id}`.
- [ ] Coletar `relatorio_desempenho_aluno_turma` por aluno.
- [ ] Ordenar por ano/turma/data dos documentos.
- [ ] Bloquear quando nao houver relatorio aluno-turma suficiente.
- [ ] Implementar `relatorio_desempenho_aluno_longitudinal`.
- [ ] Implementar `POST /api/executar/pipeline-desempenho-aluno-longitudinal`.
- [ ] Adicionar testes sem provider real caro.
- [ ] Atualizar log com evidencia real.

---

## Tipos Atuais/Futuros

```python
RELATORIO_DESEMPENHO_ALUNO_TURMA = "relatorio_desempenho_aluno_turma"
RELATORIO_DESEMPENHO_ALUNO_LONGITUDINAL = "relatorio_desempenho_aluno_longitudinal"
```

Metadata minima:

```json
{
  "scope": "aluno_turma",
  "aluno_id": "...",
  "turma_id": "...",
  "materia_id": "...",
  "atividade_ids": ["..."]
}
```

```json
{
  "scope": "aluno_longitudinal",
  "aluno_id": "...",
  "relatorios_aluno_turma_ids": ["..."]
}
```

---

## Testes Minimos

- aluno em duas turmas da mesma materia aparece duas vezes;
- aluno sem documentos aparece com pendencias;
- documento de outro aluno nao aparece;
- UI renderiza materia > turma > atividade;
- relatorio aluno-turma bloqueia sem base minima;
- longitudinal bloqueia sem relatorios aluno-turma.

---

## Fora Do Escopo Do Primeiro Loop

- Portal autenticado.
- Migracao grande em `Documento`.
- Pipeline real com provider.
- Longitudinal automatico.

## Como Retomar Sem Se Perder

1. Ler este arquivo.
2. Ler as ultimas linhas de [05_log_operacional.md](05_log_operacional.md).
3. Fazer somente o primeiro item aberto do checklist atual.
4. Atualizar o log com resultado real.
5. Nao abrir nova frente antes de fechar ou bloquear o item atual.
