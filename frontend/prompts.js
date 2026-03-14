/**
 * Prompts Page Module — NOVO CR
 *
 * Extracted from inline index_v2.html into a standalone script.
 * Follows the same pattern as chat_system.js:
 *   - Global functions (no ES modules)
 *   - State on window.promptsState
 *   - Relies on global helpers: api(), apiForm(), escapeHtml(), truncateText(),
 *     showToast(), isContentRequestActive()
 *
 * Plan: docs/PLAN_Prompts_Page_Rewrite.md
 */

// ============================================================
// STATE
// ============================================================

window.promptsState = {
    currentEtapa: null,
    currentPage: 1,
    perPage: 20,
    tabPages: {},       // { etapa_id: pageNum } — per-tab page state
    etapas: [],         // cached from /api/prompts/etapas
    materias: [],       // cached from /api/materias
    materiaMap: {},     // { id: nome }
    requestId: null,    // content-request guard
    promptsCache: {},   // { etapa_id: { prompts, total, page, per_page, total_pages } }
    knownEtapas: [      // canonical EtapaProcessamento values
        'extrair_questoes', 'extrair_gabarito', 'extrair_respostas',
        'corrigir', 'analisar_habilidades', 'gerar_relatorio',
        'chat_geral',
        'relatorio_desempenho_tarefa', 'relatorio_desempenho_turma',
        'relatorio_desempenho_materia'
    ]
};

// ============================================================
// MAIN ENTRY POINT
// ============================================================

async function initPromptsPage(requestId) {
    const state = window.promptsState;
    state.requestId = requestId;

    const contentEl = document.getElementById('content');
    contentEl.innerHTML = '<div class="loading-spinner" style="text-align:center;padding:40px;color:var(--text-muted)">Carregando prompts...</div>';

    try {
        const [etapasData, materiasData] = await Promise.all([
            api('/prompts/etapas'),
            api('/materias')
        ]);

        if (!isContentRequestActive(requestId, 'prompts')) return;

        state.etapas = etapasData.etapas || [];
        state.materias = materiasData.materias || [];
        state.materiaMap = state.materias.reduce((acc, m) => {
            acc[m.id] = m.nome;
            return acc;
        }, {});

        // Default to first tab
        if (!state.currentEtapa && state.etapas.length > 0) {
            state.currentEtapa = state.etapas[0].id;
        }

        renderPromptsPage();
        await loadPromptsForTab(state.currentEtapa);
    } catch (e) {
        console.error('Erro ao carregar prompts:', e);
        showToast('Erro ao carregar prompts', 'error');
    }
}

// ============================================================
// PAGE LAYOUT
// ============================================================

function renderPromptsPage() {
    const state = window.promptsState;
    const contentEl = document.getElementById('content');

    contentEl.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">
                Prompts
                <button class="section-help" onclick="toggleHelpPanel('prompts')" title="O que sao prompts?">?</button>
            </h1>
            <p class="page-subtitle">Gerencie os prompts de cada etapa do pipeline</p>
        </div>

        <div class="prompts-tabs-container">
            <div class="prompts-tabs" id="prompts-tabs"></div>
        </div>

        <div class="prompts-toolbar" id="prompts-toolbar"></div>

        <div id="prompts-cards-area">
            <div style="text-align:center;padding:40px;color:var(--text-muted)">Selecione uma etapa acima</div>
        </div>

        <div id="prompts-pagination-area"></div>

        <div id="prompts-form-area" style="display:none"></div>

        <div id="prompts-history-area" style="display:none"></div>
    `;

    renderStageTabs(state.etapas, state.currentEtapa);
}

// ============================================================
// F3-T1: STAGE TABS
// ============================================================

function renderStageTabs(etapas, activeEtapa) {
    const state = window.promptsState;
    const container = document.getElementById('prompts-tabs');
    if (!container) return;

    const tabsHtml = etapas.map(e => {
        const isActive = e.id === activeEtapa;
        const isUnknown = !state.knownEtapas.includes(e.id);
        const warningBadge = isUnknown ? ' <span class="prompts-tab-warning" title="Nova etapa — configuracao pode estar incompleta">!</span>' : '';
        return `<button class="prompts-tab${isActive ? ' tab-active' : ''}"
                    data-etapa="${escapeHtml(e.id)}"
                    onclick="onPromptsTabClick('${escapeHtml(e.id)}')"
                    title="${escapeHtml(e.descricao || e.nome)}">
                    ${escapeHtml(e.nome)}${warningBadge}
                </button>`;
    }).join('');

    container.innerHTML = tabsHtml;
}

async function onPromptsTabClick(etapaId) {
    const state = window.promptsState;
    state.currentEtapa = etapaId;
    state.currentPage = state.tabPages[etapaId] || 1;

    // Update tab active state
    document.querySelectorAll('.prompts-tab').forEach(tab => {
        tab.classList.toggle('tab-active', tab.dataset.etapa === etapaId);
    });

    await loadPromptsForTab(etapaId);
}

async function loadPromptsForTab(etapaId) {
    const state = window.promptsState;
    const cardsArea = document.getElementById('prompts-cards-area');
    if (!cardsArea) return;

    cardsArea.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted)">Carregando...</div>';

    try {
        const page = state.tabPages[etapaId] || 1;
        const data = await api(`/prompts?etapa=${encodeURIComponent(etapaId)}&page=${page}&per_page=${state.perPage}`);

        if (!isContentRequestActive(state.requestId, 'prompts')) return;

        state.promptsCache[etapaId] = data;
        renderToolbar(etapaId);
        renderPromptCards(data.prompts || [], etapaId);
        renderPagination(data.total || 0, data.page || 1, data.per_page || state.perPage, data.total_pages || 1);
    } catch (e) {
        console.error('Erro ao carregar prompts da etapa:', e);
        cardsArea.innerHTML = '<div style="text-align:center;padding:20px;color:var(--danger)">Erro ao carregar prompts</div>';
    }
}

// ============================================================
// TOOLBAR (create buttons)
// ============================================================

function renderToolbar(etapaId) {
    const toolbar = document.getElementById('prompts-toolbar');
    if (!toolbar) return;

    const etapaLabel = window.promptsState.etapas.find(e => e.id === etapaId)?.nome || etapaId;

    toolbar.innerHTML = `
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;">
            <button class="btn btn-primary" onclick="criarEmBranco()">+ Criar em branco</button>
            <span style="color:var(--text-muted);font-size:0.85rem;align-self:center;">Etapa: <strong>${escapeHtml(etapaLabel)}</strong></span>
        </div>
    `;
}

// ============================================================
// F4-T1: PROMPT CARDS + F6-T1: READ-ONLY DEFAULTS
// ============================================================

function renderPromptCards(prompts, etapaAtiva) {
    const state = window.promptsState;
    const cardsArea = document.getElementById('prompts-cards-area');
    if (!cardsArea) return;

    if (prompts.length === 0) {
        cardsArea.innerHTML = `
            <div class="card" style="text-align:center;padding:40px;">
                <p style="color:var(--text-muted);margin-bottom:12px;">Nenhum prompt encontrado para esta etapa.</p>
                <button class="btn btn-primary" onclick="criarEmBranco()">Criar primeiro prompt</button>
            </div>
        `;
        return;
    }

    const cardsHtml = prompts.map(p => {
        const isPadrao = p.is_padrao;
        const isAtivo = p.is_ativo !== false;
        const isGlobal = !p.materia_id;
        const materiaName = p.materia_id ? (state.materiaMap[p.materia_id] || p.materia_id) : null;

        // Badges
        const badges = [];
        if (isPadrao) badges.push('<span class="prompt-badge badge-padrao">Padrao</span>');
        else badges.push('<span class="prompt-badge badge-custom">Custom</span>');
        if (isAtivo) badges.push('<span class="prompt-badge badge-ativo">Ativo</span>');
        else badges.push('<span class="prompt-badge badge-inativo">Inativo</span>');
        if (isGlobal) badges.push('<span class="prompt-badge badge-global">Global</span>');
        else badges.push(`<span class="prompt-badge badge-materia">${escapeHtml(materiaName)}</span>`);

        // Actions differ for default vs custom
        let actionsHtml = '';
        if (isPadrao) {
            actionsHtml = `
                <div class="prompt-actions">
                    <button class="btn btn-sm" onclick="criarDoModelo('${escapeHtml(p.id)}')">Criar a partir do modelo</button>
                </div>
            `;
        } else {
            actionsHtml = `
                <div class="prompt-actions">
                    <button class="btn btn-sm" onclick="editarPrompt('${escapeHtml(p.id)}')">Editar</button>
                    <button class="btn btn-sm" onclick="showHistorico('${escapeHtml(p.id)}')">Historico</button>
                    <button class="btn btn-sm" onclick="criarDoModelo('${escapeHtml(p.id)}')">Duplicar</button>
                    <button class="btn btn-sm btn-danger" onclick="deletarPrompt('${escapeHtml(p.id)}', ${isPadrao})">Excluir</button>
                </div>
            `;
        }

        const lockIcon = isPadrao ? '<span class="prompt-lock" title="Prompt padrao — somente leitura">&#128274;</span> ' : '';
        const cardClass = isPadrao ? 'prompt-card is-padrao' : 'prompt-card';

        return `
            <div class="${cardClass}" data-prompt-id="${escapeHtml(p.id)}">
                <div class="prompt-card-header" onclick="togglePromptCard(this)">
                    <div class="prompt-card-title">
                        ${lockIcon}<span class="prompt-card-name">${escapeHtml(p.nome)}</span>
                    </div>
                    <div class="prompt-card-badges">${badges.join('')}</div>
                    <span class="prompt-card-chevron">&#9660;</span>
                </div>
                <div class="prompt-card-body" style="display:none">
                    ${p.descricao ? `<p class="prompt-descricao">${escapeHtml(p.descricao)}</p>` : ''}
                    ${p.texto_sistema ? `
                        <div class="prompt-section">
                            <label class="prompt-section-label">Prompt de Sistema</label>
                            <pre class="prompt-text">${escapeHtml(p.texto_sistema)}</pre>
                        </div>
                    ` : ''}
                    <div class="prompt-section">
                        <label class="prompt-section-label">Prompt do Usuario</label>
                        <pre class="prompt-text">${escapeHtml(p.texto)}</pre>
                    </div>
                    ${p.variaveis && p.variaveis.length > 0 ? `
                        <div class="prompt-section">
                            <label class="prompt-section-label">Variaveis</label>
                            <div class="prompt-vars">${p.variaveis.map(v => `<code>{{${escapeHtml(v)}}}</code>`).join(' ')}</div>
                        </div>
                    ` : ''}
                    <div class="prompt-meta">
                        <span>Versao ${p.versao || 1}</span>
                        ${p.atualizado_em ? `<span>Atualizado: ${new Date(p.atualizado_em).toLocaleDateString('pt-BR')}</span>` : ''}
                    </div>
                    ${actionsHtml}
                </div>
            </div>
        `;
    }).join('');

    cardsArea.innerHTML = cardsHtml;
}

function togglePromptCard(headerEl) {
    const body = headerEl.nextElementSibling;
    const chevron = headerEl.querySelector('.prompt-card-chevron');
    const isExpanded = body.style.display !== 'none';
    body.style.display = isExpanded ? 'none' : 'block';
    if (chevron) {
        chevron.innerHTML = isExpanded ? '&#9660;' : '&#9650;';
    }
}

// ============================================================
// F8-T1: PAGINATION UI
// ============================================================

function renderPagination(total, page, perPage, totalPages) {
    const paginationArea = document.getElementById('prompts-pagination-area');
    if (!paginationArea) return;

    if (totalPages <= 1) {
        paginationArea.innerHTML = '';
        return;
    }

    let pagesHtml = '';
    for (let i = 1; i <= totalPages; i++) {
        const activeClass = i === page ? ' pagination-active' : '';
        pagesHtml += `<button class="pagination-btn${activeClass}" onclick="goToPromptsPage(${i})">${i}</button>`;
    }

    paginationArea.innerHTML = `
        <div class="prompts-pagination">
            <button class="pagination-btn" onclick="goToPromptsPage(${page - 1})" ${page <= 1 ? 'disabled' : ''}>&#8592; Anterior</button>
            ${pagesHtml}
            <button class="pagination-btn" onclick="goToPromptsPage(${page + 1})" ${page >= totalPages ? 'disabled' : ''}>Proximo &#8594;</button>
            <span class="pagination-info">${total} prompt(s)</span>
        </div>
    `;
}

async function goToPromptsPage(page) {
    const state = window.promptsState;
    if (page < 1) return;
    state.currentPage = page;
    state.tabPages[state.currentEtapa] = page;
    await loadPromptsForTab(state.currentEtapa);
}

// ============================================================
// F5-T1: CREATE PROMPT FORM (template + blank)
// ============================================================

function criarEmBranco() {
    showCreateForm('blank', null);
}

async function criarDoModelo(promptId) {
    try {
        const data = await api(`/prompts/${encodeURIComponent(promptId)}`);
        showCreateForm('template', data.prompt || data);
    } catch (e) {
        showToast('Erro ao carregar prompt modelo', 'error');
    }
}

function showCreateForm(mode, templatePrompt) {
    const state = window.promptsState;
    const formArea = document.getElementById('prompts-form-area');
    if (!formArea) return;

    const etapaAtiva = state.currentEtapa || '';
    const nome = mode === 'template' && templatePrompt ? `${templatePrompt.nome} (copia)` : '';
    const textoSistema = mode === 'template' && templatePrompt ? (templatePrompt.texto_sistema || '') : '';
    const texto = mode === 'template' && templatePrompt ? (templatePrompt.texto || '') : '';
    const descricao = mode === 'template' && templatePrompt ? (templatePrompt.descricao || '') : '';
    const materiaId = mode === 'template' && templatePrompt ? (templatePrompt.materia_id || '') : '';
    const title = mode === 'template' ? 'Criar a partir do modelo' : 'Criar novo prompt';

    const materiasOptions = state.materias.map(m =>
        `<option value="${escapeHtml(m.id)}" ${m.id === materiaId ? 'selected' : ''}>${escapeHtml(m.nome)}</option>`
    ).join('');

    formArea.style.display = 'block';
    formArea.innerHTML = `
        <div class="card" style="margin-top:16px;">
            <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
                <h3 class="card-title">${escapeHtml(title)}</h3>
                <button class="btn btn-sm" onclick="hideCreateForm()">Cancelar</button>
            </div>
            <div class="form-group">
                <label class="form-label">Nome *</label>
                <input type="text" class="form-input" id="prompt-form-nome"
                    value="${escapeHtml(nome)}" placeholder="Ex: Correcao - Matematica">
            </div>
            <div class="form-group">
                <label class="form-label">Etapa</label>
                <select class="form-select" id="prompt-form-etapa">
                    ${state.etapas.map(e => `<option value="${escapeHtml(e.id)}" ${e.id === etapaAtiva ? 'selected' : ''}>${escapeHtml(e.nome)}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Materia (opcional)</label>
                <select class="form-select" id="prompt-form-materia">
                    <option value="">Global</option>
                    ${materiasOptions}
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Descricao</label>
                <input type="text" class="form-input" id="prompt-form-descricao"
                    value="${escapeHtml(descricao)}" placeholder="Descricao opcional">
            </div>
            <div class="form-group">
                <label class="form-label">Prompt de Sistema (opcional)</label>
                <textarea class="form-textarea" id="prompt-form-texto-sistema" rows="6"
                    placeholder="Instrucoes de sistema para o modelo...">${escapeHtml(textoSistema)}</textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Prompt do Usuario *</label>
                <textarea class="form-textarea" id="prompt-form-texto" rows="10"
                    placeholder="Digite o prompt do usuario aqui...">${escapeHtml(texto)}</textarea>
            </div>
            <div style="display:flex;gap:8px;">
                <button class="btn btn-primary" onclick="submitCreateForm()">Salvar Prompt</button>
                <button class="btn" onclick="hideCreateForm()">Cancelar</button>
            </div>
        </div>
    `;

    formArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function hideCreateForm() {
    const formArea = document.getElementById('prompts-form-area');
    if (formArea) {
        formArea.style.display = 'none';
        formArea.innerHTML = '';
    }
}

async function submitCreateForm() {
    const nome = document.getElementById('prompt-form-nome')?.value.trim();
    const etapa = document.getElementById('prompt-form-etapa')?.value;
    const materiaId = document.getElementById('prompt-form-materia')?.value;
    const descricao = document.getElementById('prompt-form-descricao')?.value.trim();
    const textoSistema = document.getElementById('prompt-form-texto-sistema')?.value.trim();
    const texto = document.getElementById('prompt-form-texto')?.value.trim();

    if (!nome || !texto) {
        showToast('Preencha nome e texto do prompt', 'error');
        return;
    }

    try {
        await api('/prompts', {
            method: 'POST',
            body: JSON.stringify({
                nome,
                etapa,
                texto,
                texto_sistema: textoSistema || null,
                descricao: descricao || null,
                materia_id: materiaId || null
            })
        });
        showToast('Prompt criado!', 'success');
        hideCreateForm();
        await loadPromptsForTab(window.promptsState.currentEtapa);
    } catch (e) {
        showToast('Erro ao criar prompt', 'error');
    }
}

// ============================================================
// F5-T2: INLINE EDIT FORM
// ============================================================

async function editarPrompt(promptId) {
    try {
        const data = await api(`/prompts/${encodeURIComponent(promptId)}`);
        const p = data.prompt || data;
        showEditForm(p);
    } catch (e) {
        showToast('Erro ao carregar prompt para edicao', 'error');
    }
}

function showEditForm(prompt) {
    const card = document.querySelector(`.prompt-card[data-prompt-id="${prompt.id}"]`);
    if (!card) return;

    const body = card.querySelector('.prompt-card-body');
    if (!body) return;

    body.style.display = 'block';
    body.innerHTML = `
        <div class="prompt-edit-form">
            <div class="form-group">
                <label class="form-label">Nome</label>
                <input type="text" class="form-input" id="edit-nome-${prompt.id}" value="${escapeHtml(prompt.nome)}">
            </div>
            <div class="form-group">
                <label class="form-label">Descricao</label>
                <input type="text" class="form-input" id="edit-descricao-${prompt.id}" value="${escapeHtml(prompt.descricao || '')}">
            </div>
            <div class="form-group">
                <label class="form-label">Prompt de Sistema</label>
                <textarea class="form-textarea" id="edit-texto-sistema-${prompt.id}" rows="6">${escapeHtml(prompt.texto_sistema || '')}</textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Prompt do Usuario</label>
                <textarea class="form-textarea" id="edit-texto-${prompt.id}" rows="10">${escapeHtml(prompt.texto || '')}</textarea>
            </div>
            <div style="display:flex;gap:8px;">
                <button class="btn btn-primary" onclick="submitEditForm('${escapeHtml(prompt.id)}')">Salvar</button>
                <button class="btn" onclick="cancelarEdicao()">Cancelar</button>
            </div>
        </div>
    `;
}

async function submitEditForm(promptId) {
    const nome = document.getElementById(`edit-nome-${promptId}`)?.value.trim();
    const descricao = document.getElementById(`edit-descricao-${promptId}`)?.value.trim();
    const textoSistema = document.getElementById(`edit-texto-sistema-${promptId}`)?.value.trim();
    const texto = document.getElementById(`edit-texto-${promptId}`)?.value.trim();

    if (!texto) {
        showToast('O texto do prompt nao pode estar vazio', 'error');
        return;
    }

    try {
        await api(`/prompts/${encodeURIComponent(promptId)}`, {
            method: 'PUT',
            body: JSON.stringify({
                nome: nome || null,
                texto,
                texto_sistema: textoSistema || null,
                descricao: descricao || null
            })
        });
        showToast('Prompt atualizado!', 'success');
        await loadPromptsForTab(window.promptsState.currentEtapa);
    } catch (e) {
        showToast('Erro ao atualizar prompt', 'error');
    }
}

function cancelarEdicao() {
    // Reload the current tab to restore card state
    loadPromptsForTab(window.promptsState.currentEtapa);
}

// ============================================================
// F5-T3: DELETE WITH CONFIRMATION
// ============================================================

async function deletarPrompt(promptId, isPadrao) {
    let msg = 'Tem certeza que deseja excluir este prompt?';
    if (isPadrao) {
        msg = 'Este prompt e o padrao para esta etapa. Ao exclui-lo, o sistema voltara ao padrao do sistema.\n\nDeseja continuar?';
    }

    if (!confirm(msg)) return;

    try {
        await api(`/prompts/${encodeURIComponent(promptId)}`, { method: 'DELETE' });
        showToast('Prompt excluido!', 'success');
        await loadPromptsForTab(window.promptsState.currentEtapa);
    } catch (e) {
        if (isPadrao) {
            showToast('Nao e possivel excluir o prompt padrao do sistema', 'error');
        } else {
            showToast('Erro ao excluir prompt', 'error');
        }
    }
}

// ============================================================
// F7-T1: VERSION HISTORY UI + REVERT
// ============================================================

async function showHistorico(promptId) {
    const historyArea = document.getElementById('prompts-history-area');
    if (!historyArea) return;

    try {
        const data = await api(`/prompts/${encodeURIComponent(promptId)}`);
        const prompt = data.prompt || data;
        const historico = data.historico || [];

        if (historico.length === 0) {
            historyArea.style.display = 'block';
            historyArea.innerHTML = `
                <div class="card" style="margin-top:16px;">
                    <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
                        <h3 class="card-title">Historico — ${escapeHtml(prompt.nome)}</h3>
                        <button class="btn btn-sm" onclick="hideHistorico()">Fechar</button>
                    </div>
                    <p style="color:var(--text-muted);padding:16px;">Nenhuma versao anterior encontrada.</p>
                </div>
            `;
            historyArea.scrollIntoView({ behavior: 'smooth' });
            return;
        }

        const rows = historico.map(h => `
            <div class="history-entry">
                <div class="history-meta">
                    <span class="history-version">v${h.versao}</span>
                    <span class="history-date">${h.modificado_em ? new Date(h.modificado_em).toLocaleString('pt-BR') : '—'}</span>
                    <span class="history-author">${escapeHtml(h.modificado_por || 'sistema')}</span>
                </div>
                <pre class="prompt-text history-text">${escapeHtml(truncateText(h.texto || '', 300))}</pre>
                <button class="btn btn-sm" onclick="reverterVersao('${escapeHtml(promptId)}', '${escapeHtml(h.texto || '')}')">Reverter para esta versao</button>
            </div>
        `).join('');

        historyArea.style.display = 'block';
        historyArea.innerHTML = `
            <div class="card" style="margin-top:16px;">
                <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
                    <h3 class="card-title">Historico — ${escapeHtml(prompt.nome)}</h3>
                    <button class="btn btn-sm" onclick="hideHistorico()">Fechar</button>
                </div>
                <div class="history-list">${rows}</div>
            </div>
        `;
        historyArea.scrollIntoView({ behavior: 'smooth' });
    } catch (e) {
        showToast('Erro ao carregar historico', 'error');
    }
}

async function reverterVersao(promptId, textoAntigo) {
    if (!confirm('Reverter para esta versao? A versao atual sera salva no historico.')) return;

    try {
        await api(`/prompts/${encodeURIComponent(promptId)}`, {
            method: 'PUT',
            body: JSON.stringify({ texto: textoAntigo })
        });
        showToast('Versao revertida!', 'success');
        hideHistorico();
        await loadPromptsForTab(window.promptsState.currentEtapa);
    } catch (e) {
        showToast('Erro ao reverter versao', 'error');
    }
}

function hideHistorico() {
    const historyArea = document.getElementById('prompts-history-area');
    if (historyArea) {
        historyArea.style.display = 'none';
        historyArea.innerHTML = '';
    }
}
