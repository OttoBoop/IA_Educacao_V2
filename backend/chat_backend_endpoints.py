# ============================================================
# ENDPOINTS ADICIONAIS PARA O CHAT
# Adicionar estes endpoints ao routes_extras.py ou main_v2.py
# ============================================================

# No início do arquivo, adicionar import se necessário:
# from storage_v2 import storage_v2 as storage

@router.get("/api/documentos/todos", tags=["Chat"])
async def listar_todos_documentos(
    materia_ids: Optional[str] = None,
    turma_ids: Optional[str] = None,
    atividade_ids: Optional[str] = None,
    aluno_ids: Optional[str] = None,
    tipos: Optional[str] = None
):
    """
    Lista todos os documentos do sistema com metadados completos.
    Usado pelo sistema de chat para seleção de contexto.
    
    Parâmetros são listas separadas por vírgula.
    """
    # Parse filters
    filters = {
        'materia_ids': materia_ids.split(',') if materia_ids else None,
        'turma_ids': turma_ids.split(',') if turma_ids else None,
        'atividade_ids': atividade_ids.split(',') if atividade_ids else None,
        'aluno_ids': aluno_ids.split(',') if aluno_ids else None,
        'tipos': tipos.split(',') if tipos else None,
    }
    
    documentos = []
    
    # Buscar todas as matérias
    materias = storage.listar_materias()
    
    for materia in materias:
        # Filtrar por matéria se especificado
        if filters['materia_ids'] and materia.id not in filters['materia_ids']:
            continue
        
        turmas = storage.listar_turmas(materia.id)
        
        for turma in turmas:
            # Filtrar por turma se especificado
            if filters['turma_ids'] and turma.id not in filters['turma_ids']:
                continue
            
            atividades = storage.listar_atividades(turma.id)
            
            for atividade in atividades:
                # Filtrar por atividade se especificado
                if filters['atividade_ids'] and atividade.id not in filters['atividade_ids']:
                    continue
                
                # Buscar documentos da atividade
                docs_atividade = storage.listar_documentos(atividade.id)
                
                for doc in docs_atividade:
                    # Filtrar por tipo se especificado
                    if filters['tipos'] and doc.tipo.value not in filters['tipos']:
                        continue
                    
                    # Filtrar por aluno se especificado
                    if filters['aluno_ids']:
                        # Incluir documentos base (sem aluno) E documentos dos alunos selecionados
                        if doc.aluno_id and doc.aluno_id not in filters['aluno_ids']:
                            continue
                    
                    # Buscar nome do aluno se houver
                    aluno_nome = None
                    if doc.aluno_id:
                        aluno = storage.get_aluno(doc.aluno_id)
                        aluno_nome = aluno.nome if aluno else None
                    
                    documentos.append({
                        "id": doc.id,
                        "nome_arquivo": doc.nome_arquivo,
                        "tipo": doc.tipo.value,
                        "materia_id": materia.id,
                        "materia_nome": materia.nome,
                        "turma_id": turma.id,
                        "turma_nome": turma.nome,
                        "atividade_id": atividade.id,
                        "atividade_nome": atividade.nome,
                        "aluno_id": doc.aluno_id,
                        "aluno_nome": aluno_nome,
                        "criado_em": doc.criado_em.isoformat() if doc.criado_em else None,
                        "ia_provider": doc.ia_provider,
                        "ia_modelo": doc.ia_modelo,
                        "status": doc.status.value if doc.status else None
                    })
    
    return {
        "documentos": documentos,
        "total": len(documentos),
        "filtros_aplicados": {k: v for k, v in filters.items() if v}
    }


# ============================================================
# ENDPOINT DE CHAT ATUALIZADO
# Substituir o endpoint /api/chat existente no main_v2.py
# ============================================================

@app.post("/api/chat", tags=["Chat"])
async def chat_with_ai(request: ChatRequest):
    """
    Chat interativo com a IA, com acesso aos documentos selecionados.
    
    O frontend envia:
    - messages: histórico de mensagens
    - provider: nome do provider a usar
    - context_docs: lista de IDs de documentos para contexto
    """
    try:
        # Verificar se provider foi especificado
        if not request.provider:
            raise HTTPException(400, "Provider não especificado")
        
        # Obter provider
        try:
            provider = ai_registry.get(request.provider)
        except Exception as e:
            raise HTTPException(400, f"Provider '{request.provider}' não encontrado: {str(e)}")
        
        # Montar contexto se documentos especificados
        context = ""
        docs_info = []
        
        if request.context_docs and len(request.context_docs) > 0:
            for doc_id in request.context_docs:
                doc = storage.get_documento(doc_id)
                if not doc:
                    continue
                
                # Tentar ler conteúdo do documento
                conteudo = ""
                try:
                    if doc.caminho_arquivo:
                        arquivo_path = Path(doc.caminho_arquivo)
                        if arquivo_path.exists():
                            if arquivo_path.suffix.lower() == '.json':
                                import json
                                with open(arquivo_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    conteudo = json.dumps(data, indent=2, ensure_ascii=False)
                            elif arquivo_path.suffix.lower() in ['.txt', '.md']:
                                with open(arquivo_path, 'r', encoding='utf-8') as f:
                                    conteudo = f.read()
                            else:
                                conteudo = f"[Arquivo {arquivo_path.suffix}: {doc.nome_arquivo}]"
                except Exception as e:
                    conteudo = f"[Erro ao ler arquivo: {str(e)}]"
                
                # Buscar informações adicionais
                atividade = storage.get_atividade(doc.atividade_id)
                turma = storage.get_turma(atividade.turma_id) if atividade else None
                materia = storage.get_materia(turma.materia_id) if turma else None
                aluno = storage.get_aluno(doc.aluno_id) if doc.aluno_id else None
                
                doc_context = f"""
--- Documento: {doc.nome_arquivo} ---
Tipo: {doc.tipo.value}
Matéria: {materia.nome if materia else 'N/A'}
Turma: {turma.nome if turma else 'N/A'}
Atividade: {atividade.nome if atividade else 'N/A'}
{f"Aluno: {aluno.nome}" if aluno else ""}

Conteúdo:
{conteudo[:5000]}  # Limitar tamanho
{"[... conteúdo truncado ...]" if len(conteudo) > 5000 else ""}
"""
                context += doc_context
                docs_info.append({
                    "id": doc.id,
                    "nome": doc.nome_arquivo,
                    "tipo": doc.tipo.value
                })
        
        # Montar system prompt
        system_prompt = """Você é um assistente especializado em análise e correção de provas educacionais.

Suas responsabilidades incluem:
- Analisar documentos de provas, gabaritos e correções
- Ajudar professores a entender resultados e desempenho dos alunos
- Identificar padrões de erros e dificuldades
- Sugerir melhorias pedagógicas
- Gerar insights sobre o aprendizado

Seja claro, didático e objetivo em suas respostas."""

        if context:
            system_prompt += f"""

═══════════════════════════════════════
DOCUMENTOS DISPONÍVEIS PARA CONSULTA:
═══════════════════════════════════════

{context}

═══════════════════════════════════════

Use as informações acima para responder às perguntas do usuário.
Se precisar de informações que não estão nos documentos, informe que não tem acesso a esses dados."""
        else:
            system_prompt += """

Nenhum documento foi selecionado para contexto.
Você pode responder perguntas gerais sobre educação e avaliação, mas não terá acesso a dados específicos de provas ou alunos."""
        
        # Preparar mensagens para o modelo
        messages_for_ai = []
        
        # Adicionar histórico (limitado aos últimos 10 para não exceder contexto)
        for msg in request.messages[-10:]:
            messages_for_ai.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Última mensagem do usuário
        last_message = request.messages[-1].content if request.messages else ""
        
        # Chamar IA
        import time
        start_time = time.time()
        
        response = await provider.complete(last_message, system_prompt)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return {
            "response": response.content,
            "provider": response.provider,
            "model": response.model,
            "tokens_used": response.tokens_used,
            "latency_ms": latency_ms,
            "context_docs_used": len(docs_info),
            "context_docs_info": docs_info
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Erro no chat: {str(e)}")


# ============================================================
# MODELO PYDANTIC ATUALIZADO
# Verificar se ChatRequest já tem context_docs
# ============================================================

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    provider: Optional[str] = None
    context_docs: Optional[List[str]] = None  # IDs de documentos para contexto
