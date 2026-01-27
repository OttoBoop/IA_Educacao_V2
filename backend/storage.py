"""
Sistema de Armazenamento e Vector Database

Gerencia:
1. Organização de arquivos em pastas estruturadas
2. Vector embeddings para busca semântica
3. Rastreamento de qual IA processou cada documento
4. Metadados de correções e análises
"""

import os
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
import numpy as np
from enum import Enum


class DocumentType(Enum):
    PROVA_ORIGINAL = "prova_original"      # Gabarito do professor
    RESOLUCAO = "resolucao"                 # Resolução/rubrica
    PROVA_ALUNO = "prova_aluno"            # Prova respondida por aluno
    CORRECAO = "correcao"                   # Correção gerada pela IA
    ANALISE = "analise"                     # Análise de habilidades


@dataclass
class Questao:
    """Representa uma questão extraída"""
    id: str
    numero: int
    enunciado: str
    itens: List[Dict[str, str]] = field(default_factory=list)  # [{item: "a", texto: "..."}]
    pontuacao_maxima: float = 0
    habilidades: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentoProcessado:
    """Metadados de um documento processado"""
    id: str
    tipo: DocumentType
    arquivo_original: str
    materia: str
    questoes: List[Questao]
    processado_por: str  # Identificador da IA
    timestamp: datetime
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class Correcao:
    """Resultado da correção de uma questão"""
    id: str
    prova_aluno_id: str
    questao_id: str
    item_id: Optional[str]
    
    resposta_aluno: str
    resposta_esperada: str
    
    nota: float
    nota_maxima: float
    
    feedback: str
    erros_identificados: List[str]
    habilidades_demonstradas: List[str]
    habilidades_faltantes: List[str]
    
    corrigido_por: str  # Identificador da IA
    timestamp: datetime
    
    confianca: float  # 0-1, quão confiante a IA está
    metadata: Dict[str, Any] = field(default_factory=dict)


class StorageManager:
    """Gerencia armazenamento de arquivos e metadados"""
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.db_path = self.base_path / "metadata.db"
        self._setup_directories()
        self._setup_database()
    
    def _setup_directories(self):
        """Cria estrutura de diretórios"""
        dirs = [
            "provas",           # Provas originais (gabaritos)
            "resolucoes",       # Resoluções/rubricas
            "alunos",           # Provas dos alunos (por matéria/turma)
            "correcoes",        # Correções geradas
            "analises",         # Análises agregadas
            "embeddings",       # Vector embeddings
            "exports"           # Exportações finais
        ]
        for d in dirs:
            (self.base_path / d).mkdir(parents=True, exist_ok=True)
    
    def _setup_database(self):
        """Inicializa banco SQLite para metadados"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Tabela de documentos
        c.execute('''
            CREATE TABLE IF NOT EXISTS documentos (
                id TEXT PRIMARY KEY,
                tipo TEXT NOT NULL,
                arquivo_original TEXT NOT NULL,
                materia TEXT NOT NULL,
                processado_por TEXT,
                timestamp TEXT,
                metadata TEXT
            )
        ''')
        
        # Tabela de questões
        c.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id TEXT PRIMARY KEY,
                documento_id TEXT NOT NULL,
                numero INTEGER,
                enunciado TEXT,
                itens TEXT,
                pontuacao_maxima REAL,
                habilidades TEXT,
                metadata TEXT,
                FOREIGN KEY (documento_id) REFERENCES documentos(id)
            )
        ''')
        
        # Tabela de correções
        c.execute('''
            CREATE TABLE IF NOT EXISTS correcoes (
                id TEXT PRIMARY KEY,
                prova_aluno_id TEXT NOT NULL,
                questao_id TEXT NOT NULL,
                item_id TEXT,
                resposta_aluno TEXT,
                resposta_esperada TEXT,
                nota REAL,
                nota_maxima REAL,
                feedback TEXT,
                erros TEXT,
                habilidades_demonstradas TEXT,
                habilidades_faltantes TEXT,
                corrigido_por TEXT,
                timestamp TEXT,
                confianca REAL,
                metadata TEXT,
                FOREIGN KEY (prova_aluno_id) REFERENCES documentos(id),
                FOREIGN KEY (questao_id) REFERENCES questoes(id)
            )
        ''')
        
        # Tabela de embeddings
        c.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                documento_id TEXT,
                questao_id TEXT,
                texto TEXT,
                embedding BLOB,
                modelo TEXT,
                timestamp TEXT,
                FOREIGN KEY (documento_id) REFERENCES documentos(id),
                FOREIGN KEY (questao_id) REFERENCES questoes(id)
            )
        ''')
        
        # Tabela de experimentos (para comparar IAs)
        c.execute('''
            CREATE TABLE IF NOT EXISTS experimentos (
                id TEXT PRIMARY KEY,
                nome TEXT,
                descricao TEXT,
                provider_config TEXT,
                timestamp TEXT,
                resultados TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_id(self, *args) -> str:
        """Gera ID único baseado nos argumentos"""
        content = "_".join(str(a) for a in args) + str(datetime.now().timestamp())
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_path_for_type(self, doc_type: DocumentType, materia: str) -> Path:
        """Retorna o caminho correto para um tipo de documento"""
        type_dirs = {
            DocumentType.PROVA_ORIGINAL: "provas",
            DocumentType.RESOLUCAO: "resolucoes",
            DocumentType.PROVA_ALUNO: "alunos",
            DocumentType.CORRECAO: "correcoes",
            DocumentType.ANALISE: "analises"
        }
        path = self.base_path / type_dirs[doc_type] / materia
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def save_document(self, 
                      file_path: str,
                      doc_type: DocumentType,
                      materia: str,
                      processado_por: str = "manual",
                      metadata: Dict[str, Any] = None) -> str:
        """Salva um documento e retorna seu ID"""
        import shutil
        
        doc_id = self._generate_id(file_path, doc_type.value, materia)
        
        # Copiar arquivo para pasta correta
        dest_dir = self.get_path_for_type(doc_type, materia)
        dest_path = dest_dir / f"{doc_id}_{Path(file_path).name}"
        shutil.copy2(file_path, dest_path)
        
        # Salvar metadados no banco
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO documentos (id, tipo, arquivo_original, materia, processado_por, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            doc_id,
            doc_type.value,
            str(dest_path),
            materia,
            processado_por,
            datetime.now().isoformat(),
            json.dumps(metadata or {})
        ))
        conn.commit()
        conn.close()
        
        return doc_id
    
    def save_questao(self, questao: Questao, documento_id: str) -> str:
        """Salva uma questão extraída"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO questoes (id, documento_id, numero, enunciado, itens, pontuacao_maxima, habilidades, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            questao.id,
            documento_id,
            questao.numero,
            questao.enunciado,
            json.dumps(questao.itens),
            questao.pontuacao_maxima,
            json.dumps(questao.habilidades),
            json.dumps(questao.metadata)
        ))
        conn.commit()
        conn.close()
        return questao.id
    
    def save_correcao(self, correcao: Correcao) -> str:
        """Salva uma correção"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO correcoes (
                id, prova_aluno_id, questao_id, item_id,
                resposta_aluno, resposta_esperada,
                nota, nota_maxima, feedback,
                erros, habilidades_demonstradas, habilidades_faltantes,
                corrigido_por, timestamp, confianca, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            correcao.id,
            correcao.prova_aluno_id,
            correcao.questao_id,
            correcao.item_id,
            correcao.resposta_aluno,
            correcao.resposta_esperada,
            correcao.nota,
            correcao.nota_maxima,
            correcao.feedback,
            json.dumps(correcao.erros_identificados),
            json.dumps(correcao.habilidades_demonstradas),
            json.dumps(correcao.habilidades_faltantes),
            correcao.corrigido_por,
            correcao.timestamp.isoformat(),
            correcao.confianca,
            json.dumps(correcao.metadata)
        ))
        conn.commit()
        conn.close()
        return correcao.id
    
    def get_documento(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Recupera um documento pelo ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM documentos WHERE id = ?', (doc_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "tipo": row[1],
                "arquivo_original": row[2],
                "materia": row[3],
                "processado_por": row[4],
                "timestamp": row[5],
                "metadata": json.loads(row[6]) if row[6] else {}
            }
        return None
    
    def get_questoes_documento(self, doc_id: str) -> List[Questao]:
        """Recupera todas as questões de um documento"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM questoes WHERE documento_id = ? ORDER BY numero', (doc_id,))
        rows = c.fetchall()
        conn.close()
        
        questoes = []
        for row in rows:
            questoes.append(Questao(
                id=row[0],
                numero=row[2],
                enunciado=row[3],
                itens=json.loads(row[4]) if row[4] else [],
                pontuacao_maxima=row[5],
                habilidades=json.loads(row[6]) if row[6] else [],
                metadata=json.loads(row[7]) if row[7] else {}
            ))
        return questoes
    
    def get_correcoes_aluno(self, prova_aluno_id: str) -> List[Correcao]:
        """Recupera todas as correções de uma prova de aluno"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM correcoes WHERE prova_aluno_id = ?', (prova_aluno_id,))
        rows = c.fetchall()
        conn.close()
        
        correcoes = []
        for row in rows:
            correcoes.append(Correcao(
                id=row[0],
                prova_aluno_id=row[1],
                questao_id=row[2],
                item_id=row[3],
                resposta_aluno=row[4],
                resposta_esperada=row[5],
                nota=row[6],
                nota_maxima=row[7],
                feedback=row[8],
                erros_identificados=json.loads(row[9]) if row[9] else [],
                habilidades_demonstradas=json.loads(row[10]) if row[10] else [],
                habilidades_faltantes=json.loads(row[11]) if row[11] else [],
                corrigido_por=row[12],
                timestamp=datetime.fromisoformat(row[13]),
                confianca=row[14],
                metadata=json.loads(row[15]) if row[15] else {}
            ))
        return correcoes
    
    def list_documentos(self, 
                        tipo: Optional[DocumentType] = None,
                        materia: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista documentos com filtros opcionais"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        query = 'SELECT * FROM documentos WHERE 1=1'
        params = []
        
        if tipo:
            query += ' AND tipo = ?'
            params.append(tipo.value)
        if materia:
            query += ' AND materia = ?'
            params.append(materia)
        
        query += ' ORDER BY timestamp DESC'
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        return [{
            "id": row[0],
            "tipo": row[1],
            "arquivo_original": row[2],
            "materia": row[3],
            "processado_por": row[4],
            "timestamp": row[5],
            "metadata": json.loads(row[6]) if row[6] else {}
        } for row in rows]
    
    def list_materias(self) -> List[str]:
        """Lista todas as matérias cadastradas"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT DISTINCT materia FROM documentos ORDER BY materia')
        materias = [row[0] for row in c.fetchall()]
        conn.close()
        return materias
    
    def get_estatisticas_ia(self, provider_id: str) -> Dict[str, Any]:
        """Retorna estatísticas de uso de uma IA específica"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Documentos processados
        c.execute(
            'SELECT COUNT(*) FROM documentos WHERE processado_por = ?',
            (provider_id,)
        )
        docs_count = c.fetchone()[0]
        
        # Correções feitas
        c.execute(
            'SELECT COUNT(*), AVG(confianca), AVG(nota/nota_maxima) FROM correcoes WHERE corrigido_por = ?',
            (provider_id,)
        )
        row = c.fetchone()
        
        conn.close()
        
        return {
            "provider_id": provider_id,
            "documentos_processados": docs_count,
            "correcoes_feitas": row[0] or 0,
            "confianca_media": round(row[1] or 0, 3),
            "nota_media_percentual": round((row[2] or 0) * 100, 1)
        }


class VectorStore:
    """Store para embeddings e busca semântica"""
    
    def __init__(self, storage: StorageManager):
        self.storage = storage
        self.embeddings_path = storage.base_path / "embeddings"
    
    async def create_embedding(self, 
                               text: str, 
                               provider_name: str = "openai") -> List[float]:
        """Cria embedding usando o provider especificado"""
        import httpx
        
        # Por enquanto, só OpenAI embeddings
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "text-embedding-3-small",
                    "input": text
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
        
        return data["data"][0]["embedding"]
    
    async def index_questao(self, 
                            questao: Questao, 
                            documento_id: str) -> str:
        """Indexa uma questão para busca semântica"""
        # Criar texto para embedding
        text = f"Questão {questao.numero}: {questao.enunciado}"
        if questao.itens:
            for item in questao.itens:
                text += f"\n{item.get('item', '')}: {item.get('texto', '')}"
        
        # Gerar embedding
        embedding = await self.create_embedding(text)
        
        # Salvar no banco
        conn = sqlite3.connect(self.storage.db_path)
        c = conn.cursor()
        
        emb_id = self.storage._generate_id(questao.id, "embedding")
        
        c.execute('''
            INSERT OR REPLACE INTO embeddings (id, documento_id, questao_id, texto, embedding, modelo, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            emb_id,
            documento_id,
            questao.id,
            text,
            np.array(embedding).tobytes(),
            "text-embedding-3-small",
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return emb_id
    
    async def search_similar(self, 
                             query: str, 
                             top_k: int = 5,
                             materia: Optional[str] = None) -> List[Tuple[str, float, Dict]]:
        """Busca questões similares à query"""
        # Gerar embedding da query
        query_embedding = np.array(await self.create_embedding(query))
        
        # Buscar todos os embeddings
        conn = sqlite3.connect(self.storage.db_path)
        c = conn.cursor()
        
        if materia:
            c.execute('''
                SELECT e.questao_id, e.texto, e.embedding, d.materia
                FROM embeddings e
                JOIN documentos d ON e.documento_id = d.id
                WHERE d.materia = ?
            ''', (materia,))
        else:
            c.execute('''
                SELECT e.questao_id, e.texto, e.embedding, d.materia
                FROM embeddings e
                JOIN documentos d ON e.documento_id = d.id
            ''')
        
        rows = c.fetchall()
        conn.close()
        
        # Calcular similaridades
        results = []
        for row in rows:
            stored_embedding = np.frombuffer(row[2], dtype=np.float64)
            # Cosine similarity
            similarity = np.dot(query_embedding, stored_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
            )
            results.append((
                row[0],  # questao_id
                float(similarity),
                {"texto": row[1], "materia": row[3]}
            ))
        
        # Ordenar por similaridade e retornar top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


# Instância global
storage = StorageManager()
vector_store = VectorStore(storage)
