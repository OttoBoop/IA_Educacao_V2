# Ad-hoc Test Scripts

These are quick utility scripts for testing the **live Prova AI API**.

**NOTE:** These are NOT part of the pytest test suite. They're for manual/ad-hoc testing.

---

## Active Scripts

| Script | Purpose | Endpoints Tested |
|--------|---------|------------------|
| `test_atividades.py` | Quick test of atividades endpoint | `/api/atividades` |
| `test_doc_endpoint.py` | Test documentos content endpoint | `/api/documentos/{id}/conteudo` |
| `test_online.py` | Verify system is online, test matérias/turmas | `/api/materias`, `/api/turmas`, `/api/atividades` |

### Usage

```bash
cd IA_Educacao_V2/backend/scripts
python test_online.py
```

### Notes

- `test_online.py` may need updating - uses `/api/atividades` without required `turma_id` parameter

---

## Deprecated Scripts (`deprecated/`)

These scripts test **DISABLED routers** (see `docs/guides/API_UNIFICATION_GUIDE.md`):

| Script | Disabled Router | Notes |
|--------|-----------------|-------|
| `test_deployed.py` | `pipeline` | Tests full pipeline execution |
| `test_resultados_endpoint.py` | `resultados` | Tests `/api/resultados/{atividade}/{aluno}` |
| `teste_chat_online.py` | `chat` | Comprehensive chat test with documents |

### Router Status (from API_UNIFICATION_GUIDE.md)

| Router | Status |
|--------|--------|
| `extras` | **Active** |
| `prompts` | **Active** |
| `code_executor` | **Active** |
| `chat` | **DISABLED** |
| `pipeline` | **DISABLED** |
| `resultados` | **DISABLED** |

### Reactivation

If these routers are reactivated in the future:
1. Move scripts back to `scripts/`
2. Verify they work with current API
3. Update this README

---

## Adding New Scripts

When adding new ad-hoc test scripts:
1. Check if the router is active (see table above)
2. If router is disabled, place in `deprecated/`
3. Add entry to the appropriate table in this README
4. Consider adding proper pytest tests instead
