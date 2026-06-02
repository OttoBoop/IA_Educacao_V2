# 02 — Diagnóstico do bug do botão Gerar Relatório

> **Status:** ✅ Causa-raiz confirmada via 3 Explore agents em paralelo (2026-05-24)
> **Sintoma reportado:** botão aparece clicável por uns ms e depois TROCA pra um botão novo que não funciona

---

## Causa-raiz

Não é regressão git. Não é Codex/outro agente. É um bug local em `loadDesempenhoData()` que SOBRESCREVE o botão funcional quando o backend retorna `has_atividades=false`.

### Fluxo da quebra

```
T0  Usuário clica aba "Desempenho da turma"
T1  showTurmaTab('desempenho') escreve container.innerHTML com o botão CORRETO
    → onclick="openDesempenhoSettings('turma', 'XXX')"
    → ⏱️ Janela onde o botão está clicável (~50–500 ms até T3)
T2  loadDesempenhoData('turma', 'XXX') é chamado (assincronamente)
    → fetch('/desempenho/turma/XXX')
T3  Response chega: { has_atividades: false, runs: [] }
T4  Linha 11963 EXECUTA: generateArea.innerHTML = `<button disabled>...`
    → 🔴 Botão funcional é destruído
    → 🔴 Stub novo NÃO tem onclick, está disabled, e não responde a click
T5  Usuário tenta clicar → nada acontece
```

`has_atividades` significa "tem pelo menos uma atividade com CORREÇÃO concluída". Como a Lista0 tem 38 alunos com prova respondida mas sem correção concluída ainda (depois da limpeza dos docs gerados em Ciclo 2), o backend retorna `false` e a UI destrói o botão.

---

## Locais no código

### Render inicial (funcional) — 3 lugares idênticos

[prova-ia-v2/frontend/index_v2.html:9121](../../frontend/index_v2.html#L9121) — matéria:
```html
<div id="desempenho-generate-area-materia" class="desempenho-generate-area">
    <button class="btn btn-primary" onclick="openDesempenhoSettings('materia', '${materiaId}')">⚙️ Gerar Relatório</button>
</div>
```

[prova-ia-v2/frontend/index_v2.html:9211](../../frontend/index_v2.html#L9211) — turma:
```html
<div id="desempenho-generate-area-turma" class="desempenho-generate-area">
    <button class="btn btn-primary" onclick="openDesempenhoSettings('turma', '${turmaId}')">⚙️ Gerar Relatório</button>
</div>
```

[prova-ia-v2/frontend/index_v2.html:9401](../../frontend/index_v2.html#L9401) — tarefa:
```html
<div id="desempenho-generate-area-tarefa" class="desempenho-generate-area">
    <button class="btn btn-primary" onclick="openDesempenhoSettings('tarefa', '${atividadeId}')">⚙️ Gerar Relatório</button>
</div>
```

### Sobrescrita destrutiva (quebra)

[prova-ia-v2/frontend/index_v2.html:11959-11969](../../frontend/index_v2.html#L11959-L11969):
```js
// B-T3: Update generate button based on has_atividades
if (generateArea) {
    if (!hasAtividades) {
        generateArea.innerHTML = `
            <button class="btn btn-primary" disabled>▶️ Gerar Relatório</button>
            <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 4px;">
                Nenhuma atividade corrigida. Corrija atividades primeiro para gerar o relatório.
            </div>
        `;
    }
}
```

---

## Modal e seleção de etapas (problema secundário)

[prova-ia-v2/frontend/index_v2.html:5352-5373](../../frontend/index_v2.html#L5352-L5373) — modal `modal-desempenho-settings` tem `<div id="desempenho-etapas-tree">` que é populado por `prefetchDesempenhoEtapasState()` → `renderDesempenhoEtapasRow()` ([linha 12164](../../frontend/index_v2.html#L12164)).

Cada item gera um checkbox individual `.desempenho-etapa-check` com `data-aluno` e `data-stage`. Sem master toggle. Pro Otávio re-rodar tudo, ele teria que clicar 38 × 6 = 228 checkboxes individualmente.

---

## Fix proposto

### Fix 1: parar de destruir o botão funcional

Em [11959-11969](../../frontend/index_v2.html#L11959-L11969), trocar a sobrescrita por um banner ABAIXO do botão (sem tocar nele):

```js
if (generateArea && !hasAtividades) {
    // Não destruir o botão — adicionar aviso ao lado dele
    if (!generateArea.querySelector('.desempenho-no-atividades-warn')) {
        const warn = document.createElement('div');
        warn.className = 'desempenho-no-atividades-warn';
        warn.style.cssText = 'color: var(--text-muted); font-size: 0.8rem; margin-top: 4px;';
        warn.textContent = 'Nenhuma atividade corrigida ainda. Clicar "Gerar Relatório" vai rodar a pipeline inteira (extração → correção → relatório) antes do desempenho.';
        generateArea.appendChild(warn);
    }
}
```

Resultado: botão original com `onclick="openDesempenhoSettings(...)"` permanece, usuário pode clicar.

### Fix 2: master checkbox "Selecionar todas" no modal

Em `prefetchDesempenhoEtapasState()` ou no início de `renderDesempenhoEtapasRow()`, injetar uma linha-mestre antes do tree:

```html
<label class="desempenho-master-toggle">
    <input type="checkbox" id="desempenho-etapa-select-all" checked>
    <strong>Selecionar todas as etapas</strong>
    <span class="muted">— desmarque as que NÃO quer re-executar</span>
</label>
```

Com listener:
```js
document.getElementById('desempenho-etapa-select-all').addEventListener('change', (e) => {
    document.querySelectorAll('.desempenho-etapa-check').forEach(cb => {
        cb.checked = e.target.checked;
    });
});
```

Default `checked` → modal já abre com tudo selecionado. Otávio desmarca o que não quer e clica "Gerar Relatório".

---

## O que NÃO precisa mudar

- `executor._cascade_prereqs` ([prova-ia-v2/backend/executor.py:6299](../../backend/executor.py#L6299)) — já faz "rodar todos os alunos da turma com skip cache". Sem regressão.
- Endpoint `/api/executar/pipeline-desempenho-turma` ([prova-ia-v2/backend/routes_prompts.py:1301](../../backend/routes_prompts.py#L1301)) — funciona, dispara background task e retorna `task_id`.
- `force_reexec` default `False` — comportamento correto. Só re-executa explicitamente.
- Restauração do botão após sucesso ([prova-ia-v2/frontend/index_v2.html:12429-12431](../../frontend/index_v2.html#L12429-L12431)) — `_cleanupDesempenhoProgress` já restaura o botão com onclick correto.

---

## Verificação pós-fix

1. Carregar aba Desempenho da turma 2026-1 (Lista0)
2. Esperar a chamada `/desempenho/turma/...` retornar
3. Verificar que o botão **continua clicável** (não vira disabled)
4. Verificar que o aviso "Nenhuma atividade corrigida ainda..." aparece ABAIXO
5. Clicar no botão → modal abre
6. Verificar que master checkbox está marcado
7. Desmarcar uma etapa → confirmar que outras permanecem marcadas
8. Marcar master → todas voltam a ficar marcadas
9. Clicar Gerar Relatório → spinner inicia, task_id sai no polling
