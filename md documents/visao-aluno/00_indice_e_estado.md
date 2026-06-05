# 00 — Loop Operacional: Visao Do Aluno

**Leia este arquivo primeiro em toda retomada.**
**Log vivo:** [05_log_operacional.md](05_log_operacional.md)

## Painel Do Loop

| Campo | Estado |
|---|---|
| Objetivo | Criar uma visao onde se escolhe um aluno e se ve apenas o que pertence a ele. |
| Proximo passo | Loop 4: base longitudinal por aluno. |
| Primeiro patch | Fechado: backend/UI da visao aluno + base/leitura/geracao aluno-turma + testes focados. |
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

## Loop 4: Longitudinal Por Aluno

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
