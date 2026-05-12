# Investigacao: Alunos Fantasma + Templates Nao Renderizados

Data: 2026-04-17

---

## PROBLEMA A: 3 Alunos Corrigidos Sem `prova_respondida`

### Alunos Afetados (atividade 126e8b5ad7dd6d59 — Lista0, Algebra Linear)

| Aluno | aluno_id | Docs existentes |
|-------|----------|-----------------|
| ALICE BARROS LOURENCINI PALAORO | 9b0f104fa9e7c5d9 | extracao_respostas, correcao (JSON+PDF), analise_habilidades (JSON+PDF), relatorio_final (PDF) |
| FABRICIO DALVI VENTURIM | cdec224bb0733be0 | extracao_respostas, correcao (JSON+PDF) |
| RAPHAEL FELBERG LEVY | 85b4e1c73e9a37f0 | extracao_respostas, correcao (JSON+PDF) |

**Nenhum dos tres possui documento `prova_respondida`.**

### Conteudo das Extracoes de Respostas

Todas as 3 `extracao_respostas` contem **7 questoes marcadas como em_branco=true**, com 0 questoes respondidas. Exemplos de observacoes:

- Alice (claude-haiku-4-5): `"Questao nao respondida"` em todas as 7
- Fabricio (gemini-3-flash): `"Questao deixada totalmente em branco"` em todas as 7
- Raphael (gemini-3-flash): `"Conteudo da resposta nao fornecido no documento"` em todas as 7

Todos contem `_avisos_documento` com codigo `MISSING_CONTENT`, indicando que a IA nao encontrou respostas.

### Conteudo da Correcao (exemplo: Alice)

A correcao JSON mostra `nota_final: 0.0` com todas as 7 questoes `status: "em_branco"`. O feedback eh detalhado e pedagogico — descreve exatamente o que cada questao exigia e oferece recomendacoes. O campo `criado_por` eh `"pipeline_tool"` (tool-use).

### Causa Raiz: Como o Pipeline Permitiu Isso

**Caminho do bug no codigo:**

1. **`EXTRAIR_RESPOSTAS` nao requer `prova_respondida` na checagem de dependencias JSON** (`_preparar_contexto_json`, linhas 1060-1095 de `executor.py`). So verifica `questoes_extraidas` e `gabarito_extraido`. A unica checagem de arquivo fisico esta em `_coletar_arquivos_para_etapa` (linhas 936-948), que tenta buscar `PROVA_RESPONDIDA` — se nao encontra, o array `arquivos` fica vazio.

2. **A checagem de arquivo vazio (linhas 684-705) deveria ter barrado**, porque `EXTRAIR_RESPOSTAS` esta na lista `etapas_requerem_arquivo`. MAS — isso so se aplica ao caminho `executar_etapa_multimodal`. Se o pipeline usou `executar_etapa` (texto), essa checagem nao existe.

3. **Hipotese mais provavel**: O pipeline `processar_aluno_completo` (linha 3273+) chama `_executar_com_retry(EXTRAIR_RESPOSTAS, aluno_id)`, que vai para `executar_etapa()` (nao multimodal, linhas 3162-3169 no else). No caminho texto, nao ha checagem de arquivo fisico obrigatorio.

4. **Uma vez que `extracao_respostas` existe** (mesmo com tudo em branco), `CORRIGIR` roda normalmente porque seu unico prerequisito JSON obrigatorio eh `respostas_aluno` (que existe — so tem tudo em branco). A IA corrige normalmente, dando nota 0 para tudo.

5. O pipeline continua encadeando: CORRIGIR -> ANALISAR_HABILIDADES -> GERAR_RELATORIO, sem nunca verificar se `prova_respondida` original existe.

**Resumo**: O pipeline nao tem nenhuma validacao de que o documento `prova_respondida` original existe antes de rodar `EXTRAIR_RESPOSTAS`. A IA recebe um prompt pedindo para extrair respostas de... nada. Ela obedientemente retorna tudo em branco. O resto do pipeline encadeia a partir disso.

### Evidencia de que Nao Ha prova_respondida Mal-Linkada

A API `/documentos/todos` para cada aluno retorna documentos com `aluno_id` correto. Nenhum documento `prova_respondida` aparece em nenhuma consulta. Nao ha linkagem errada — simplesmente nao existe o documento.

### Correcao Recomendada

1. **No `processar_aluno_completo`**: Antes de rodar `extrair_respostas`, verificar se existe pelo menos 1 documento `PROVA_RESPONDIDA` para o aluno. Se nao existir, pular o aluno inteiro (ou todas as etapas per-aluno).

2. **No `_preparar_contexto_json` para CORRIGIR**: Adicionar `prova_respondida` como dependencia obrigatoria (ou pelo menos como warning visivel).

3. **Na UI**: Se `extracao_respostas` retornar 100% em branco com `MISSING_CONTENT`, mostrar banner vermelho "Prova nao encontrada — verifique se o arquivo foi enviado".

---

## PROBLEMA B: `{{nota_final}}` Literal nos Relatorios

### Mecanismo de Geracao do Relatorio Final

O `gerar_relatorio()` (executor.py:1306) funciona assim:

1. Chama `_preparar_variaveis_texto()` (linha 1334) que monta um dict de variaveis
2. Chama `_preparar_contexto_json()` (linha 1340) e **silenciosamente descarta** `_documentos_faltantes` (linha 1343)
3. Renderiza o prompt com `prompt.render(**variaveis)` (linha 1348)
4. Envia para IA com tool-use (create_document + execute_python_code)

### Onde `nota_final` Deveria Ser Substituida

**Fonte**: `_preparar_variaveis_texto()` (linhas 1538-1549) calcula `nota_final` a partir do JSON de `correcoes`:
- Se `correcoes` for dict com campo `nota_final`, usa esse valor
- Se `correcoes` for lista, soma os `.nota` de cada item
- Se falhar: coloca `"N/A"`

**Destino**: O prompt em `prompts.py:498` contem `**Nota Final:** {{nota_final}}` e `"nota_final": "{{nota_final}}"` (linha 515).

### Causa Raiz: Dois Caminhos de Falha

**Caminho 1 — `correcoes` nao esta disponivel como variavel texto**:

O `_preparar_variaveis_texto()` (linhas 1458-1497) itera documentos do aluno. Para carregar `correcoes`, precisa de um documento tipo `CORRECAO`. Se nao encontra (ou se `_ler_documento_texto` retorna vazio para JSON), a variavel `correcoes` nao entra no dict, e o bloco das linhas 1538-1549 nao executa. Resultado: `nota_final` nunca eh definida.

**Caminho 2 — `correcoes` existe mas parsing falha**:

O `except:` generico na linha 1548 captura qualquer erro de JSON parsing e coloca `"N/A"`. Isso substitui `{{nota_final}}` por `N/A`, nao por literal. Entao esse caminho NAO gera o bug.

**Caminho 3 (MAIS PROVAVEL) — O template DENTRO do JSON exemplo**:

A causa mais insidiosa esta na linha 515 do prompt:
```
"nota_final": "{{nota_final}}",
```

Esse `{{nota_final}}` eh parte do EXEMPLO de output JSON no prompt. Quando `nota_final` eh substituida corretamente no prompt, funciona. Mas o problema eh que a **IA recebe esse template e pode decidir copiar literalmente** a estrutura, incluindo o `{{nota_final}}` como string.

Especificamente, a LLM recebe o prompt renderizado com algo como:
```
"nota_final": "0.0",
```
E deveria produzir `"nota_final": 0.0` no output. Mas se `nota_final` NAO foi substituida no prompt (Caminho 1), a LLM recebe:
```
"nota_final": "{{nota_final}}",
```
E pode copiar isso literalmente para o output JSON, gerando o documento com `{{nota_final}}` literal.

### Fluxo Detalhado do Bug

1. `gerar_relatorio()` chama `_preparar_variaveis_texto()` que itera documentos do aluno
2. Se o documento de `correcao` NAO for encontrado (ou nao for parseavel), `correcoes` nao entra no dict
3. O bloco `if "correcoes" in variaveis and "nota_final" not in variaveis:` (linha 1538) NAO executa
4. `nota_final` permanece indefinida
5. `prompt.render(**variaveis)` faz substituicao: `texto.replace("{{nota_final}}", ...)` — mas como `nota_final` nao esta no kwargs, o `{{nota_final}}` permanece literal no prompt
6. A IA recebe o prompt com `{{nota_final}}` literal e copia para o JSON de saida
7. O documento `relatorio_final` eh salvo com `"nota_final": "{{nota_final}}"` literal

### Agravante: `gerar_relatorio()` Descarta Faltantes Silenciosamente

Na linha 1343: `contexto_json.pop("_documentos_faltantes", [])` — mesmo quando `correcoes` eh obrigatoria e esta faltando, o metodo ignora e continua. O `_preparar_contexto_json` corretamente identifica que `correcoes` falta (linha 1098-1106), mas `gerar_relatorio()` descarta esse sinal.

### Correcao Recomendada

1. **Imediato**: Em `_preparar_variaveis_texto`, se `nota_final` nao foi definida apos todo o processamento, definir um fallback explicitamente:
   ```python
   if "nota_final" not in variaveis:
       variaveis["nota_final"] = "N/A (correcao nao encontrada)"
   ```

2. **Robustez**: Em `gerar_relatorio()`, NAO descartar `_documentos_faltantes`. Se `correcoes` falta, falhar o stage com erro estruturado (assim como `executar_etapa_multimodal` faz nas linhas 618-659).

3. **Prompt**: Remover o `"nota_final": "{{nota_final}}"` do exemplo JSON no prompt (linha 515). O schema de output ja esta definido em `STAGE_TOOL_INSTRUCTIONS` (linha 229+). O exemplo com template variables eh confuso para a IA.

4. **Validacao pos-geracao**: Verificar o JSON de output para literais `{{...}}` antes de salvar. Se encontrar, marcar como erro.

---

## Conexao Entre os Dois Problemas

Os dois problemas podem ocorrer juntos: um aluno fantasma (sem prova_respondida) gera uma correcao com nota 0. Se por algum motivo a correcao nao eh encontrada pelo `_preparar_variaveis_texto` do relatorio (race condition de storage, Supabase download falhando, etc.), o relatorio sai com `{{nota_final}}` literal.

No caso especifico de Alice (que tem relatorio_final), a correcao JSON EXISTE e contem `nota_final: 0.0`. Se o relatorio foi gerado corretamente, deveria ter `0.0`. Para verificar se o relatorio dela tem o bug de template, seria necessario baixar o PDF e examinar — mas a API retorna `conteudo: null, pode_visualizar: false` para PDFs.

---

## Resumo Executivo

| Problema | Causa Raiz | Severidade | Fix |
|----------|-----------|------------|-----|
| **A: Fantasmas** | Pipeline nao valida existencia de `prova_respondida` antes de `EXTRAIR_RESPOSTAS` | Media (nota 0 eh "correta" dado que prova nao existe) | Guardrail pre-pipeline: checar se aluno tem prova |
| **B: {{nota_final}}** | `nota_final` nao entra nas variaveis se `correcoes` nao eh encontrado; prompt contem template no exemplo de output | Alta (relatorio publico com lixo) | Fallback para `nota_final` + remover template do exemplo |
