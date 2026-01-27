#!/bin/bash

# Prova AI - Script de Inicialização
# ==================================

set -e

echo "🎓 Prova AI - Inicializando..."
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instale Python 3.10+"
    exit 1
fi

# Criar diretórios de dados se não existirem
mkdir -p data/{provas,resolucoes,alunos,correcoes,analises,embeddings,exports}

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado."
    echo "   Copiando de .env.example..."
    cp .env.example .env
    echo "   ⚠️  Edite .env com suas chaves de API antes de continuar!"
    echo ""
fi

# Verificar dependências
echo "📦 Verificando dependências..."
if [ ! -d "venv" ]; then
    echo "   Criando ambiente virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "   Instalando pacotes..."
pip install -q -r requirements.txt

# Carregar variáveis de ambiente
export $(cat .env | xargs)

# Iniciar servidor
echo ""
echo "🚀 Iniciando servidor..."
echo "   Interface: http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "   Pressione Ctrl+C para parar"
echo ""

cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
