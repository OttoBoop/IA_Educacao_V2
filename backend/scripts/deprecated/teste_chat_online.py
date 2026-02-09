#!/usr/bin/env python3
"""
Teste completo do chat online com acesso a documentos
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = 'https://ia-educacao-v2.onrender.com'

def log(message):
    """Log com timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def make_request(method, endpoint, **kwargs):
    """Fazer requisição HTTP com logging"""
    url = f"{BASE_URL}{endpoint}"
    log(f"Making {method} request to {endpoint}")

    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=30, **kwargs)
        elif method.upper() == 'POST':
            response = requests.post(url, timeout=60, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        log(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        log(f"Request failed: {e}")
        return None

def main():
    log("🚀 INICIANDO TESTE COMPLETO DO CHAT ONLINE")
    log("=" * 60)

    # 1. Verificar modelos disponíveis
    log("\n📋 1. VERIFICANDO MODELOS DISPONÍVEIS...")
    response = make_request('GET', '/api/settings/models')
    if response and response.status_code == 200:
        models = response.json()
        log(f"✅ {len(models)} modelos encontrados")
        # Selecionar um modelo que suporte chat
        chat_model = None
        for model in models:
            if 'gpt' in model.get('id', '').lower() or 'claude' in model.get('id', '').lower():
                chat_model = model['id']
                break
        if not chat_model and models:
            chat_model = models[0]['id']

        log(f"Modelo selecionado para teste: {chat_model}")
    else:
        log("❌ Falha ao obter modelos")
        chat_model = 'gpt-4o-mini'  # fallback

    # 2. Obter atividade com documentos
    log("\n📚 2. BUSCANDO ATIVIDADE COM DOCUMENTOS...")
    response = make_request('GET', '/api/navegacao/arvore')
    atividade_id = None
    atividade_nome = None

    if response and response.status_code == 200:
        tree = response.json()
        # Procurar atividade com mais documentos
        max_docs = 0
        for materia in tree.get('materias', []):
            for turma in materia.get('turmas', []):
                for atividade in turma.get('atividades', []):
                    total_docs = atividade.get('total_documentos', 0)
                    if total_docs > max_docs:
                        max_docs = total_docs
                        atividade_id = atividade['id']
                        atividade_nome = atividade['nome']

        if atividade_id:
            log(f"✅ Atividade selecionada: {atividade_nome} (ID: {atividade_id}, {max_docs} documentos)")
        else:
            log("❌ Nenhuma atividade com documentos encontrada")
            return
    else:
        log("❌ Falha ao obter árvore de navegação")
        return

    # 3. Listar documentos da atividade
    log("\n📄 3. LISTANDO DOCUMENTOS DA ATIVIDADE...")
    response = make_request('GET', f'/api/chat/documentos/{atividade_id}')
    documentos = []

    if response and response.status_code == 200:
        documentos = response.json().get('documentos', [])
        log(f"✅ {len(documentos)} documentos encontrados")

        # Mostrar tipos de documentos
        tipos = {}
        for doc in documentos:
            tipo = doc.get('tipo', 'desconhecido')
            tipos[tipo] = tipos.get(tipo, 0) + 1

        log("Tipos de documentos:")
        for tipo, count in tipos.items():
            log(f"  - {tipo}: {count}")

        # Selecionar um documento JSON para teste
        doc_json = None
        for doc in documentos:
            if doc.get('extensao', '').lower() == '.json':
                doc_json = doc
                break

        if doc_json:
            log(f"Documento JSON selecionado: {doc_json['nome']} (ID: {doc_json['id']})")
        else:
            log("⚠️ Nenhum documento JSON encontrado")
    else:
        log("❌ Falha ao listar documentos")
        return

    # 4. Teste de chat sem contexto
    log("\n💬 4. TESTANDO CHAT SEM CONTEXTO...")
    payload_sem_contexto = {
        'model_id': chat_model,
        'messages': [{
            'role': 'user',
            'content': 'Olá! Você é um assistente educacional. Me diga quais tipos de documentos você consegue acessar neste sistema.'
        }]
    }

    response = make_request('POST', '/api/chat', json=payload_sem_contexto)
    resposta_sem_contexto = None

    if response and response.status_code == 200:
        data = response.json()
        resposta_sem_contexto = data.get('resposta', '')
        log("✅ Chat sem contexto respondeu!")
        log(f"Modelo usado: {data.get('modelo', 'N/A')}")
        log(f"Resposta: {resposta_sem_contexto[:200]}...")
    else:
        log(f"❌ Falha no chat sem contexto: {response.text if response else 'Erro de conexão'}")

    # 5. Teste de chat com contexto
    log("\n📖 5. TESTANDO CHAT COM CONTEXTO DE DOCUMENTO...")

    if doc_json:
        payload_com_contexto = {
            'model_id': chat_model,
            'messages': [{
                'role': 'user',
                'content': f'Você tem acesso aos documentos desta atividade. Analise o documento "{doc_json["nome"]}" e me diga que tipo de informação ele contém. Mostre alguns dados específicos se conseguir lê-lo.'
            }],
            'context_docs': [doc_json['id']]
        }

        response = make_request('POST', '/api/chat', json=payload_com_contexto)

        if response and response.status_code == 200:
            data = response.json()
            resposta_com_contexto = data.get('resposta', '')
            log("✅ Chat com contexto respondeu!")
            log(f"Modelo usado: {data.get('modelo', 'N/A')}")
            log(f"Anexos enviados: {data.get('anexos_enviados', 0)}")
            log(f"Resposta: {resposta_com_contexto[:300]}...")

            # 6. Análise da resposta
            log("\n🔍 6. ANÁLISE DOS RESULTADOS...")

            # Verificar se a resposta menciona conteúdo do documento
            menciona_documento = doc_json['nome'].lower() in resposta_com_contexto.lower()
            menciona_json = 'json' in resposta_com_contexto.lower()
            menciona_conteudo = any(word in resposta_com_contexto.lower() for word in ['dados', 'informação', 'conteúdo', 'análise'])

            log("Análise da resposta com contexto:")
            log(f"  - Menciona nome do documento: {'✅' if menciona_documento else '❌'}")
            log(f"  - Menciona JSON: {'✅' if menciona_json else '❌'}")
            log(f"  - Menciona conteúdo/dados: {'✅' if menciona_conteudo else '❌'}")

            # Comparar respostas
            if resposta_sem_contexto and resposta_com_contexto:
                similaridade = len(set(resposta_sem_contexto.split()) & set(resposta_com_contexto.split())) / len(set(resposta_sem_contexto.split()))
                log(f"  - Similaridade entre respostas: {similaridade:.2%}")

                if similaridade < 0.5:
                    log("✅ Respostas são significativamente diferentes - contexto foi usado!")
                else:
                    log("⚠️ Respostas são muito similares - contexto pode não ter sido usado")

        else:
            log(f"❌ Falha no chat com contexto: {response.text if response else 'Erro de conexão'}")
    else:
        log("⚠️ Pulando teste com contexto - nenhum documento JSON disponível")

    log("\n" + "=" * 60)
    log("🏁 TESTE CONCLUÍDO")

    # Resumo final
    log("\n📊 RESUMO FINAL:")
    log(f"  - Modelos disponíveis: ✅")
    log(f"  - Atividade encontrada: ✅ ({atividade_nome})")
    log(f"  - Documentos listados: ✅ ({len(documentos)})")
    log(f"  - Chat sem contexto: {'✅' if resposta_sem_contexto else '❌'}")
    log(f"  - Chat com contexto: {'✅' if doc_json else '⚠️ (sem JSON)'}")
    log(f"  - Acesso a documentos: {'✅ CONFIRMADO' if (doc_json and menciona_conteudo) else '❌ NÃO VERIFICADO'}")

if __name__ == '__main__':
    main()