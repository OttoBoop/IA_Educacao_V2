// ============================================================
// CHAT SYSTEM - Prova AI
// Sistema de Chat com seleção de provider e contexto modular
// ============================================================

// Estado global do chat
window.chatState = {
    history: [],
    currentProvider: null,
    isLoading: false,
    
    // Sistema de contexto
    context: {
        mode: 'filtered', // 'all', 'filtered', 'manual'
        filters: {
            materias: null,
            turmas: null,
            atividades: null,
            alunos: null,
            tipos: null
        },
        hideJsonFiles: false, // Ocultar arquivos JSON da lista (padrão: mostrar todos)
        excludedDocs: new Set(),
        includedDocs: new Set(),
        availableDocs: [],

        // Cache para filtros dependentes
        cache: {
            turmasDisponiveis: [],
            atividadesDisponiveis: [],
            alunosDisponiveis: []
        },

        // Sistema de Override Manual para documentos
        manualOverrides: {
            included: new Set(),  // Docs adicionados manualmente (laranja) - nao batem com filtros
            excluded: new Set()   // Docs removidos manualmente (azul claro) - batem com filtros
        },

        // Cache de intersecoes para indicadores visuais
        intersectionCache: {
            materias: {},    // { materia_id: { total, comDocs, semDocs } }
            turmas: {},      // { turma_id: { total, comDocs, semDocs } }
            atividades: {}   // { atividade_id: { total, comDocs, semDocs } }
        }
    }
};

// Labels para tipos de documento
const TIPO_DOC_LABELS = {
    'enunciado': '📄 Enunciado',
    'gabarito': '✅ Gabarito',
    'criterios_correcao': '📋 Critérios',
    'prova_respondida': '📝 Prova do Aluno',
    'extracao_questoes': '🔍 Extração Questões',
    'extracao_gabarito': '🔍 Extração Gabarito',
    'extracao_respostas': '🔍 Extração Respostas',
    'correcao': '✏️ Correção',
    'analise_habilidades': '📊 Análise',
    'relatorio_final': '📑 Relatório'
};

// ============================================================
// FUNÇÃO PRINCIPAL: showChat
// ============================================================
async function showChat() {
    currentView = 'chat';
    setBreadcrumb([
        {nome: 'Início', onclick: 'showDashboard()'},
        {nome: 'Chat com IA', onclick: 'showChat()'}
    ]);

    // Carregar modelos e dados iniciais em paralelo
    const [modelsData, materiasData, alunosData] = await Promise.allSettled([
        api('/settings/models').catch(() => ({ models: [] })),
        api('/materias').catch(() => ({ materias: [] })),
        api('/alunos').catch(() => ({ alunos: [] }))
    ]);

    const models = modelsData.status === 'fulfilled' ? modelsData.value : { models: [] };
    const materias = materiasData.status === 'fulfilled' ? materiasData.value.materias : [];
    const alunos = alunosData.status === 'fulfilled' ? alunosData.value.alunos : [];

    // Guardar no cache
    window._chatMaterias = materias;
    window._chatAlunos = alunos;
    window._chatModels = models.models || [];
    window._chatDefaultModel = models.models?.find(m => m.is_default)?.id || models.models?.[0]?.id;

    // Renderizar a view do chat
    document.getElementById('content').innerHTML = renderChatView(models, materias, alunos);

    // Setup event listeners
    setupChatEventListeners();

    // Carregar documentos disponíveis
    await loadAvailableDocuments();
}

// ============================================================
// RENDERIZAÇÃO DA VIEW
// ============================================================
function renderChatView(models, materias, alunos) {
    const modelOptions = renderModelOptions(models);
    const hasModels = models.models && models.models.length > 0;
    
    return `
        <div class="chat-layout">
            <!-- Painel de Contexto (Lateral) -->
            <div class="chat-context-panel" id="context-panel">
                <div class="context-header">
                    <h3>📚 Contexto</h3>
                    <button class="btn btn-sm" onclick="toggleContextPanel()" title="Minimizar">
                        <span id="context-toggle-icon">◀</span>
                    </button>
                </div>
                
                <div class="context-body" id="context-body">
                    <!-- Seletor de Modo -->
                    <div class="context-section">
                        <label class="form-label">Modo de Seleção</label>
                        <div class="context-mode-buttons">
                            <button class="mode-btn" data-mode="all" onclick="setContextMode('all')">
                                ✅ Todos
                            </button>
                            <button class="mode-btn active" data-mode="filtered" onclick="setContextMode('filtered')">
                                🔍 Filtrar
                            </button>
                            <button class="mode-btn" data-mode="manual" onclick="setContextMode('manual')">
                                ✋ Manual
                            </button>
                        </div>
                    </div>
                    
                    <!-- Filtros (aparecem no modo 'filtered') -->
                    <div class="context-filters" id="context-filters" style="display: block;">
                        <!-- Filtro por Alunos -->
                        <div class="filter-group">
                            <label class="form-label">👤 Alunos</label>
                            <div id="filter-alunos-container"></div>
                            <div class="filter-chips" id="chips-alunos"></div>
                        </div>

                        <!-- Filtro por Matéria -->
                        <div class="filter-group">
                            <label class="form-label">📚 Matérias</label>
                            <div id="filter-materias-container"></div>
                            <div class="filter-chips" id="chips-materias"></div>
                        </div>

                        <!-- Filtro por Turma -->
                        <div class="filter-group">
                            <label class="form-label">👥 Turmas</label>
                            <div id="filter-turmas-container"></div>
                            <div class="filter-chips" id="chips-turmas"></div>
                        </div>

                        <!-- Filtro por Atividade -->
                        <div class="filter-group">
                            <label class="form-label">📝 Atividades</label>
                            <div id="filter-atividades-container"></div>
                            <div class="filter-chips" id="chips-atividades"></div>
                        </div>

                        <!-- Filtro por Tipo de Documento -->
                        <div class="filter-group">
                            <label class="form-label">📄 Tipos de Documento</label>
                            <div id="filter-tipos-container"></div>
                            <div class="filter-chips" id="chips-tipos"></div>
                        </div>

                        <!-- Toggle para ocultar arquivos JSON -->
                        <div class="filter-group" style="border-top: 1px solid var(--border); padding-top: 10px; margin-top: 10px;">
                            <label class="form-label" style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="hide-json-toggle" onchange="toggleHideJson()" style="width: 16px; height: 16px;">
                                <span>🔒 Ocultar arquivos JSON</span>
                            </label>
                            <small style="color: var(--text-muted); font-size: 11px;">
                                JSONs são dados brutos. PDFs/CSVs são mais visuais.
                            </small>
                        </div>

                        <button class="btn btn-sm" onclick="clearAllFilters()" style="width: 100%; margin-top: 8px;">
                            🗑️ Limpar Filtros
                        </button>
                    </div>
                    
                    <!-- Lista de Documentos Selecionados -->
                    <div class="context-section">
                        <div class="docs-header">
                            <label class="form-label">Documentos: <strong id="docs-count">0</strong> / <span id="docs-total">0</span></label>
                            <button class="btn btn-sm" onclick="toggleAllDocs()" title="Inverter seleção">↔️</button>
                        </div>
                        <div class="docs-list" id="context-docs-list">
                            <div class="empty-state-mini">
                                <span>Carregando...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Área Principal do Chat -->
            <div class="chat-main">
                <!-- Header do Chat -->
                <div class="chat-header">
                    <div class="chat-header-left">
                        <h2>💬 Chat com IA</h2>
                    </div>
                    <div class="chat-header-right">
                        <label class="form-label-inline">Modelo:</label>
                        ${hasModels ? `
                            <select class="form-select" id="chat-model-select" style="min-width: 200px;">
                                ${modelOptions}
                            </select>
                        ` : `
                            <div class="provider-warning">
                                ⚠️ <a href="#" onclick="openModal('modal-settings'); showSettingsTab('models'); return false;">Configure um modelo</a>
                            </div>
                        `}
                        <button class="btn btn-sm" onclick="clearChatHistory()" title="Limpar conversa">
                            🗑️
                        </button>
                    </div>
                </div>
                
                <!-- Mensagens -->
                <div class="chat-messages" id="chat-messages">
                    <div class="message assistant">
                        <div class="message-content">
                            Olá! Sou seu assistente para análise e correção de provas. 
                            ${hasModels ? `
                                <br><br>
                                📚 <strong>Contexto:</strong> Você pode selecionar documentos no painel à esquerda para que eu tenha acesso às informações relevantes.
                                <br><br>
                                Como posso ajudar?
                            ` : `
                                <br><br>
                                ⚠️ <strong>Atenção:</strong> Nenhum modelo de IA está configurado.
                                <a href="#" onclick="openModal('modal-settings'); showSettingsTab('models'); return false;">Clique aqui</a> para adicionar um modelo.
                            `}
                        </div>
                    </div>
                </div>
                
                <!-- Input -->
                <div class="chat-input-area">
                    <div class="chat-input-row">
                        <textarea 
                            class="chat-input" 
                            id="chat-input" 
                            placeholder="${hasModels ? 'Digite sua mensagem...' : 'Configure um modelo primeiro...'}"
                            rows="1"
                            ${!hasModels ? 'disabled' : ''}
                        ></textarea>
                        <button class="btn btn-primary" id="chat-send-btn" onclick="sendChatMessage()" ${!hasModels ? 'disabled' : ''}>
                            Enviar
                        </button>
                    </div>
                    <div class="chat-input-info">
                        <span id="context-status">📚 Contexto: Todos os documentos</span>
                        <span id="provider-status"></span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderModelOptions(models) {
    if (!models.models || models.models.length === 0) {
        return '<option value="">Nenhum modelo configurado</option>';
    }

    return models.models.map(m => `
        <option value="${m.id}" ${m.is_default ? 'selected' : ''}>
            ${escapeHtml(m.nome)} (${m.modelo})
        </option>
    `).join('');
}

// ============================================================
// SETUP DE EVENT LISTENERS
// ============================================================
function setupChatEventListeners() {
    const input = document.getElementById('chat-input');
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });

        // Auto-resize
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 200) + 'px';
        });
    }

    // Inicializar dropdowns de filtro melhorados
    initFilterDropdowns();
}

/**
 * Inicializa os dropdowns customizados de filtro
 */
function initFilterDropdowns() {
    // Alunos
    const alunos = (window._chatAlunos || []).map(a => ({ id: a.id, nome: a.nome }));
    createFilterDropdown('filter-alunos-container', alunos, (selected) => {
        window.chatState.context.filters.alunos = selected.length > 0 ? selected : null;
        updateFilterChips('alunos', selected, window._chatAlunos, 'nome');
        window.chatState.context.intersectionCache = calcularIntersecoes(selected);
        atualizarIndicadoresVisuais();
        updateDocumentsList();
    }, { placeholder: 'Selecionar alunos...', searchable: true });

    // Matérias
    const materias = (window._chatMaterias || []).map(m => ({ id: m.id, nome: m.nome }));
    createFilterDropdown('filter-materias-container', materias, async (selected) => {
        window.chatState.context.filters.materias = selected.length > 0 ? selected : null;
        updateFilterChips('materias', selected, window._chatMaterias, 'nome');
        await loadTurmasForMateriasDropdown(selected);
        clearDependentFilters(['turmas', 'atividades']);
        updateDocumentsList();
    }, { placeholder: 'Selecionar matérias...', searchable: true });

    // Turmas (inicialmente vazio)
    createFilterDropdown('filter-turmas-container', [], () => {}, {
        placeholder: 'Selecione matéria(s) primeiro',
        emptyText: 'Selecione matéria(s) primeiro'
    });

    // Atividades (inicialmente vazio)
    createFilterDropdown('filter-atividades-container', [], () => {}, {
        placeholder: 'Selecione turma(s) primeiro',
        emptyText: 'Selecione turma(s) primeiro'
    });

    // Tipos de documento
    const tipos = Object.entries(TIPO_DOC_LABELS).map(([k, v]) => ({ id: k, nome: v }));
    createFilterDropdown('filter-tipos-container', tipos, (selected) => {
        window.chatState.context.filters.tipos = selected.length > 0 ? selected : null;
        const tiposList = selected.map(t => ({ id: t, nome: TIPO_DOC_LABELS[t] || t }));
        updateFilterChips('tipos', selected, tiposList, 'nome');
        updateDocumentsList();
    }, { placeholder: 'Selecionar tipos...' });
}

/**
 * Atualiza dropdown de turmas baseado nas matérias selecionadas
 */
async function loadTurmasForMateriasDropdown(materiaIds) {
    if (!materiaIds || materiaIds.length === 0) {
        createFilterDropdown('filter-turmas-container', [], () => {}, {
            placeholder: 'Selecione matéria(s) primeiro',
            emptyText: 'Selecione matéria(s) primeiro'
        });
        window.chatState.context.cache.turmasDisponiveis = [];
        return;
    }

    try {
        const turmasPromises = materiaIds.map(id => api(`/materias/${id}/turmas`).catch(() => ({ turmas: [] })));
        const results = await Promise.all(turmasPromises);
        const todasTurmas = results.flatMap(r => r.turmas || []);

        // Remover duplicadas
        const turmasUnicas = [];
        const ids = new Set();
        for (const t of todasTurmas) {
            if (!ids.has(t.id)) {
                ids.add(t.id);
                turmasUnicas.push(t);
            }
        }

        window.chatState.context.cache.turmasDisponiveis = turmasUnicas;

        const turmasItems = turmasUnicas.map(t => ({ id: t.id, nome: t.nome }));
        createFilterDropdown('filter-turmas-container', turmasItems, async (selected) => {
            window.chatState.context.filters.turmas = selected.length > 0 ? selected : null;
            updateFilterChips('turmas', selected, window.chatState.context.cache.turmasDisponiveis, 'nome');
            await loadAtividadesForTurmasDropdown(selected);
            clearDependentFilters(['atividades']);
            updateDocumentsList();
        }, { placeholder: 'Selecionar turmas...', searchable: turmasUnicas.length > 5 });

    } catch (e) {
        console.error('Erro ao carregar turmas:', e);
    }
}

/**
 * Atualiza dropdown de atividades baseado nas turmas selecionadas
 */
async function loadAtividadesForTurmasDropdown(turmaIds) {
    if (!turmaIds || turmaIds.length === 0) {
        createFilterDropdown('filter-atividades-container', [], () => {}, {
            placeholder: 'Selecione turma(s) primeiro',
            emptyText: 'Selecione turma(s) primeiro'
        });
        window.chatState.context.cache.atividadesDisponiveis = [];
        return;
    }

    try {
        const atividadesPromises = turmaIds.map(id => api(`/turmas/${id}/atividades`).catch(() => ({ atividades: [] })));
        const results = await Promise.all(atividadesPromises);
        const todasAtividades = results.flatMap(r => r.atividades || []);

        // Remover duplicadas
        const atividadesUnicas = [];
        const ids = new Set();
        for (const a of todasAtividades) {
            if (!ids.has(a.id)) {
                ids.add(a.id);
                atividadesUnicas.push(a);
            }
        }

        window.chatState.context.cache.atividadesDisponiveis = atividadesUnicas;

        const atividadesItems = atividadesUnicas.map(a => ({ id: a.id, nome: a.nome }));
        createFilterDropdown('filter-atividades-container', atividadesItems, (selected) => {
            window.chatState.context.filters.atividades = selected.length > 0 ? selected : null;
            updateFilterChips('atividades', selected, window.chatState.context.cache.atividadesDisponiveis, 'nome');
            updateDocumentsList();
        }, { placeholder: 'Selecionar atividades...', searchable: atividadesUnicas.length > 5 });

    } catch (e) {
        console.error('Erro ao carregar atividades:', e);
    }
}

// ============================================================
// ENVIO DE MENSAGENS
// ============================================================
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message || window.chatState.isLoading) return;

    const modelSelect = document.getElementById('chat-model-select');
    const modelId = modelSelect?.value;

    if (!modelId) {
        showToast('Selecione um modelo de IA', 'error');
        return;
    }
    
    // Adicionar mensagem do usuário
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.innerHTML += `
        <div class="message user">
            <div class="message-content">${escapeHtml(message)}</div>
        </div>
    `;
    
    input.value = '';
    input.style.height = 'auto';
    window.chatState.history.push({ role: 'user', content: message });
    
    // Mostrar indicador de loading
    window.chatState.isLoading = true;
    const loadingId = 'loading-' + Date.now();
    messagesDiv.innerHTML += `
        <div class="message assistant loading" id="${loadingId}">
            <div class="message-content">
                <span class="typing-indicator">●●●</span> Pensando...
            </div>
        </div>
    `;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    // Preparar documentos de contexto
    const contextDocs = getSelectedDocumentIds();
    
    try {
        const response = await api('/chat', {
            method: 'POST',
            body: JSON.stringify({
                messages: window.chatState.history,
                model_id: modelId,
                context_docs: contextDocs.length > 0 ? contextDocs : null
            })
        });
        
        // Remover loading
        document.getElementById(loadingId)?.remove();
        
        // Adicionar resposta
        const formattedResponse = formatChatMessage(response.response);
        const modelInfo = response.model_name || response.model || response.provider || 'IA';
        messagesDiv.innerHTML += `
            <div class="message assistant">
                <div class="message-content">${formattedResponse}</div>
                <div class="message-meta">
                    ${modelInfo} • ${response.tokens_used || '?'} tokens • ${response.latency_ms || '?'}ms
                </div>
            </div>
        `;
        
        // Strip binary document blocks before storing in history to avoid token overflow
        const cleanContent = response.response.replace(
            /```documento-binario:[^\n]+\n[\s\S]*?```/g,
            '[Arquivo binário gerado - ver acima]'
        );
        window.chatState.history.push({ role: 'assistant', content: cleanContent });
        
    } catch (error) {
        document.getElementById(loadingId)?.remove();
        messagesDiv.innerHTML += `
            <div class="message assistant error">
                <div class="message-content">
                    ❌ Erro ao enviar mensagem: ${error.message || 'Erro desconhecido'}
                </div>
            </div>
        `;
    }
    
    window.chatState.isLoading = false;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function formatChatMessage(text) {
    if (!text) return '';

    // DEBUG: Ver o texto raw
    console.log('formatChatMessage input:', text.substring(0, 500));

    // 1. PRIMEIRO: Detectar blocos de documento (ANTES dos blocos de código!)
    // DEPRECATED: AI should use python-exec: blocks instead of documento/document: blocks
    // This is kept for backward compatibility only
    const documentBlocks = [];
    // Match both "documento:" (Portuguese) and "document:" (English)
    const docRegex = /```\s*documen(?:to|t)\s*:\s*([^\n\r]+)[\r\n]+([\s\S]*?)```/gi;
    text = text.replace(docRegex, (match, titulo, conteudo) => {
        console.warn('DEPRECATED: documento: block detected. AI should use python-exec: instead for real files.');
        console.log('Documento encontrado!', { titulo, conteudo: conteudo.substring(0, 100) });
        documentBlocks.push({ titulo: titulo.trim(), conteudo: conteudo.trim() });
        return `@@DOCBLOCK${documentBlocks.length - 1}@@`;
    });

    console.log('Documentos encontrados:', documentBlocks.length);

    // 1.5. Detectar blocos de documento BINARIO (gerados por code execution)
    // Formato: ```documento-binario:nome.xlsx
    //          type=mime/type
    //          size=1234
    //          data=base64...
    //          ```
    const binaryDocBlocks = [];
    const binaryDocRegex = /```\s*documento-binario\s*:\s*([^\n\r]+)[\r\n]+([\s\S]*?)```/gi;
    text = text.replace(binaryDocRegex, (match, filename, metadata) => {
        console.log('Documento binário encontrado!', { filename });

        // Parse metadata
        const typeMatch = metadata.match(/type=([^\n\r]+)/);
        const sizeMatch = metadata.match(/size=(\d+)/);
        // Fix: Use regex that captures everything after "data=" to handle large base64 strings
        const dataMatch = metadata.match(/data=([\s\S]+)$/);

        const mimeType = typeMatch ? typeMatch[1].trim() : 'application/octet-stream';
        const size = sizeMatch ? parseInt(sizeMatch[1]) : 0;
        // Trim and remove any trailing whitespace/newlines from base64 data
        const base64Data = dataMatch ? dataMatch[1].trim().replace(/[\s\r\n]+/g, '') : '';

        binaryDocBlocks.push({
            filename: filename.trim(),
            mimeType: mimeType,
            size: size,
            data: base64Data
        });
        return `@@BINDOCBLOCK${binaryDocBlocks.length - 1}@@`;
    });

    console.log('Documentos binários encontrados:', binaryDocBlocks.length);

    // 2. Proteger blocos de código normais (depois de extrair documentos)
    const codeBlocks = [];
    text = text.replace(/```(\w*)[\r\n]+([\s\S]*?)```/g, (match, lang, code) => {
        codeBlocks.push({ lang, code });
        return `@@CODEBLOCK${codeBlocks.length - 1}@@`;
    });

    // 3. Tabelas markdown (processar antes de outras transformações)
    // Armazenar tabelas para download
    const tableBlocks = [];
    text = text.replace(/^\|(.+)\|\s*\n\|[-:\s|]+\|\s*\n((?:\|.+\|\s*\n?)+)/gm, (match, header, rows) => {
        const headers = header.split('|').map(h => h.trim()).filter(Boolean);
        const bodyRows = rows.trim().split('\n').map(row =>
            row.split('|').map(c => c.trim()).filter(Boolean)
        );

        // Guardar markdown original da tabela para download
        tableBlocks.push(match);

        let table = `<div class="table-container" data-table-id="${tableBlocks.length - 1}">`;
        table += '<table class="md-table"><thead><tr>';
        headers.forEach(h => table += `<th>${h}</th>`);
        table += '</tr></thead><tbody>';
        bodyRows.forEach(row => {
            table += '<tr>';
            row.forEach(cell => table += `<td>${cell}</td>`);
            table += '</tr>';
        });
        table += '</tbody></table>';
        table += `<div class="table-download-options">
            <span class="table-download-label">Baixar como:</span>
            <button class="btn btn-sm table-download-btn" onclick="baixarTabelaComo(${tableBlocks.length - 1}, 'csv')">CSV</button>
            <button class="btn btn-sm table-download-btn" onclick="baixarTabelaComo(${tableBlocks.length - 1}, 'md')">Markdown</button>
        </div>`;
        table += '</div>';
        return table;
    });

    // Armazenar tabelas no window para acesso posterior
    if (tableBlocks.length > 0) {
        window._tableContents = window._tableContents || {};
        tableBlocks.forEach((tbl, i) => {
            window._tableContents[i] = tbl;
        });
    }

    // 4. Títulos (h1-h6) - processar do maior para o menor
    text = text.replace(/^######\s+(.+)$/gm, '<h6 class="md-h6">$1</h6>');
    text = text.replace(/^#####\s+(.+)$/gm, '<h5 class="md-h5">$1</h5>');
    text = text.replace(/^####\s+(.+)$/gm, '<h4 class="md-h4">$1</h4>');
    text = text.replace(/^###\s+(.+)$/gm, '<h3 class="md-h3">$1</h3>');
    text = text.replace(/^##\s+(.+)$/gm, '<h2 class="md-h2">$1</h2>');
    text = text.replace(/^#\s+(.+)$/gm, '<h1 class="md-h1">$1</h1>');

    // 5. Linha horizontal
    text = text.replace(/^---+$/gm, '<hr class="md-hr">');

    // 6. Blockquotes (linhas começando com >)
    text = text.replace(/^>\s+(.+)$/gm, '<blockquote class="md-quote">$1</blockquote>');
    // Juntar blockquotes consecutivos
    text = text.replace(/<\/blockquote>\s*<blockquote class="md-quote">/g, '<br>');

    // 7. Listas não ordenadas (- ou *)
    text = text.replace(/^[\*\-]\s+(.+)$/gm, '<li class="md-li">$1</li>');
    // Agrupar <li> consecutivos em <ul>
    text = text.replace(/(<li class="md-li">.*<\/li>\n?)+/g, '<ul class="md-ul">$&</ul>');

    // 8. Listas ordenadas (1. 2. 3.)
    text = text.replace(/^\d+\.\s+(.+)$/gm, '<li class="md-oli">$1</li>');
    // Agrupar em <ol>
    text = text.replace(/(<li class="md-oli">.*<\/li>\n?)+/g, '<ol class="md-ol">$&</ol>');

    // 9. Links [texto](url)
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="md-link">$1</a>');

    // 10. Negrito e itálico
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    text = text.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    text = text.replace(/_([^_]+)_/g, '<em>$1</em>');

    // 11. Código inline
    text = text.replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>');

    // 12. Quebras de linha (mas não dentro de elementos block)
    text = text.replace(/\n(?!<)/g, '<br>');
    // Limpar <br> extras após elementos block
    text = text.replace(/(<\/h[1-6]>|<\/ul>|<\/ol>|<\/table>|<\/blockquote>|<hr[^>]*>)<br>/g, '$1');

    // 13. Restaurar blocos de código
    codeBlocks.forEach((block, i) => {
        const escapedCode = block.code
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        text = text.replace(
            `@@CODEBLOCK${i}@@`,
            `<pre class="md-pre"><code class="language-${block.lang}">${escapedCode}</code></pre>`
        );
    });

    // 14. Restaurar blocos de documento (com botao especial)
    documentBlocks.forEach((block, i) => {
        const docId = `doc_${Date.now()}_${i}`;
        // Armazenar o conteudo no window para acesso posterior
        window._documentContents = window._documentContents || {};
        window._documentContents[docId] = block;

        text = text.replace(
            `@@DOCBLOCK${i}@@`,
            `<div class="document-block">
                <div class="document-block-header">
                    <span class="document-icon">📄</span>
                    <span class="document-title">${escapeHtml(block.titulo)}</span>
                </div>
                <div class="document-block-buttons">
                    <button class="btn btn-primary document-open-btn" onclick="abrirDocumentoGerado('${docId}')">
                        Abrir
                    </button>
                    <button class="btn btn-secondary document-download-btn" onclick="baixarDocumentoGerado('${docId}')">
                        Baixar
                    </button>
                </div>
            </div>`
        );
    });

    // 15. Restaurar blocos de documento BINARIO (arquivos gerados por code execution)
    binaryDocBlocks.forEach((block, i) => {
        const docId = `bindoc_${Date.now()}_${i}`;
        // Armazenar os dados binários no window para acesso posterior
        window._binaryDocuments = window._binaryDocuments || {};
        window._binaryDocuments[docId] = block;

        const sizeKB = Math.round(block.size / 1024 * 10) / 10;
        const icon = getFileIcon(block.filename);

        text = text.replace(
            `@@BINDOCBLOCK${i}@@`,
            `<div class="document-block binary-document">
                <div class="document-block-header">
                    <span class="document-icon">${icon}</span>
                    <span class="document-title">${escapeHtml(block.filename)}</span>
                    <span class="document-size">(${sizeKB} KB)</span>
                </div>
                <div class="document-block-buttons">
                    <button class="btn btn-primary document-download-btn" onclick="baixarDocumentoBinario('${docId}')">
                        Baixar
                    </button>
                </div>
            </div>`
        );
    });

    return text;
}

/**
 * Retorna o ícone apropriado para o tipo de arquivo
 */
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'xlsx': '📊', 'xls': '📊',
        'docx': '📝', 'doc': '📝',
        'pdf': '📕',
        'pptx': '📽️', 'ppt': '📽️',
        'csv': '📋',
        'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'gif': '🖼️',
        'json': '📦',
        'txt': '📄', 'md': '📄'
    };
    return icons[ext] || '📄';
}

/**
 * Baixa um documento binário gerado por code execution
 * @param {string} docId - ID do documento armazenado em window._binaryDocuments
 */
function baixarDocumentoBinario(docId) {
    const docData = window._binaryDocuments?.[docId];
    if (!docData) {
        console.error('Documento binário não encontrado:', docId);
        alert('Erro: Documento não encontrado');
        return;
    }

    try {
        // Decode base64 and create blob
        const binaryString = atob(docData.data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        const blob = new Blob([bytes], { type: docData.mimeType });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = docData.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log(`Documento binário baixado: ${docData.filename}`);
    } catch (error) {
        console.error('Erro ao baixar documento binário:', error);
        alert('Erro ao baixar documento: ' + error.message);
    }
}

function clearChatHistory() {
    if (!confirm('Limpar todo o histórico da conversa?')) return;
    window.chatState.history = [];
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.innerHTML = `
        <div class="message assistant">
            <div class="message-content">
                Conversa limpa! Como posso ajudar?
            </div>
        </div>
    `;
}

// ============================================================
// SISTEMA DE DOCUMENTOS GERADOS
// ============================================================

/**
 * Abre um documento gerado pela IA em uma nova aba formatada para impressão
 * @param {string} docId - ID do documento armazenado em window._documentContents
 */
function abrirDocumentoGerado(docId) {
    const docData = window._documentContents?.[docId];
    if (!docData) {
        console.error('Documento não encontrado:', docId);
        alert('Erro: Documento não encontrado');
        return;
    }

    // Converter markdown para HTML
    const htmlContent = convertMarkdownToHtml(docData.conteudo);

    // Criar HTML completo para a nova janela
    const htmlCompleto = `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${escapeHtml(docData.titulo)} - Prova AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f9fafb;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px 50px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #3b82f6;
        }

        .header h1 {
            color: #1e40af;
            font-size: 1.8rem;
            margin-bottom: 8px;
        }

        .header .date {
            color: #6b7280;
            font-size: 0.9rem;
        }

        .content {
            margin-bottom: 30px;
        }

        .content h1 {
            font-size: 1.6rem;
            color: #1e40af;
            margin: 24px 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #3b82f6;
        }

        .content h2 {
            font-size: 1.3rem;
            color: #1e3a8a;
            margin: 20px 0 12px 0;
        }

        .content h3 {
            font-size: 1.1rem;
            color: #1e40af;
            margin: 16px 0 10px 0;
        }

        .content p {
            margin: 10px 0;
        }

        .content ul, .content ol {
            margin: 12px 0;
            padding-left: 28px;
        }

        .content li {
            margin: 6px 0;
        }

        .content table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }

        .content th, .content td {
            border: 1px solid #d1d5db;
            padding: 10px 14px;
            text-align: left;
        }

        .content th {
            background: #f3f4f6;
            font-weight: 600;
        }

        .content tr:nth-child(even) {
            background: #f9fafb;
        }

        .content blockquote {
            border-left: 4px solid #3b82f6;
            padding: 12px 20px;
            margin: 16px 0;
            background: #eff6ff;
            color: #1e40af;
            font-style: italic;
        }

        .content hr {
            border: none;
            border-top: 1px solid #e5e7eb;
            margin: 24px 0;
        }

        .content code {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
        }

        .content pre {
            background: #1f2937;
            color: #f9fafb;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 16px 0;
        }

        .content pre code {
            background: none;
            padding: 0;
            color: inherit;
        }

        .content strong {
            font-weight: 600;
        }

        .footer {
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 0.85rem;
        }

        .print-bar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #1e40af;
            color: white;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1000;
        }

        .print-bar button {
            background: white;
            color: #1e40af;
            border: none;
            padding: 8px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
        }

        .print-bar button:hover {
            background: #f3f4f6;
        }

        body {
            padding-top: 70px;
        }

        /* Estilos para impressão */
        @media print {
            .print-bar {
                display: none !important;
            }

            body {
                padding: 0;
                background: white;
            }

            .container {
                box-shadow: none;
                padding: 20px;
                max-width: 100%;
            }

            @page {
                margin: 2cm;
            }
        }
    </style>
</head>
<body>
    <div class="print-bar">
        <span>Documento: ${escapeHtml(docData.titulo)}</span>
        <button onclick="window.print()">Imprimir / Salvar PDF</button>
    </div>

    <div class="container">
        <div class="header">
            <h1>${escapeHtml(docData.titulo)}</h1>
            <div class="date">Gerado em ${new Date().toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: 'long',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            })}</div>
        </div>

        <div class="content">
            ${htmlContent}
        </div>

        <div class="footer">
            Documento gerado por Prova AI
        </div>
    </div>
</body>
</html>
    `;

    // Abrir em nova aba
    const novaJanela = window.open('', '_blank');
    if (novaJanela) {
        novaJanela.document.write(htmlCompleto);
        novaJanela.document.close();
    } else {
        alert('Popup bloqueado! Por favor, permita popups para este site.');
    }
}


/**
 * Baixa um documento gerado pela IA
 * @param {string} docId - ID do documento armazenado em window._documentContents
 */
function baixarDocumentoGerado(docId) {
    const docData = window._documentContents?.[docId];
    if (!docData) {
        console.error('Documento nao encontrado:', docId);
        alert('Erro: Documento nao encontrado');
        return;
    }

    const titulo = docData.titulo;
    const conteudo = docData.conteudo;

    // Extrair extensao do titulo
    const extMatch = titulo.match(/\.([a-zA-Z0-9]+)$/);
    const extensao = extMatch ? extMatch[1].toLowerCase() : 'txt';

    // Nome do arquivo
    let nomeArquivo = titulo;
    if (!titulo.match(/\.[a-zA-Z0-9]+$/)) {
        nomeArquivo = titulo + '.txt';
    }

    // MIME types simples
    const mimeTypes = {
        'md': 'text/markdown',
        'txt': 'text/plain',
        'html': 'text/html',
        'htm': 'text/html',
        'json': 'application/json',
        'csv': 'text/csv',
        'py': 'text/x-python',
        'js': 'text/javascript',
        'java': 'text/x-java',
        'sql': 'text/x-sql',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'yml': 'text/yaml',
    };

    const mimeType = mimeTypes[extensao] || 'text/plain';

    // Baixar direto - sem conversao nenhuma
    const blob = new Blob([conteudo], { type: mimeType + ';charset=utf-8' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = nomeArquivo;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    console.log(`Documento baixado: ${nomeArquivo} (${mimeType})`);
}


/**
 * Baixa uma tabela do chat em formato escolhido pelo usuario
 * @param {number} tableIndex - Indice da tabela em window._tableContents
 * @param {string} formato - 'csv' ou 'md'
 */
function baixarTabelaComo(tableIndex, formato) {
    const markdown = window._tableContents?.[tableIndex];
    if (!markdown) {
        console.error('Tabela nao encontrada:', tableIndex);
        alert('Erro: Tabela nao encontrada');
        return;
    }

    let conteudo, mimeType, nomeArquivo;

    if (formato === 'csv') {
        conteudo = convertMarkdownTableToCSV(markdown);
        mimeType = 'text/csv';
        nomeArquivo = `tabela_${tableIndex + 1}.csv`;
    } else {
        // Markdown - baixar como esta
        conteudo = markdown;
        mimeType = 'text/markdown';
        nomeArquivo = `tabela_${tableIndex + 1}.md`;
    }

    const blob = new Blob([conteudo], { type: mimeType + ';charset=utf-8' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = nomeArquivo;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    console.log(`Tabela baixada como: ${nomeArquivo}`);
}


/**
 * Converte tabelas markdown para formato CSV
 * @param {string} markdown - Texto em markdown
 * @returns {string} - Conteudo CSV
 */
function convertMarkdownTableToCSV(markdown) {
    const lines = markdown.split('\n');
    const csvLines = [];
    let inTable = false;

    for (const line of lines) {
        const trimmed = line.trim();

        // Detectar linha de tabela
        if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
            // Ignorar linha separadora (|---|---|)
            if (trimmed.match(/^\|[\s\-:]+\|$/)) {
                continue;
            }

            inTable = true;
            // Extrair celulas
            const cells = trimmed
                .split('|')
                .slice(1, -1)  // Remover primeiro e ultimo vazio
                .map(cell => {
                    let cleaned = cell.trim();
                    // Escapar aspas e envolver em aspas se necessario
                    if (cleaned.includes(',') || cleaned.includes('"') || cleaned.includes('\n')) {
                        cleaned = '"' + cleaned.replace(/"/g, '""') + '"';
                    }
                    return cleaned;
                });

            csvLines.push(cells.join(','));
        } else if (inTable && trimmed === '') {
            // Fim da tabela
            inTable = false;
        }
    }

    // Se nao encontrou tabelas, retornar o conteudo original
    if (csvLines.length === 0) {
        return markdown;
    }

    return csvLines.join('\n');
}


/**
 * Converte Markdown para HTML (versao para documentos)
 * @param {string} markdown - Texto em markdown
 * @returns {string} - HTML formatado
 */
function convertMarkdownToHtml(markdown) {
    if (!markdown) return '';

    let html = markdown;

    // Blocos de código
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        const escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return `<pre><code class="language-${lang}">${escaped}</code></pre>`;
    });

    // Tabelas
    html = html.replace(/^\|(.+)\|\s*\n\|[-:\s|]+\|\s*\n((?:\|.+\|\s*\n?)+)/gm, (match, header, rows) => {
        const headers = header.split('|').map(h => h.trim()).filter(Boolean);
        const bodyRows = rows.trim().split('\n').map(row =>
            row.split('|').map(c => c.trim()).filter(Boolean)
        );

        let table = '<table><thead><tr>';
        headers.forEach(h => table += `<th>${h}</th>`);
        table += '</tr></thead><tbody>';
        bodyRows.forEach(row => {
            table += '<tr>';
            row.forEach(cell => table += `<td>${cell}</td>`);
            table += '</tr>';
        });
        table += '</tbody></table>';
        return table;
    });

    // Títulos
    html = html.replace(/^######\s+(.+)$/gm, '<h6>$1</h6>');
    html = html.replace(/^#####\s+(.+)$/gm, '<h5>$1</h5>');
    html = html.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');

    // Linha horizontal
    html = html.replace(/^---+$/gm, '<hr>');

    // Blockquotes
    html = html.replace(/^>\s+(.+)$/gm, '<blockquote>$1</blockquote>');
    html = html.replace(/<\/blockquote>\s*<blockquote>/g, '<br>');

    // Listas não ordenadas
    html = html.replace(/^[\*\-]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Listas ordenadas
    html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

    // Negrito e itálico
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    html = html.replace(/_([^_]+)_/g, '<em>$1</em>');

    // Código inline
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Parágrafos (linhas que não são elementos block)
    html = html.replace(/^(?!<[hupbolt]|<\/|<li|<hr|<table|<pre|<blockquote)(.+)$/gm, '<p>$1</p>');

    // Limpar quebras de linha extras
    html = html.replace(/\n{2,}/g, '\n');

    return html;
}

// ============================================================
// SISTEMA DE CONTEXTO
// ============================================================
function toggleContextPanel() {
    const panel = document.getElementById('context-panel');
    const body = document.getElementById('context-body');
    const icon = document.getElementById('context-toggle-icon');

    panel.classList.toggle('collapsed');
    const isCollapsed = panel.classList.contains('collapsed');

    body.style.display = isCollapsed ? 'none' : 'block';
    icon.textContent = isCollapsed ? '▶' : '◀';

    // Restaurar estado dos filtros ao reabrir o painel
    if (!isCollapsed) {
        const ctx = window.chatState.context;
        const filtersDiv = document.getElementById('context-filters');
        if (filtersDiv) {
            filtersDiv.style.display = ctx.mode === 'filtered' ? 'block' : 'none';
        }
    }
}

function setContextMode(mode) {
    const ctx = window.chatState.context;
    ctx.mode = mode;

    // Limpar overrides ao mudar de modo
    ctx.manualOverrides.included.clear();
    ctx.manualOverrides.excluded.clear();

    // Atualizar botoes
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    // Mostrar/esconder filtros
    const filtersDiv = document.getElementById('context-filters');
    filtersDiv.style.display = mode === 'filtered' ? 'block' : 'none';

    // Atualizar indicadores visuais se houver alunos selecionados
    if (mode === 'filtered') {
        atualizarIndicadoresVisuais();
    }

    // Atualizar lista de documentos
    updateDocumentsList();
    updateContextStatus();
}

async function loadAvailableDocuments() {
    try {
        // Buscar todos os documentos disponiveis
        const data = await api('/documentos/todos');
        window.chatState.context.availableDocs = data.documentos || [];

        // Calcular intersecoes se houver alunos selecionados
        const alunosSelecionados = window.chatState.context.filters.alunos || [];
        if (alunosSelecionados.length > 0) {
            window.chatState.context.intersectionCache = calcularIntersecoes(alunosSelecionados);
            atualizarIndicadoresVisuais();
        }

        updateDocumentsList();
    } catch (e) {
        console.error('Erro ao carregar documentos:', e);
        window.chatState.context.availableDocs = [];
        updateDocumentsList();
    }
}

function updateDocumentsList() {
    const listDiv = document.getElementById('context-docs-list');
    const ctx = window.chatState.context;
    const docs = getFilteredDocuments();
    const allDocs = ctx.availableDocs;
    const overrides = ctx.manualOverrides;
    const alunosSelecionados = new Set(ctx.filters.alunos || []);

    document.getElementById('docs-count').textContent = docs.length;
    document.getElementById('docs-total').textContent = allDocs.length;

    if (docs.length === 0) {
        listDiv.innerHTML = `
            <div class="empty-state-mini">
                <span>Nenhum documento ${allDocs.length > 0 ? 'corresponde aos filtros' : 'disponível'}</span>
            </div>
        `;
        return;
    }

    // Agrupar por atividade para melhor visualização
    const grouped = {};
    docs.forEach(doc => {
        const key = doc.atividade_nome || 'Outros';
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(doc);
    });

    let html = '';
    for (const [atividade, docList] of Object.entries(grouped)) {
        html += `<div class="doc-group-title">${atividade}</div>`;
        docList.forEach(doc => {
            // Determinar estado de selecao considerando overrides
            const isOverrideIncluded = overrides.included.has(doc.id);
            const isOverrideExcluded = overrides.excluded.has(doc.id);
            const isExcluded = ctx.excludedDocs.has(doc.id) || isOverrideExcluded;

            let isIncluded;
            if (ctx.mode === 'manual') {
                isIncluded = ctx.includedDocs.has(doc.id) || isOverrideIncluded;
            } else {
                isIncluded = !isExcluded || isOverrideIncluded;
            }

            // Determinar cor usando o novo sistema de intersecao
            const corClass = getCorDocumento(doc, alunosSelecionados, overrides);

            // Determinar classe de exclusao (nao usar se tiver override de inclusao)
            const excludedClass = (!isIncluded && !isOverrideIncluded) ? 'excluded' : '';

            // Criar nome legivel: tipo + aluno (se houver)
            const tipoLabel = TIPO_DOC_LABELS[doc.tipo] || doc.tipo;
            const displayName = doc.aluno_nome
                ? `${tipoLabel.split(' ')[1] || tipoLabel}`
                : tipoLabel;
            const tooltipText = `${tipoLabel}${doc.aluno_nome ? ' - ' + doc.aluno_nome : ''}\n${doc.nome_arquivo || ''}`;

            html += `
                <div class="doc-item-mini ${excludedClass} ${corClass}"
                     onclick="toggleDocSelection('${doc.id}')"
                     title="${tooltipText.trim()}${isOverrideIncluded ? '\n(adicionado manualmente)' : ''}${isOverrideExcluded ? '\n(removido manualmente)' : ''}">
                    <input type="checkbox" ${isIncluded ? 'checked' : ''} onclick="event.stopPropagation()">
                    <span class="doc-type-icon">${tipoLabel.substring(0, 2) || '📄'}</span>
                    <span class="doc-name">${truncateText(displayName, 18)}</span>
                    ${doc.aluno_nome ? `<span class="doc-aluno" title="${doc.aluno_nome}">${truncateText(doc.aluno_nome, 18)}</span>` : ''}
                </div>
            `;
        });
    }

    // Adicionar legenda de cores
    html += renderLegendaIntersecao();

    listDiv.innerHTML = html;
    updateContextStatus();
}

function toggleDocSelection(docId) {
    const ctx = window.chatState.context;
    const overrides = ctx.manualOverrides;
    const alunosSelecionados = new Set(ctx.filters.alunos || []);

    // Encontrar documento
    const doc = ctx.availableDocs.find(d => d.id === docId);
    if (!doc) return;

    // Verificar se documento "bate" com os filtros atuais
    const docBateComFiltros = verificarDocBateComFiltros(doc, alunosSelecionados);

    if (ctx.mode === 'manual') {
        // Modo manual: toggle simples
        if (ctx.includedDocs.has(docId)) {
            ctx.includedDocs.delete(docId);
            overrides.included.delete(docId);
        } else {
            ctx.includedDocs.add(docId);
            // Se doc nao bate com filtros, marcar como override
            if (!docBateComFiltros && alunosSelecionados.size > 0) {
                overrides.included.add(docId);
            }
        }
    } else {
        // Modo filtered/all
        if (ctx.excludedDocs.has(docId)) {
            // Re-incluir documento
            ctx.excludedDocs.delete(docId);
            overrides.excluded.delete(docId);
            // Se doc nao bate com filtros, marcar como override de inclusao
            if (!docBateComFiltros && alunosSelecionados.size > 0) {
                overrides.included.add(docId);
            }
        } else {
            // Excluir documento
            ctx.excludedDocs.add(docId);
            overrides.included.delete(docId);
            // Se doc bate com filtros, marcar como override de exclusao
            if (docBateComFiltros) {
                overrides.excluded.add(docId);
            }
        }
    }

    updateDocumentsList();
}

function toggleAllDocs() {
    const ctx = window.chatState.context;
    const docs = getFilteredDocuments();
    
    if (ctx.mode === 'manual') {
        // Se todos selecionados, desmarcar todos. Senão, selecionar todos.
        const allSelected = docs.every(d => ctx.includedDocs.has(d.id));
        docs.forEach(d => {
            if (allSelected) {
                ctx.includedDocs.delete(d.id);
            } else {
                ctx.includedDocs.add(d.id);
            }
        });
    } else {
        // Inverter exclusões
        const allExcluded = docs.every(d => ctx.excludedDocs.has(d.id));
        docs.forEach(d => {
            if (allExcluded) {
                ctx.excludedDocs.delete(d.id);
            } else {
                ctx.excludedDocs.add(d.id);
            }
        });
    }
    
    updateDocumentsList();
}

function getFilteredDocuments() {
    const ctx = window.chatState.context;
    let docs = [...ctx.availableDocs];
    
    // Aplicar filtro de JSON se ativado (funciona em todos os modos)
    if (ctx.hideJsonFiles) {
        docs = docs.filter(d => {
            const ext = (d.extensao || d.nome_arquivo || '').toLowerCase();
            return !ext.endsWith('.json');
        });
    }
    
    if (ctx.mode === 'all') {
        return docs;
    }
    
    if (ctx.mode === 'filtered') {
        const f = ctx.filters;
        
        if (f.alunos && f.alunos.length > 0) {
            docs = docs.filter(d => !d.aluno_id || f.alunos.includes(d.aluno_id));
        }
        if (f.materias && f.materias.length > 0) {
            docs = docs.filter(d => f.materias.includes(d.materia_id));
        }
        if (f.turmas && f.turmas.length > 0) {
            docs = docs.filter(d => f.turmas.includes(d.turma_id));
        }
        if (f.atividades && f.atividades.length > 0) {
            docs = docs.filter(d => f.atividades.includes(d.atividade_id));
        }
        if (f.tipos && f.tipos.length > 0) {
            docs = docs.filter(d => f.tipos.includes(d.tipo));
        }
    }
    
    return docs;
}

// Toggle para ocultar/mostrar arquivos JSON
function toggleHideJson() {
    const checkbox = document.getElementById('hide-json-toggle');
    window.chatState.context.hideJsonFiles = checkbox?.checked || false;
    updateDocumentsList();
    updateContextStatus();
}

function getSelectedDocumentIds() {
    const ctx = window.chatState.context;
    const docs = getFilteredDocuments();
    
    if (ctx.mode === 'manual') {
        return Array.from(ctx.includedDocs);
    }
    
    return docs
        .filter(d => !ctx.excludedDocs.has(d.id))
        .map(d => d.id);
}

function updateContextStatus() {
    const selected = getSelectedDocumentIds();
    const total = window.chatState.context.availableDocs.length;
    const statusEl = document.getElementById('context-status');
    
    if (!statusEl) return;
    
    if (selected.length === 0) {
        statusEl.textContent = '📚 Contexto: Nenhum documento selecionado';
        statusEl.className = 'context-warning';
    } else if (selected.length === total) {
        statusEl.textContent = `📚 Contexto: Todos os ${total} documentos`;
        statusEl.className = '';
    } else {
        statusEl.textContent = `📚 Contexto: ${selected.length} de ${total} documentos`;
        statusEl.className = '';
    }
}

// ============================================================
// CALCULO DE INTERSECOES
// ============================================================

/**
 * Calcula a intersecao de alunos selecionados com cada item de filtro.
 * Retorna um cache com contagens para materias, turmas e atividades.
 *
 * @param {string[]} alunosSelecionados - IDs dos alunos selecionados
 * @returns {Object} Cache de intersecoes
 */
function calcularIntersecoes(alunosSelecionados) {
    const docs = window.chatState.context.availableDocs;
    const total = alunosSelecionados.length;

    // Se nenhum aluno selecionado, retorna cache vazio
    if (total === 0) {
        return { materias: {}, turmas: {}, atividades: {} };
    }

    const alunosSet = new Set(alunosSelecionados);

    // Calcular intersecao por materia
    const materias = {};
    const materiasUnicas = [...new Set(docs.map(d => d.materia_id).filter(Boolean))];

    materiasUnicas.forEach(materiaId => {
        const docsMateria = docs.filter(d => d.materia_id === materiaId);
        const alunosComDocs = new Set();

        docsMateria.forEach(doc => {
            if (doc.aluno_id && alunosSet.has(doc.aluno_id)) {
                alunosComDocs.add(doc.aluno_id);
            }
        });

        materias[materiaId] = {
            total: total,
            comDocs: alunosComDocs.size,
            semDocs: total - alunosComDocs.size
        };
    });

    // Calcular intersecao por turma
    const turmas = {};
    const turmasUnicas = [...new Set(docs.map(d => d.turma_id).filter(Boolean))];

    turmasUnicas.forEach(turmaId => {
        const docsTurma = docs.filter(d => d.turma_id === turmaId);
        const alunosComDocs = new Set();

        docsTurma.forEach(doc => {
            if (doc.aluno_id && alunosSet.has(doc.aluno_id)) {
                alunosComDocs.add(doc.aluno_id);
            }
        });

        turmas[turmaId] = {
            total: total,
            comDocs: alunosComDocs.size,
            semDocs: total - alunosComDocs.size
        };
    });

    // Calcular intersecao por atividade
    const atividades = {};
    const atividadesUnicas = [...new Set(docs.map(d => d.atividade_id).filter(Boolean))];

    atividadesUnicas.forEach(atividadeId => {
        const docsAtividade = docs.filter(d => d.atividade_id === atividadeId);
        const alunosComDocs = new Set();

        docsAtividade.forEach(doc => {
            if (doc.aluno_id && alunosSet.has(doc.aluno_id)) {
                alunosComDocs.add(doc.aluno_id);
            }
        });

        atividades[atividadeId] = {
            total: total,
            comDocs: alunosComDocs.size,
            semDocs: total - alunosComDocs.size
        };
    });

    return { materias, turmas, atividades };
}

/**
 * Determina a classe CSS para um item de filtro baseado na intersecao.
 *
 * @param {Object} intersecaoData - Dados de intersecao do item { total, comDocs, semDocs }
 * @returns {string} Classe CSS a aplicar
 */
function getCorIntersecao(intersecaoData) {
    if (!intersecaoData || intersecaoData.total === 0) return 'filter-normal';

    const { total, comDocs } = intersecaoData;

    if (comDocs === total) return 'filter-normal';   // Todos os alunos tem docs
    if (comDocs === 0) return 'filter-none';         // Nenhum aluno tem docs
    return 'filter-partial';                          // Alguns alunos tem docs
}

/**
 * Determina a classe CSS para um documento individual.
 *
 * @param {Object} doc - Documento
 * @param {Set} alunosSelecionados - Set de IDs dos alunos selecionados
 * @param {Object} overrides - Objeto com Sets de included e excluded
 * @returns {string} Classe CSS a aplicar
 */
function getCorDocumento(doc, alunosSelecionados, overrides) {
    // Override manual de inclusao = laranja
    if (overrides.included.has(doc.id)) {
        return 'doc-override-included';
    }

    // Override manual de exclusao = azul claro
    if (overrides.excluded.has(doc.id)) {
        return 'doc-override-excluded';
    }

    // Sem alunos selecionados ou documento base = normal
    if (alunosSelecionados.size === 0 || !doc.aluno_id) {
        return '';
    }

    // Documento de aluno selecionado = normal
    if (alunosSelecionados.has(doc.aluno_id)) {
        return '';
    }

    // Documento de aluno NAO selecionado = cinza
    return 'doc-no-intersection';
}

/**
 * Verifica se um documento corresponde aos filtros atuais de alunos.
 *
 * @param {Object} doc - Documento
 * @param {Set} alunosSelecionados - Set de IDs dos alunos selecionados
 * @returns {boolean} True se o documento bate com os filtros
 */
function verificarDocBateComFiltros(doc, alunosSelecionados) {
    // Documento base sempre "bate"
    if (!doc.aluno_id) return true;

    // Nenhum aluno selecionado = todos batem
    if (alunosSelecionados.size === 0) return true;

    // Verificar se o aluno do doc esta entre os selecionados
    return alunosSelecionados.has(doc.aluno_id);
}

/**
 * Atualiza indicadores visuais de intersecao em todos os selects de filtro.
 */
function atualizarIndicadoresVisuais() {
    const cache = window.chatState.context.intersectionCache;
    const alunosSelecionados = window.chatState.context.filters.alunos || [];

    // Se nenhum aluno selecionado, limpar todos os indicadores
    if (alunosSelecionados.length === 0) {
        limparIndicadoresVisuais();
        return;
    }

    // Atualizar opcoes de materias
    const selectMaterias = document.getElementById('filter-materias');
    if (selectMaterias && cache.materias) {
        Array.from(selectMaterias.options).forEach(opt => {
            const data = cache.materias[opt.value];
            // Remover classes antigas
            opt.classList.remove('filter-normal', 'filter-partial', 'filter-none');
            // Adicionar nova classe
            if (data) {
                opt.classList.add(getCorIntersecao(data));
                // Adicionar indicador numerico
                const originalText = opt.dataset.originalText || opt.text;
                opt.dataset.originalText = originalText;
                if (data.comDocs < data.total) {
                    opt.text = `${originalText} (${data.comDocs}/${data.total})`;
                } else {
                    opt.text = originalText;
                }
            }
        });
    }

    // Atualizar opcoes de turmas
    const selectTurmas = document.getElementById('filter-turmas');
    if (selectTurmas && cache.turmas) {
        Array.from(selectTurmas.options).forEach(opt => {
            if (!opt.value || opt.disabled) return;
            const data = cache.turmas[opt.value];
            opt.classList.remove('filter-normal', 'filter-partial', 'filter-none');
            if (data) {
                opt.classList.add(getCorIntersecao(data));
                const originalText = opt.dataset.originalText || opt.text;
                opt.dataset.originalText = originalText;
                if (data.comDocs < data.total) {
                    opt.text = `${originalText} (${data.comDocs}/${data.total})`;
                } else {
                    opt.text = originalText;
                }
            }
        });
    }

    // Atualizar opcoes de atividades
    const selectAtividades = document.getElementById('filter-atividades');
    if (selectAtividades && cache.atividades) {
        Array.from(selectAtividades.options).forEach(opt => {
            if (!opt.value || opt.disabled) return;
            const data = cache.atividades[opt.value];
            opt.classList.remove('filter-normal', 'filter-partial', 'filter-none');
            if (data) {
                opt.classList.add(getCorIntersecao(data));
                const originalText = opt.dataset.originalText || opt.text;
                opt.dataset.originalText = originalText;
                if (data.comDocs < data.total) {
                    opt.text = `${originalText} (${data.comDocs}/${data.total})`;
                } else {
                    opt.text = originalText;
                }
            }
        });
    }
}

/**
 * Limpa todos os indicadores visuais dos selects de filtro.
 */
function limparIndicadoresVisuais() {
    ['filter-materias', 'filter-turmas', 'filter-atividades'].forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            Array.from(select.options).forEach(opt => {
                opt.classList.remove('filter-normal', 'filter-partial', 'filter-none');
                if (opt.dataset.originalText) {
                    opt.text = opt.dataset.originalText;
                }
            });
        }
    });
}

/**
 * Renderiza a legenda de cores para intersecao.
 */
function renderLegendaIntersecao() {
    const alunosSelecionados = window.chatState.context.filters.alunos || [];

    // Só mostrar legenda se houver alunos selecionados ou overrides
    const overrides = window.chatState.context.manualOverrides;
    if (alunosSelecionados.length === 0 && overrides.included.size === 0 && overrides.excluded.size === 0) {
        return '';
    }

    return `
        <div class="intersection-legend">
            <div class="legend-item">
                <span class="legend-color normal"></span>
                <span>Normal</span>
            </div>
            <div class="legend-item">
                <span class="legend-color partial"></span>
                <span>Parcial</span>
            </div>
            <div class="legend-item">
                <span class="legend-color none"></span>
                <span>Sem docs</span>
            </div>
            <div class="legend-item">
                <span class="legend-color override-in"></span>
                <span>Adicionado</span>
            </div>
            <div class="legend-item">
                <span class="legend-color override-out"></span>
                <span>Removido</span>
            </div>
        </div>
    `;
}

// ============================================================
// FILTROS CASCATA - IMPROVED DROPDOWNS
// ============================================================

/**
 * Cria um dropdown customizado com checkboxes
 * @param {string} containerId - ID do container onde criar o dropdown
 * @param {Array} items - Lista de itens {id, nome, count?}
 * @param {Function} onChange - Callback quando seleção muda
 * @param {Object} options - Opções adicionais
 */
function createFilterDropdown(containerId, items, onChange, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const placeholder = options.placeholder || 'Selecione...';
    const emptyText = options.emptyText || 'Nenhuma opção disponível';
    const searchable = options.searchable !== false && items.length > 5;
    const selected = options.selected || [];

    const dropdownId = `dropdown-${containerId}`;

    container.innerHTML = `
        <div class="filter-dropdown" id="${dropdownId}">
            <div class="filter-dropdown-trigger" onclick="toggleFilterDropdown('${dropdownId}')">
                <span class="trigger-text">${selected.length > 0 ? `${selected.length} selecionado(s)` : placeholder}</span>
                <span class="filter-dropdown-arrow">▼</span>
            </div>
            <div class="filter-dropdown-menu">
                ${searchable ? `
                    <div class="filter-dropdown-search">
                        <input type="text" placeholder="Buscar..." oninput="filterDropdownItems('${dropdownId}', this.value)">
                    </div>
                ` : ''}
                <div class="filter-dropdown-items">
                    ${items.length === 0 ? `<div class="filter-dropdown-empty">${emptyText}</div>` :
                        items.map(item => `
                            <div class="filter-dropdown-item ${selected.includes(item.id) ? 'checked' : ''}"
                                 data-value="${item.id}"
                                 onclick="toggleDropdownItem('${dropdownId}', '${item.id}')">
                                <input type="checkbox" ${selected.includes(item.id) ? 'checked' : ''}>
                                <span class="item-label">${item.nome}</span>
                                ${item.count !== undefined ? `<span class="item-count">${item.count}</span>` : ''}
                            </div>
                        `).join('')
                    }
                </div>
            </div>
        </div>
    `;

    // Guardar callback e items
    container._dropdownCallback = onChange;
    container._dropdownItems = items;
}

function toggleFilterDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;

    const wasOpen = dropdown.classList.contains('open');

    // Fechar todos os outros dropdowns
    document.querySelectorAll('.filter-dropdown.open').forEach(d => {
        d.classList.remove('open');
        d.querySelector('.filter-dropdown-trigger')?.classList.remove('active');
    });

    if (!wasOpen) {
        dropdown.classList.add('open');
        dropdown.querySelector('.filter-dropdown-trigger')?.classList.add('active');

        // Focus no search se existir
        const searchInput = dropdown.querySelector('.filter-dropdown-search input');
        if (searchInput) {
            setTimeout(() => searchInput.focus(), 100);
        }
    }
}

function toggleDropdownItem(dropdownId, value) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;

    const item = dropdown.querySelector(`.filter-dropdown-item[data-value="${value}"]`);
    if (!item) return;

    const checkbox = item.querySelector('input[type="checkbox"]');
    checkbox.checked = !checkbox.checked;
    item.classList.toggle('checked', checkbox.checked);

    // Atualizar texto do trigger
    const selectedCount = dropdown.querySelectorAll('.filter-dropdown-item.checked').length;
    const trigger = dropdown.querySelector('.trigger-text');
    if (trigger) {
        trigger.textContent = selectedCount > 0 ? `${selectedCount} selecionado(s)` : 'Selecione...';
    }

    // Chamar callback
    const container = dropdown.parentElement;
    if (container._dropdownCallback) {
        const selectedValues = Array.from(dropdown.querySelectorAll('.filter-dropdown-item.checked'))
            .map(el => el.dataset.value);
        container._dropdownCallback(selectedValues);
    }
}

function filterDropdownItems(dropdownId, searchText) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;

    const search = searchText.toLowerCase().trim();
    dropdown.querySelectorAll('.filter-dropdown-item').forEach(item => {
        const label = item.querySelector('.item-label')?.textContent.toLowerCase() || '';
        item.style.display = label.includes(search) ? 'flex' : 'none';
    });
}

function getDropdownSelectedValues(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];

    const dropdown = container.querySelector('.filter-dropdown');
    if (!dropdown) return [];

    return Array.from(dropdown.querySelectorAll('.filter-dropdown-item.checked'))
        .map(el => el.dataset.value);
}

// Fechar dropdowns ao clicar fora
document.addEventListener('click', (e) => {
    if (!e.target.closest('.filter-dropdown')) {
        document.querySelectorAll('.filter-dropdown.open').forEach(d => {
            d.classList.remove('open');
            d.querySelector('.filter-dropdown-trigger')?.classList.remove('active');
        });
    }
});

// ============================================================
// FILTROS CASCATA - ORIGINAL FUNCTIONS (UPDATED)
// ============================================================
async function onFilterAlunosChange() {
    const select = document.getElementById('filter-alunos');
    const selected = Array.from(select.selectedOptions).map(o => o.value);
    window.chatState.context.filters.alunos = selected.length > 0 ? selected : null;

    updateFilterChips('alunos', selected, window._chatAlunos, 'nome');

    // Recalcular intersecoes com os novos alunos selecionados
    window.chatState.context.intersectionCache = calcularIntersecoes(selected);

    // Atualizar indicadores visuais nos selects de filtro
    atualizarIndicadoresVisuais();

    updateDocumentsList();
}

async function onFilterMateriasChange() {
    const select = document.getElementById('filter-materias');
    const selected = Array.from(select.selectedOptions).map(o => o.value);
    window.chatState.context.filters.materias = selected.length > 0 ? selected : null;
    
    updateFilterChips('materias', selected, window._chatMaterias, 'nome');
    
    // Carregar turmas das matérias selecionadas
    await loadTurmasForMaterias(selected);
    
    // Limpar filtros dependentes
    clearDependentFilters(['turmas', 'atividades']);
    updateDocumentsList();
}

async function onFilterTurmasChange() {
    const select = document.getElementById('filter-turmas');
    const selected = Array.from(select.selectedOptions).map(o => o.value);
    window.chatState.context.filters.turmas = selected.length > 0 ? selected : null;
    
    updateFilterChips('turmas', selected, window.chatState.context.cache.turmasDisponiveis, 'nome');
    
    // Carregar atividades das turmas selecionadas
    await loadAtividadesForTurmas(selected);
    
    // Limpar filtros dependentes
    clearDependentFilters(['atividades']);
    updateDocumentsList();
}

async function onFilterAtividadesChange() {
    const select = document.getElementById('filter-atividades');
    const selected = Array.from(select.selectedOptions).map(o => o.value);
    window.chatState.context.filters.atividades = selected.length > 0 ? selected : null;
    
    updateFilterChips('atividades', selected, window.chatState.context.cache.atividadesDisponiveis, 'nome');
    updateDocumentsList();
}

function onFilterTiposChange() {
    const select = document.getElementById('filter-tipos');
    const selected = Array.from(select.selectedOptions).map(o => o.value);
    window.chatState.context.filters.tipos = selected.length > 0 ? selected : null;
    
    // Criar lista fake para chips
    const tiposList = selected.map(t => ({ id: t, nome: TIPO_DOC_LABELS[t] || t }));
    updateFilterChips('tipos', selected, tiposList, 'nome');
    updateDocumentsList();
}

async function loadTurmasForMaterias(materiaIds) {
    const select = document.getElementById('filter-turmas');

    if (!materiaIds || materiaIds.length === 0) {
        select.innerHTML = '<option value="" disabled>Selecione matéria(s) primeiro</option>';
        window.chatState.context.cache.turmasDisponiveis = [];
        return;
    }

    try {
        // Carregar turmas de cada materia
        const turmasPromises = materiaIds.map(id => api(`/materias/${id}`).catch(() => ({ turmas: [] })));
        const results = await Promise.all(turmasPromises);

        const todasTurmas = results.flatMap(r => r.turmas || []);
        window.chatState.context.cache.turmasDisponiveis = todasTurmas;

        select.innerHTML = todasTurmas.map(t => {
            return `<option value="${t.id}" data-original-text="${t.nome} ${t.materia_nome ? `(${t.materia_nome})` : ''}">${t.nome} ${t.materia_nome ? `(${t.materia_nome})` : ''}</option>`;
        }).join('');

        if (todasTurmas.length === 0) {
            select.innerHTML = '<option value="" disabled>Nenhuma turma encontrada</option>';
        }

        // Atualizar indicadores visuais apos carregar turmas
        atualizarIndicadoresVisuais();
    } catch (e) {
        console.error('Erro ao carregar turmas:', e);
    }
}

async function loadAtividadesForTurmas(turmaIds) {
    const select = document.getElementById('filter-atividades');

    if (!turmaIds || turmaIds.length === 0) {
        select.innerHTML = '<option value="" disabled>Selecione turma(s) primeiro</option>';
        window.chatState.context.cache.atividadesDisponiveis = [];
        return;
    }

    try {
        // Carregar atividades de cada turma
        const atividadesPromises = turmaIds.map(id => api(`/turmas/${id}`).catch(() => ({ atividades: [] })));
        const results = await Promise.all(atividadesPromises);

        const todasAtividades = results.flatMap(r => r.atividades || []);
        window.chatState.context.cache.atividadesDisponiveis = todasAtividades;

        select.innerHTML = todasAtividades.map(a =>
            `<option value="${a.id}" data-original-text="${a.nome}">${a.nome}</option>`
        ).join('');

        if (todasAtividades.length === 0) {
            select.innerHTML = '<option value="" disabled>Nenhuma atividade encontrada</option>';
        }

        // Atualizar indicadores visuais apos carregar atividades
        atualizarIndicadoresVisuais();
    } catch (e) {
        console.error('Erro ao carregar atividades:', e);
    }
}

function updateFilterChips(filterName, selectedIds, itemsList, nameField) {
    const chipsDiv = document.getElementById(`chips-${filterName}`);
    if (!chipsDiv) return;
    
    if (!selectedIds || selectedIds.length === 0) {
        chipsDiv.innerHTML = '';
        return;
    }
    
    chipsDiv.innerHTML = selectedIds.map(id => {
        const item = itemsList.find(i => i.id === id);
        const name = item ? item[nameField] : id;
        return `
            <span class="filter-chip">
                ${truncateText(name, 20)}
                <button onclick="removeFilterItem('${filterName}', '${id}')">&times;</button>
            </span>
        `;
    }).join('');
}

function removeFilterItem(filterName, itemId) {
    const select = document.getElementById(`filter-${filterName}`);
    if (select) {
        Array.from(select.options).forEach(opt => {
            if (opt.value === itemId) opt.selected = false;
        });
    }
    
    // Trigger change event
    const handlers = {
        'alunos': onFilterAlunosChange,
        'materias': onFilterMateriasChange,
        'turmas': onFilterTurmasChange,
        'atividades': onFilterAtividadesChange,
        'tipos': onFilterTiposChange
    };
    
    if (handlers[filterName]) handlers[filterName]();
}

function clearDependentFilters(filterNames) {
    filterNames.forEach(name => {
        const select = document.getElementById(`filter-${name}`);
        if (select) {
            Array.from(select.options).forEach(opt => opt.selected = false);
        }
        window.chatState.context.filters[name] = null;
        const chipsDiv = document.getElementById(`chips-${name}`);
        if (chipsDiv) chipsDiv.innerHTML = '';
    });
}

function clearAllFilters() {
    const ctx = window.chatState.context;

    ['alunos', 'materias', 'turmas', 'atividades', 'tipos'].forEach(name => {
        const select = document.getElementById(`filter-${name}`);
        if (select) {
            Array.from(select.options).forEach(opt => opt.selected = false);
        }
        ctx.filters[name] = null;
        const chipsDiv = document.getElementById(`chips-${name}`);
        if (chipsDiv) chipsDiv.innerHTML = '';
    });

    // Limpar overrides e cache de intersecoes
    ctx.manualOverrides.included.clear();
    ctx.manualOverrides.excluded.clear();
    ctx.intersectionCache = { materias: {}, turmas: {}, atividades: {} };

    // Limpar indicadores visuais
    limparIndicadoresVisuais();

    // Reset turmas e atividades para estado inicial usando createFilterDropdown
    createFilterDropdown('filter-turmas-container', [], () => {}, {
        placeholder: 'Selecione matéria(s) primeiro',
        emptyText: 'Selecione matéria(s) primeiro'
    });
    createFilterDropdown('filter-atividades-container', [], () => {}, {
        placeholder: 'Selecione turma(s) primeiro',
        emptyText: 'Selecione turma(s) primeiro'
    });

    // Limpar cache de turmas e atividades
    ctx.cache = ctx.cache || {};
    ctx.cache.turmasDisponiveis = [];
    ctx.cache.atividadesDisponiveis = [];

    updateDocumentsList();
}

// ============================================================
// CSS ADICIONAL PARA O CHAT
// ============================================================
function injectChatStyles() {
    if (document.getElementById('chat-system-styles')) return;
    
    const styles = document.createElement('style');
    styles.id = 'chat-system-styles';
    styles.textContent = `
        .chat-layout {
            display: flex;
            height: calc(100vh - 100px);
            gap: 0;
        }
        
        .chat-context-panel {
            width: 320px;
            min-width: 320px;
            background: var(--bg-card);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            transition: width 0.3s, min-width 0.3s;
        }
        
        .chat-context-panel.collapsed {
            width: 50px;
            min-width: 50px;
        }
        
        .context-header {
            padding: 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .context-header h3 {
            margin: 0;
            font-size: 1rem;
        }
        
        .context-body {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }
        
        .context-section {
            margin-bottom: 20px;
        }
        
        .context-mode-buttons {
            display: flex;
            gap: 4px;
        }
        
        .mode-btn {
            flex: 1;
            padding: 8px 4px;
            border: 1px solid var(--border);
            background: var(--bg-input);
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.75rem;
            transition: all 0.2s;
        }
        
        .mode-btn:hover {
            border-color: var(--blue);
        }
        
        .mode-btn.active {
            background: var(--blue);
            border-color: var(--blue);
            color: white;
        }
        
        .context-filters {
            margin-top: 16px;
        }
        
        .filter-group {
            margin-bottom: 16px;
        }
        
        .filter-group .form-label {
            font-size: 0.85rem;
            margin-bottom: 4px;
        }
        
        .filter-select {
            width: 100%;
            min-height: 60px;
            font-size: 0.85rem;
        }

        /* === IMPROVED FILTER DROPDOWNS === */
        .filter-dropdown {
            position: relative;
            width: 100%;
        }

        .filter-dropdown-trigger {
            width: 100%;
            padding: 8px 12px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
            color: var(--text);
            transition: border-color 0.2s;
        }

        .filter-dropdown-trigger:hover {
            border-color: var(--primary);
        }

        .filter-dropdown-trigger.active {
            border-color: var(--primary);
            border-bottom-left-radius: 0;
            border-bottom-right-radius: 0;
        }

        .filter-dropdown-arrow {
            transition: transform 0.2s;
        }

        .filter-dropdown-trigger.active .filter-dropdown-arrow {
            transform: rotate(180deg);
        }

        .filter-dropdown-menu {
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--bg-card);
            border: 1px solid var(--primary);
            border-top: none;
            border-radius: 0 0 6px 6px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 100;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .filter-dropdown.open .filter-dropdown-menu {
            display: block;
        }

        .filter-dropdown-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: background 0.1s;
        }

        .filter-dropdown-item:hover {
            background: var(--bg-hover);
        }

        .filter-dropdown-item input[type="checkbox"] {
            width: 16px;
            height: 16px;
            cursor: pointer;
            accent-color: var(--primary);
        }

        .filter-dropdown-item.checked {
            background: rgba(59, 130, 246, 0.1);
        }

        .filter-dropdown-item .item-label {
            flex: 1;
        }

        .filter-dropdown-item .item-count {
            font-size: 0.75rem;
            color: var(--text-muted);
            background: var(--bg-input);
            padding: 2px 6px;
            border-radius: 10px;
        }

        .filter-dropdown-empty {
            padding: 12px;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
        }

        .filter-dropdown-search {
            padding: 8px;
            border-bottom: 1px solid var(--border);
        }

        .filter-dropdown-search input {
            width: 100%;
            padding: 6px 10px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 4px;
            font-size: 0.8rem;
            color: var(--text);
        }

        .filter-dropdown-search input:focus {
            outline: none;
            border-color: var(--primary);
        }

        .filter-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-top: 6px;
        }
        
        .filter-chip {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            background: var(--blue);
            color: white;
            border-radius: 12px;
            font-size: 0.75rem;
        }
        
        .filter-chip button {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 0;
            font-size: 1rem;
            line-height: 1;
        }
        
        .docs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .docs-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--bg-dark);
        }
        
        .doc-group-title {
            padding: 6px 10px;
            background: var(--bg-input);
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
        }
        
        .doc-item-mini {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            cursor: pointer;
            font-size: 0.8rem;
            border-bottom: 1px solid var(--border);
            transition: background 0.2s;
        }
        
        .doc-item-mini:hover {
            background: var(--bg-input);
        }
        
        .doc-item-mini.excluded {
            opacity: 0.5;
            text-decoration: line-through;
        }
        
        .doc-item-mini.doc-partial {
            background: rgba(255, 193, 7, 0.1);
        }

        /* ============================================
           CORES DE INTERSECAO - SISTEMA DE FILTROS
           ============================================ */

        /* Intersecao em itens de filtro (options dos selects) */
        .filter-normal { }

        .filter-partial {
            background: rgba(234, 179, 8, 0.2) !important;
        }

        .filter-none {
            background: rgba(113, 113, 122, 0.15) !important;
            color: var(--text-muted) !important;
        }

        /* Documentos com override manual */
        .doc-item-mini.doc-override-included {
            background: rgba(249, 115, 22, 0.2) !important;
            border-left: 3px solid #f97316;
            position: relative;
        }

        .doc-item-mini.doc-override-excluded {
            background: rgba(56, 189, 248, 0.15) !important;
            border-left: 3px solid #38bdf8;
            text-decoration: line-through;
            opacity: 0.7;
        }

        /* Documento que nao bate com alunos selecionados */
        .doc-item-mini.doc-no-intersection {
            opacity: 0.5;
            background: rgba(113, 113, 122, 0.1);
        }

        /* Legenda de cores */
        .intersection-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 10px;
            border-top: 1px solid var(--border);
            margin-top: 12px;
            font-size: 0.7rem;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }

        .legend-color.normal { background: var(--bg-input); border: 1px solid var(--border); }
        .legend-color.partial { background: rgba(234, 179, 8, 0.4); }
        .legend-color.none { background: rgba(113, 113, 122, 0.3); }
        .legend-color.override-in { background: rgba(249, 115, 22, 0.4); }
        .legend-color.override-out { background: rgba(56, 189, 248, 0.4); }

        .doc-item-mini input[type="checkbox"] {
            margin: 0;
        }
        
        .doc-type-icon {
            font-size: 0.9rem;
        }
        
        .doc-name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .doc-aluno {
            font-size: 0.7rem;
            color: var(--text-muted);
            background: var(--bg-input);
            padding: 1px 6px;
            border-radius: 8px;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex-shrink: 0;
        }
        
        .empty-state-mini {
            padding: 20px;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
        }
        
        /* Chat Main */
        .chat-main {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
        }
        
        .chat-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-card);
        }
        
        .chat-header h2 {
            margin: 0;
            font-size: 1.1rem;
        }
        
        .chat-header-right {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .form-label-inline {
            margin: 0;
            font-size: 0.85rem;
            color: var(--text-muted);
        }
        
        .provider-warning {
            color: var(--amber);
            font-size: 0.85rem;
        }
        
        .provider-warning a {
            color: var(--blue);
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .message {
            max-width: 80%;
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            align-self: flex-end;
        }
        
        .message.assistant {
            align-self: flex-start;
        }
        
        .message-content {
            padding: 14px 18px;
            border-radius: 12px;
            font-size: 0.9rem;
            line-height: 1.6;
        }
        
        .message.user .message-content {
            background: var(--blue);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant .message-content {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-bottom-left-radius: 4px;
        }
        
        .message.assistant.error .message-content {
            border-color: var(--danger);
            background: rgba(248, 81, 73, 0.1);
        }
        
        .message-meta {
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-top: 4px;
            padding-left: 4px;
        }
        
        .message-content pre {
            background: var(--bg-dark);
            padding: 12px;
            border-radius: 6px;
            margin: 8px 0;
            overflow-x: auto;
        }
        
        .message-content code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
        }

        /* ============================================
           ESTILOS MARKDOWN - CHAT
           ============================================ */

        /* Títulos */
        .message-content .md-h1 {
            font-size: 1.5rem;
            font-weight: 700;
            margin: 16px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--blue);
            color: var(--text);
        }
        .message-content .md-h2 {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 14px 0 10px 0;
            color: var(--text);
        }
        .message-content .md-h3 {
            font-size: 1.1rem;
            font-weight: 600;
            margin: 12px 0 8px 0;
            color: var(--text);
        }
        .message-content .md-h4,
        .message-content .md-h5,
        .message-content .md-h6 {
            font-size: 1rem;
            font-weight: 600;
            margin: 10px 0 6px 0;
            color: var(--text-muted);
        }

        /* Tabelas */
        .message-content .md-table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            font-size: 0.85rem;
            background: var(--bg-dark);
            border-radius: 6px;
            overflow: hidden;
        }
        .message-content .md-table th,
        .message-content .md-table td {
            border: 1px solid var(--border);
            padding: 10px 12px;
            text-align: left;
        }
        .message-content .md-table th {
            background: var(--bg-input);
            font-weight: 600;
            color: var(--text);
        }
        .message-content .md-table tr:nth-child(even) {
            background: rgba(255,255,255,0.02);
        }

        /* Listas */
        .message-content .md-ul,
        .message-content .md-ol {
            margin: 10px 0;
            padding-left: 24px;
        }
        .message-content .md-li,
        .message-content .md-oli {
            margin: 4px 0;
            line-height: 1.5;
        }

        /* Blockquotes */
        .message-content .md-quote {
            border-left: 4px solid var(--blue);
            margin: 12px 0;
            padding: 8px 16px;
            background: rgba(59, 130, 246, 0.1);
            color: var(--text-muted);
            font-style: italic;
            border-radius: 0 6px 6px 0;
        }

        /* Linha horizontal */
        .message-content .md-hr {
            border: none;
            border-top: 1px solid var(--border);
            margin: 16px 0;
        }

        /* Links */
        .message-content .md-link {
            color: var(--blue);
            text-decoration: none;
        }
        .message-content .md-link:hover {
            text-decoration: underline;
        }

        /* Código inline */
        .message-content .md-inline-code {
            background: var(--bg-dark);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.85em;
        }

        /* Bloco de código */
        .message-content .md-pre {
            background: var(--bg-dark);
            padding: 14px;
            border-radius: 8px;
            margin: 12px 0;
            overflow-x: auto;
            border: 1px solid var(--border);
        }

        /* Container de tabela com opcoes de download */
        .table-container {
            margin: 12px 0;
        }
        .table-download-options {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 8px;
            padding: 8px 12px;
            background: var(--bg-input);
            border-radius: 6px;
            font-size: 0.8rem;
        }
        .table-download-label {
            color: var(--text-muted);
        }
        .table-download-btn {
            padding: 4px 12px;
            font-size: 0.75rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
        }
        .table-download-btn:hover {
            background: var(--blue);
            color: white;
            border-color: var(--blue);
        }

        /* ============================================
           BLOCOS DE DOCUMENTO GERADO
           ============================================ */
        .document-block {
            background: linear-gradient(135deg, var(--bg-input) 0%, var(--bg-card) 100%);
            border: 2px solid var(--blue);
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .document-block-header {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .document-icon {
            font-size: 1.5rem;
        }
        .document-title {
            font-weight: 600;
            font-size: 1rem;
            color: var(--text);
        }
        .document-block-buttons {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .document-open-btn,
        .document-download-btn {
            padding: 8px 16px;
            font-size: 0.9rem;
        }
        .document-download-btn {
            background: var(--bg-input);
            border: 1px solid var(--border);
            color: var(--text);
        }
        .document-download-btn:hover {
            background: var(--bg-card);
            border-color: var(--blue);
        }

        /* Blocos de documento binário (gerados por code execution) */
        .document-block.binary-document {
            background: linear-gradient(135deg, #1a2744 0%, #1e3a5f 100%);
            border: 2px solid #10b981;
        }
        .document-size {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-left: auto;
        }
        .binary-document .document-download-btn {
            background: #10b981;
            border-color: #10b981;
            color: white;
        }
        .binary-document .document-download-btn:hover {
            background: #059669;
            border-color: #059669;
        }

        .message.loading .message-content {
            background: var(--bg-input);
        }
        
        .typing-indicator {
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }
        
        /* Chat Input */
        .chat-input-area {
            padding: 16px 20px;
            border-top: 1px solid var(--border);
            background: var(--bg-card);
        }
        
        .chat-input-row {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }
        
        .chat-input {
            flex: 1;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 16px;
            color: var(--text);
            font-family: inherit;
            font-size: 0.9rem;
            resize: none;
            min-height: 44px;
            max-height: 200px;
        }
        
        .chat-input:focus {
            outline: none;
            border-color: var(--blue);
        }
        
        .chat-input:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .chat-input-info {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 8px;
        }
        
        .context-warning {
            color: var(--amber);
        }

        /* ============================================================
           CHAT RESPONSIVE - TABLET (max-width: 768px)
           ============================================================ */
        @media screen and (max-width: 768px) {
            .chat-layout {
                flex-direction: column;
                height: calc(100vh - 80px);
            }

            .chat-context-panel {
                width: 100%;
                min-width: 100%;
                max-height: 45vh;
                border-right: none;
                border-bottom: 1px solid var(--border);
            }

            .chat-context-panel.collapsed {
                width: 100%;
                min-width: 100%;
                max-height: 48px;
            }

            .chat-context-panel.collapsed .context-body {
                display: none;
            }

            #context-toggle-icon {
                transform: rotate(90deg);
            }
            .chat-context-panel.collapsed #context-toggle-icon {
                transform: rotate(-90deg);
            }

            .context-body {
                max-height: calc(45vh - 60px);
                overflow-y: auto;
            }

            .docs-list {
                max-height: 150px;
            }

            .chat-main {
                flex: 1;
                min-height: 0;
            }

            .chat-header {
                padding: 12px 16px;
                flex-wrap: wrap;
                gap: 8px;
            }

            .chat-header-right {
                width: 100%;
                justify-content: space-between;
            }

            .chat-header-right .form-select {
                flex: 1;
                min-width: 0 !important;
            }

            .chat-messages {
                padding: 12px;
            }

            .message-content {
                padding: 12px 14px;
            }

            .chat-input-area {
                padding: 12px 16px;
            }

            .chat-input {
                font-size: 16px; /* Prevents iOS zoom */
            }

            /* Touch-friendly buttons */
            .mode-btn,
            .filter-dropdown-trigger,
            .filter-dropdown-item,
            .doc-item-mini {
                min-height: 44px;
                padding: 10px 12px;
            }

            .document-open-btn,
            .document-download-btn {
                min-height: 44px;
                padding: 10px 16px;
            }
        }

        /* ============================================================
           CHAT RESPONSIVE - PHONE (max-width: 480px)
           ============================================================ */
        @media screen and (max-width: 480px) {
            .chat-layout {
                height: calc(100vh - 60px);
            }

            .chat-context-panel {
                max-height: 40vh;
            }

            .context-mode-buttons {
                flex-wrap: wrap;
            }

            .mode-btn {
                flex: 1 1 45%;
                font-size: 0.75rem;
                padding: 8px;
            }

            .chat-header {
                padding: 10px 12px;
            }

            .chat-header-left {
                width: 100%;
            }

            .chat-header-right {
                flex-direction: column;
                align-items: stretch;
            }

            .form-label-inline {
                display: none;
            }

            .chat-messages {
                padding: 10px;
            }

            .message {
                max-width: 95%;
            }

            .chat-input-area {
                padding: 10px 12px;
            }

            .chat-input-info {
                flex-direction: column;
                gap: 4px;
                font-size: 0.75rem;
            }

            .document-block {
                padding: 12px;
            }

            .document-block-buttons {
                flex-direction: column;
            }

            .document-open-btn,
            .document-download-btn {
                width: 100%;
                justify-content: center;
            }

            .filter-chip {
                font-size: 0.7rem;
                padding: 2px 6px;
            }
        }
    `;

    document.head.appendChild(styles);
}

// Injetar estilos ao carregar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectChatStyles);
} else {
    injectChatStyles();
}
