"""
Sync Service - Sincronização entre servidor local e remoto
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class SyncService:
    """Serviço para sincronizar dados entre servidor local e remoto"""

    def __init__(self, remote_base_url: str = None):
        self.remote_base_url = remote_base_url or os.getenv("REMOTE_SERVER_URL", "https://ia-educacao-v2.onrender.com")
        self.timeout = 30  # segundos

    def _make_request(self, method: str, endpoint: str, data: Any = None, files: Dict = None) -> Dict:
        """Faz uma requisição para o servidor remoto"""
        url = f"{self.remote_base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=self.timeout)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, files=files, data=data, timeout=self.timeout)
                else:
                    response = requests.post(url, json=data, timeout=self.timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")

            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição {method} {endpoint}: {e}")
            raise

    def sync_materia(self, materia_data: Dict) -> Dict:
        """Sincroniza uma matéria para o servidor remoto"""
        logger.info(f"Sincronizando matéria: {materia_data.get('nome', 'Unknown')}")

        # Verificar se já existe
        try:
            existing = self._make_request("GET", f"/api/materias")
            for m in existing.get("materias", []):
                if m["nome"] == materia_data["nome"]:
                    logger.info("Matéria já existe remotamente")
                    return m
        except:
            pass  # Se falhar, continua tentando criar

        # Criar nova matéria
        result = self._make_request("POST", "/api/materias", materia_data)
        logger.info("Matéria sincronizada com sucesso")
        return result.get("materia", {})

    def sync_turma(self, turma_data: Dict) -> Dict:
        """Sincroniza uma turma para o servidor remoto"""
        logger.info(f"Sincronizando turma: {turma_data.get('nome', 'Unknown')}")

        # Verificar se já existe
        try:
            existing = self._make_request("GET", f"/api/turmas?materia_id={turma_data.get('materia_id', '')}")
            for t in existing.get("turmas", []):
                if t["nome"] == turma_data["nome"]:
                    logger.info("Turma já existe remotamente")
                    return t
        except:
            pass

        # Criar nova turma
        result = self._make_request("POST", "/api/turmas", turma_data)
        logger.info("Turma sincronizada com sucesso")
        return result.get("turma", {})

    def sync_aluno(self, aluno_data: Dict) -> Dict:
        """Sincroniza um aluno para o servidor remoto"""
        logger.info(f"Sincronizando aluno: {aluno_data.get('nome', 'Unknown')}")

        # Verificar se já existe (por email ou matricula)
        try:
            existing = self._make_request("GET", "/api/alunos")
            for a in existing.get("alunos", []):
                if (a.get("email") == aluno_data.get("email") and aluno_data.get("email")) or \
                   (a.get("matricula") == aluno_data.get("matricula") and aluno_data.get("matricula")):
                    logger.info("Aluno já existe remotamente")
                    return a
        except:
            pass

        # Criar novo aluno
        result = self._make_request("POST", "/api/alunos", aluno_data)
        logger.info("Aluno sincronizado com sucesso")
        return result.get("aluno", {})

    def sync_documento(self, documento_path: str, metadata: Dict) -> Dict:
        """Sincroniza um documento para o servidor remoto"""
        logger.info(f"Sincronizando documento: {metadata.get('nome_arquivo', 'Unknown')}")

        if not Path(documento_path).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {documento_path}")

        # Preparar dados para upload
        with open(documento_path, 'rb') as f:
            files = {'file': (metadata['nome_arquivo'], f, 'application/octet-stream')}
            data = {
                'atividade_id': metadata.get('atividade_id', ''),
                'aluno_id': metadata.get('aluno_id'),
                'tipo': metadata.get('tipo', 'material_apoio')
            }

            result = self._make_request("POST", "/api/documentos/upload", data=data, files=files)
            logger.info("Documento sincronizado com sucesso")
            return result

    def sync_atividade_completa(self, atividade_id: str, storage) -> Dict:
        """Sincroniza uma atividade completa (matéria, turma, alunos, documentos)"""
        logger.info(f"Sincronizando atividade completa: {atividade_id}")

        # Buscar dados da atividade
        atividade = storage.get_atividade(atividade_id)
        if not atividade:
            raise ValueError(f"Atividade não encontrada: {atividade_id}")

        # Buscar matéria
        materia = storage.get_materia(atividade.materia_id)
        if not materia:
            raise ValueError(f"Matéria não encontrada: {atividade.materia_id}")

        # Buscar turma
        turma = storage.get_turma(atividade.turma_id)
        if not turma:
            raise ValueError(f"Turma não encontrada: {atividade.turma_id}")

        results = {
            "atividade_id": atividade_id,
            "materia": None,
            "turma": None,
            "alunos": [],
            "documentos": []
        }

        try:
            # Sync matéria
            materia_data = {
                "nome": materia.nome,
                "descricao": materia.descricao,
                "nivel": materia.nivel.value if hasattr(materia.nivel, 'value') else str(materia.nivel)
            }
            remote_materia = self.sync_materia(materia_data)
            results["materia"] = remote_materia

            # Sync turma
            turma_data = {
                "materia_id": remote_materia["id"],
                "nome": turma.nome,
                "ano_letivo": turma.ano_letivo,
                "periodo": turma.periodo,
                "descricao": turma.descricao
            }
            remote_turma = self.sync_turma(turma_data)
            results["turma"] = remote_turma

            # Buscar e sync alunos da turma
            alunos_turma = storage.listar_alunos(turma_id=atividade.turma_id)
            for aluno in alunos_turma:
                aluno_data = {
                    "nome": aluno.nome,
                    "email": aluno.email,
                    "matricula": aluno.matricula
                }
                remote_aluno = self.sync_aluno(aluno_data)
                results["alunos"].append(remote_aluno)

                # Vincular aluno à turma remotamente (se houver endpoint)
                # Por enquanto, assumimos que a vinculação é feita automaticamente

            # Buscar e sync documentos
            documentos = storage.listar_documentos(atividade_id=atividade_id)
            for doc in documentos:
                try:
                    doc_metadata = {
                        "nome_arquivo": doc.nome_arquivo,
                        "atividade_id": atividade_id,  # Usar ID local ou remoto?
                        "aluno_id": doc.aluno_id,
                        "tipo": doc.tipo.value if hasattr(doc.tipo, 'value') else str(doc.tipo)
                    }
                    remote_doc = self.sync_documento(doc.caminho_arquivo, doc_metadata)
                    results["documentos"].append(remote_doc)
                except Exception as e:
                    logger.error(f"Erro sincronizando documento {doc.id}: {e}")

            logger.info("Atividade sincronizada com sucesso!")
            return results

        except Exception as e:
            logger.error(f"Erro na sincronização da atividade: {e}")
            raise


# Instância global
sync_service = SyncService()