"""
=================================================================
SYNC TO REMOTE - Push local database to live server
=================================================================

This script syncs your local SQLite database (materias, turmas,
atividades, alunos, documentos) to the remote Render server via
API calls.

Files should already be in Supabase Storage (run test_data_generator.py first).
This script creates the DATABASE METADATA on the remote server.

Usage: python sync_to_remote.py
       python sync_to_remote.py --dry-run  # Preview only
"""

import sys
import os
import io
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import storage
from models import TipoDocumento

# Remote API base URL
REMOTE_URL = "https://ia-educacao-v2.onrender.com/api"


class RemoteSyncer:
    """Syncs local database to remote server via API"""

    def __init__(self, base_url: str = REMOTE_URL, dry_run: bool = False):
        self.base_url = base_url.rstrip('/')
        self.dry_run = dry_run
        self.stats = {
            "materias": 0,
            "turmas": 0,
            "atividades": 0,
            "alunos": 0,
            "vinculos": 0,
            "documentos": 0,
            "errors": 0
        }
        # Map local IDs to remote IDs
        self.id_map = {
            "materias": {},
            "turmas": {},
            "atividades": {},
            "alunos": {}
        }

    def api_post(self, endpoint: str, data: dict) -> Optional[dict]:
        """POST to remote API"""
        if self.dry_run:
            print(f"  [DRY-RUN] POST {endpoint}: {json.dumps(data, ensure_ascii=False)[:100]}...")
            return {"id": f"dry-run-{len(self.id_map['materias'])}"}

        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ERROR: {e}")
            self.stats["errors"] += 1
            return None

    def api_get(self, endpoint: str) -> Optional[dict]:
        """GET from remote API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ERROR: {e}")
            return None

    def sync_materias(self):
        """Sync all materias to remote"""
        print("\n[+] Syncing Materias...")
        materias = storage.listar_materias()

        for materia in materias:
            data = {
                "nome": materia.nome,
                "descricao": materia.descricao,
                "nivel": materia.nivel.value if hasattr(materia.nivel, 'value') else str(materia.nivel)
            }

            result = self.api_post("materias", data)
            if result and "id" in result:
                self.id_map["materias"][materia.id] = result["id"]
                self.stats["materias"] += 1
                print(f"  [v] {materia.nome}")
            else:
                print(f"  [x] Failed: {materia.nome}")

    def sync_turmas(self):
        """Sync all turmas to remote"""
        print("\n[U] Syncing Turmas...")

        for local_materia_id, remote_materia_id in self.id_map["materias"].items():
            turmas = storage.listar_turmas(local_materia_id)

            for turma in turmas:
                data = {
                    "materia_id": remote_materia_id,
                    "nome": turma.nome,
                    "ano_letivo": turma.ano_letivo,
                    "periodo": turma.periodo
                }

                result = self.api_post("turmas", data)
                if result and "id" in result:
                    self.id_map["turmas"][turma.id] = result["id"]
                    self.stats["turmas"] += 1
                    print(f"  [v] {turma.nome}")
                else:
                    print(f"  [x] Failed: {turma.nome}")

    def sync_alunos(self):
        """Sync all alunos to remote"""
        print("\n[*] Syncing Alunos...")

        # Get all unique alunos from all turmas
        all_alunos = set()
        for local_turma_id in self.id_map["turmas"].keys():
            alunos = storage.listar_alunos(local_turma_id)
            for aluno in alunos:
                all_alunos.add(aluno.id)

        # Sync each unique aluno
        for aluno_id in all_alunos:
            # Get aluno details - need to fetch from storage
            # This is a workaround since we don't have a get_aluno method
            for local_turma_id in self.id_map["turmas"].keys():
                alunos = storage.listar_alunos(local_turma_id)
                for aluno in alunos:
                    if aluno.id == aluno_id and aluno_id not in self.id_map["alunos"]:
                        data = {
                            "nome": aluno.nome,
                            "email": aluno.email,
                            "matricula": aluno.matricula
                        }

                        result = self.api_post("alunos", data)
                        if result and "id" in result:
                            self.id_map["alunos"][aluno.id] = result["id"]
                            self.stats["alunos"] += 1
                            print(f"  [v] {aluno.nome}")
                        else:
                            print(f"  [x] Failed: {aluno.nome}")
                        break

    def sync_vinculos(self):
        """Sync aluno-turma vinculos"""
        print("\n[>] Syncing Vinculos (aluno-turma)...")

        for local_turma_id, remote_turma_id in self.id_map["turmas"].items():
            alunos = storage.listar_alunos(local_turma_id)

            for aluno in alunos:
                remote_aluno_id = self.id_map["alunos"].get(aluno.id)
                if not remote_aluno_id:
                    continue

                data = {
                    "aluno_id": remote_aluno_id,
                    "turma_id": remote_turma_id
                }

                result = self.api_post("vinculos", data)
                if result:
                    self.stats["vinculos"] += 1

    def sync_atividades(self):
        """Sync all atividades to remote"""
        print("\n[>] Syncing Atividades...")

        for local_turma_id, remote_turma_id in self.id_map["turmas"].items():
            atividades = storage.listar_atividades(local_turma_id)

            for atividade in atividades:
                data = {
                    "turma_id": remote_turma_id,
                    "nome": atividade.nome,
                    "tipo": atividade.tipo,
                    "data_aplicacao": atividade.data_aplicacao.isoformat() if atividade.data_aplicacao else None,
                    "nota_maxima": atividade.nota_maxima
                }

                result = self.api_post("atividades", data)
                if result and "id" in result:
                    self.id_map["atividades"][atividade.id] = result["id"]
                    self.stats["atividades"] += 1
                    print(f"  [v] {atividade.nome}")
                else:
                    print(f"  [x] Failed: {atividade.nome}")

    def sync_documentos(self):
        """Sync document metadata to remote (files are already in Supabase)"""
        print("\n[*] Syncing Document Metadata...")

        for local_atividade_id, remote_atividade_id in self.id_map["atividades"].items():
            docs = storage.listar_documentos(local_atividade_id)

            for doc in docs:
                # Get remote aluno_id if applicable
                remote_aluno_id = None
                if doc.aluno_id:
                    remote_aluno_id = self.id_map["alunos"].get(doc.aluno_id)

                data = {
                    "atividade_id": remote_atividade_id,
                    "aluno_id": remote_aluno_id,
                    "tipo": doc.tipo.value if hasattr(doc.tipo, 'value') else str(doc.tipo),
                    "nome_arquivo": doc.nome_arquivo,
                    "caminho_arquivo": doc.caminho_arquivo,
                    "extensao": doc.extensao,
                    "tamanho_bytes": doc.tamanho_bytes,
                    "ia_provider": doc.ia_provider,
                    "ia_modelo": doc.ia_modelo,
                    "status": doc.status
                }

                # Use internal endpoint to create document metadata
                result = self.api_post("documentos/metadata", data)
                if result:
                    self.stats["documentos"] += 1

    def sync_all(self):
        """Run full sync"""
        print("\n" + "=" * 60)
        print("SYNC TO REMOTE - Pushing local database to live server")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Mode: {'DRY-RUN (no changes)' if self.dry_run else 'LIVE'}")

        # Check remote is reachable
        print("\nChecking remote server...")
        result = self.api_get("materias")
        if result is None:
            print("ERROR: Cannot reach remote server!")
            return

        current_count = len(result.get("materias", []))
        print(f"Remote currently has {current_count} materias")

        # Sync in order
        self.sync_materias()
        self.sync_turmas()
        self.sync_alunos()
        self.sync_vinculos()
        self.sync_atividades()
        self.sync_documentos()

        # Report
        print("\n" + "=" * 60)
        print("SYNC COMPLETE")
        print("=" * 60)
        print(f"  Materias:    {self.stats['materias']}")
        print(f"  Turmas:      {self.stats['turmas']}")
        print(f"  Alunos:      {self.stats['alunos']}")
        print(f"  Vinculos:    {self.stats['vinculos']}")
        print(f"  Atividades:  {self.stats['atividades']}")
        print(f"  Documentos:  {self.stats['documentos']}")
        print(f"  Errors:      {self.stats['errors']}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Sync local database to remote server")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no changes")
    parser.add_argument("--url", default=REMOTE_URL, help="Remote API URL")

    args = parser.parse_args()

    syncer = RemoteSyncer(base_url=args.url, dry_run=args.dry_run)
    syncer.sync_all()


if __name__ == "__main__":
    main()
