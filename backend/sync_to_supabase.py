"""
Script para sincronizar arquivos locais com Supabase Storage.

Execute LOCALMENTE (onde os arquivos existem) para enviar para o Supabase.

Uso: python sync_to_supabase.py
"""

import os
import sys
import io
from pathlib import Path

# Corrigir encoding do console Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adicionar backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import storage
from supabase_storage import supabase_storage

def sync_all_documents():
    """Sincroniza todos os documentos do banco de dados para o Supabase"""

    if not supabase_storage.enabled:
        print("ERRO: Supabase não está configurado!")
        print("Configure as variáveis de ambiente:")
        print("  SUPABASE_URL")
        print("  SUPABASE_SERVICE_KEY")
        print("  SUPABASE_BUCKET")
        return

    print(f"Supabase configurado: {supabase_storage.url}")
    print(f"Bucket: {supabase_storage.bucket}")
    print()

    # Listar todas as matérias -> turmas -> atividades -> documentos
    materias = storage.listar_materias()
    total_docs = 0
    uploaded = 0
    failed = 0
    skipped = 0

    for materia in materias:
        print(f"\n📚 Matéria: {materia.nome}")

        turmas = storage.listar_turmas(materia.id)
        for turma in turmas:
            print(f"  📁 Turma: {turma.nome}")

            atividades = storage.listar_atividades(turma.id)
            for atividade in atividades:
                print(f"    📋 Atividade: {atividade.nome}")

                docs = storage.listar_documentos(atividade.id)
                for doc in docs:
                    total_docs += 1

                    # Normalizar caminho
                    caminho_str = doc.caminho_arquivo.replace('\\', '/')
                    if caminho_str.startswith('data/'):
                        remote_path = caminho_str[5:]
                    else:
                        remote_path = caminho_str

                    # Verificar se arquivo existe localmente
                    local_path = storage.base_path / remote_path
                    if not local_path.exists():
                        # Tentar caminho alternativo
                        local_path = Path(doc.caminho_arquivo)
                        if not local_path.exists():
                            print(f"      ⚠️ Arquivo local não encontrado: {doc.nome_arquivo}")
                            skipped += 1
                            continue

                    # Upload para Supabase
                    print(f"      📤 Enviando: {doc.nome_arquivo}...", end=" ")
                    success, msg = supabase_storage.upload(str(local_path), remote_path)

                    if success:
                        print("✅")
                        uploaded += 1
                    else:
                        print(f"❌ {msg}")
                        failed += 1

    print("\n" + "="*50)
    print(f"📊 RESUMO:")
    print(f"   Total de documentos: {total_docs}")
    print(f"   Enviados com sucesso: {uploaded}")
    print(f"   Falhas: {failed}")
    print(f"   Ignorados (arquivo local não existe): {skipped}")
    print("="*50)


if __name__ == "__main__":
    print("="*50)
    print("🔄 SYNC TO SUPABASE")
    print("="*50)
    sync_all_documents()
