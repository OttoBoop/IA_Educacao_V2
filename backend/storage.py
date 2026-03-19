"""
NOVO CR - Sistema de Armazenamento Unificado

Gerencia:
1. Banco de dados (PostgreSQL em produção, SQLite em desenvolvimento)
2. Sistema de arquivos organizado por Matéria/Turma/Atividade
3. Metadados de documentos e processamento
4. Verificação de dependências

PERSISTÊNCIA:
- Render tem filesystem efêmero - SQLite é apagado em cada deploy
- Supabase PostgreSQL persiste entre deployments
- Auto-detecta: se SUPABASE_URL configurado, usa PostgreSQL

NOTA: Este arquivo é a unificação de storage.py e storage_v2.py
O antigo storage.py (legado) foi removido em 2026-01-30.
"""

import os
import re
import sqlite3
import hashlib
import shutil
import json
import logging
import time
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from models import (
    Materia, Turma, Aluno, AlunoTurma, Atividade, Documento, Prompt, ResultadoAluno,
    TipoDocumento, StatusProcessamento, NivelEnsino,
    verificar_dependencias, DEPENDENCIAS_DOCUMENTOS
)

# Import Supabase storage (para persistência de arquivos em cloud)
try:
    from supabase_storage import supabase_storage
    SUPABASE_STORAGE_AVAILABLE = supabase_storage.enabled
except ImportError:
    supabase_storage = None
    SUPABASE_STORAGE_AVAILABLE = False

# Import Supabase database (para persistência de dados em PostgreSQL)
try:
    from supabase_db import supabase_db
    SUPABASE_DB_AVAILABLE = supabase_db.enabled
except ImportError:
    supabase_db = None
    SUPABASE_DB_AVAILABLE = False

# Legacy alias for backward compatibility
SUPABASE_AVAILABLE = SUPABASE_STORAGE_AVAILABLE


# Diretório base para paths absolutos (compatível com Render)
BASE_DIR = Path(__file__).parent


# ============================================================
# DISPLAY NAME & FILENAME UTILITIES
# ============================================================

# Human-readable labels for TipoDocumento values
_TIPO_LABELS: Dict[str, str] = {
    "enunciado": "Enunciado",
    "gabarito": "Gabarito",
    "criterios_correcao": "Critérios de Correção",
    "material_apoio": "Material de Apoio",
    "prova_respondida": "Prova Respondida",
    "correcao_professor": "Correção do Professor",
    "extracao_questoes": "Extração de Questões",
    "extracao_gabarito": "Extração de Gabarito",
    "extracao_respostas": "Extração de Respostas",
    "correcao": "Correção",
    "analise_habilidades": "Análise de Habilidades",
    "relatorio_final": "Relatório Final",
    "correcao_narrativa": "Correção Narrativa",
    "analise_habilidades_narrativa": "Análise de Habilidades Narrativa",
    "relatorio_narrativo": "Relatório Narrativo",
    "relatorio_desempenho_tarefa": "Relatório de Desempenho (Tarefa)",
    "relatorio_desempenho_turma": "Relatório de Desempenho (Turma)",
    "relatorio_desempenho_materia": "Relatório de Desempenho (Matéria)",
}

# Characters unsafe for filesystems (/, \, :, *, ?, <, >, |)
_UNSAFE_FILENAME_CHARS = re.compile(r'[/\\:*?<>|]')


def build_display_name(
    tipo: TipoDocumento,
    aluno_nome: Optional[str],
    materia_nome: Optional[str],
    turma_nome: Optional[str],
) -> str:
    """
    Build a structured display name from document metadata.

    Format: "{Tipo Label} - {Aluno} - {Matéria} - {Turma}"
    Parts with None or empty values are omitted.
    """
    label = _TIPO_LABELS.get(tipo.value, tipo.value)
    parts = [label]
    for part in [aluno_nome, materia_nome, turma_nome]:
        if part:
            parts.append(part)
    return " - ".join(parts)


def sanitize_filename(name: str) -> str:
    """
    Strip filesystem-unsafe characters from a filename while keeping Portuguese accents.

    Removes: / \\ : * ? < > |
    Keeps: accented chars (é, ã, ô, ç), spaces, hyphens, underscores
    """
    return _UNSAFE_FILENAME_CHARS.sub("", name)


def build_storage_filename(display_name: str, extension: str) -> str:
    """
    Build a unique storage filename from a display name.

    Returns: '{sanitized_name}_{hash4}.{ext}'
    The 4-char hash suffix guarantees uniqueness for different display names.
    """
    if not extension.startswith("."):
        extension = f".{extension}"
    sanitized = sanitize_filename(display_name)
    hash_suffix = hashlib.md5(display_name.encode("utf-8")).hexdigest()[:4]
    return f"{sanitized}_{hash_suffix}{extension}"


class StorageManager:
    """
    Gerenciador de armazenamento unificado.

    BACKEND:
        - PostgreSQL (Supabase): Usado em produção, persiste entre deploys
        - SQLite: Usado em desenvolvimento local

    Estrutura de diretórios:
        data/
        ├── arquivos/
        │   └── {materia_id}/
        │       └── {turma_id}/
        │           └── {atividade_id}/
        │               ├── _base/           # Documentos da atividade
        │               │   ├── enunciado.pdf
        │               │   ├── gabarito.pdf
        │               │   └── criterios.pdf
        │               │
        │               └── {aluno_id}/      # Documentos do aluno
        │                   ├── prova_respondida.pdf
        │                   ├── extracao_respostas.json
        │                   ├── correcao.json
        │                   └── relatorio.pdf
        │
        └── database.db                      # SQLite (apenas para dev local)
    """

    def __init__(self, base_path: str = None):
        # Usar path absoluto baseado em __file__ para compatibilidade com Render
        if base_path is None:
            base_path = str(BASE_DIR / "data")
        self.base_path = Path(base_path)
        self.arquivos_path = self.base_path / "arquivos"
        self.db_path = self.base_path / "database.db"

        # Determinar backend: PostgreSQL ou SQLite
        self.use_postgresql = SUPABASE_DB_AVAILABLE
        if self.use_postgresql:
            print("[Storage] Usando PostgreSQL (Supabase) - dados persistem entre deploys")
        else:
            print("[Storage] Usando SQLite (local) - AVISO: dados perdidos em deploy no Render")

        self._setup_directories()
        if not self.use_postgresql:
            # SQLite precisa de setup local
            self._setup_database()
    
    # ============================================================
    # SETUP
    # ============================================================
    
    def _setup_directories(self):
        """Cria estrutura base de diretórios"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.arquivos_path.mkdir(parents=True, exist_ok=True)
    
    def _setup_database(self):
        """Inicializa banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Tabela: Matérias
        c.execute('''
            CREATE TABLE IF NOT EXISTS materias (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                descricao TEXT,
                nivel TEXT DEFAULT 'outro',
                criado_em TEXT,
                atualizado_em TEXT,
                metadata TEXT
            )
        ''')
        
        # Tabela: Turmas
        c.execute('''
            CREATE TABLE IF NOT EXISTS turmas (
                id TEXT PRIMARY KEY,
                materia_id TEXT NOT NULL,
                nome TEXT NOT NULL,
                ano_letivo INTEGER,
                periodo TEXT,
                descricao TEXT,
                criado_em TEXT,
                atualizado_em TEXT,
                metadata TEXT,
                FOREIGN KEY (materia_id) REFERENCES materias(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabela: Alunos
        c.execute('''
            CREATE TABLE IF NOT EXISTS alunos (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT,
                matricula TEXT,
                criado_em TEXT,
                atualizado_em TEXT,
                metadata TEXT
            )
        ''')
        
        # Tabela: Vínculo Aluno-Turma (many-to-many)
        c.execute('''
            CREATE TABLE IF NOT EXISTS alunos_turmas (
                id TEXT PRIMARY KEY,
                aluno_id TEXT NOT NULL,
                turma_id TEXT NOT NULL,
                ativo INTEGER DEFAULT 1,
                data_entrada TEXT,
                data_saida TEXT,
                observacoes TEXT,
                FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
                FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE CASCADE,
                UNIQUE(aluno_id, turma_id)
            )
        ''')
        
        # Tabela: Atividades
        c.execute('''
            CREATE TABLE IF NOT EXISTS atividades (
                id TEXT PRIMARY KEY,
                turma_id TEXT NOT NULL,
                nome TEXT NOT NULL,
                tipo TEXT,
                data_aplicacao TEXT,
                data_entrega TEXT,
                peso REAL DEFAULT 1.0,
                nota_maxima REAL DEFAULT 10.0,
                descricao TEXT,
                criado_em TEXT,
                atualizado_em TEXT,
                metadata TEXT,
                FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabela: Documentos
        c.execute('''
            CREATE TABLE IF NOT EXISTS documentos (
                id TEXT PRIMARY KEY,
                tipo TEXT NOT NULL,
                atividade_id TEXT NOT NULL,
                aluno_id TEXT,
                display_name TEXT DEFAULT '',
                nome_arquivo TEXT,
                caminho_arquivo TEXT,
                extensao TEXT,
                tamanho_bytes INTEGER DEFAULT 0,
                ia_provider TEXT,
                ia_modelo TEXT,
                prompt_usado TEXT,
                prompt_versao TEXT,
                tokens_usados INTEGER DEFAULT 0,
                tempo_processamento_ms REAL DEFAULT 0,
                status TEXT DEFAULT 'concluido',
                criado_em TEXT,
                atualizado_em TEXT,
                criado_por TEXT,
                versao INTEGER DEFAULT 1,
                documento_origem_id TEXT,
                metadata TEXT,
                FOREIGN KEY (atividade_id) REFERENCES atividades(id) ON DELETE CASCADE,
                FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE SET NULL
            )
        ''')
        
        # Tabela: Resultados (agregação)
        c.execute('''
            CREATE TABLE IF NOT EXISTS resultados (
                id TEXT PRIMARY KEY,
                aluno_id TEXT NOT NULL,
                atividade_id TEXT NOT NULL,
                nota_obtida REAL,
                nota_maxima REAL DEFAULT 10.0,
                percentual REAL,
                total_questoes INTEGER DEFAULT 0,
                questoes_corretas INTEGER DEFAULT 0,
                questoes_parciais INTEGER DEFAULT 0,
                questoes_incorretas INTEGER DEFAULT 0,
                habilidades_demonstradas TEXT,
                habilidades_faltantes TEXT,
                feedback_geral TEXT,
                corrigido_em TEXT,
                corrigido_por_ia TEXT,
                metadata TEXT,
                FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
                FOREIGN KEY (atividade_id) REFERENCES atividades(id) ON DELETE CASCADE,
                UNIQUE(aluno_id, atividade_id)
            )
        ''')
        
        # Índices para performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_turmas_materia ON turmas(materia_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_atividades_turma ON atividades(turma_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_documentos_atividade ON documentos(atividade_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_documentos_aluno ON documentos(aluno_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_alunos_turmas_aluno ON alunos_turmas(aluno_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_alunos_turmas_turma ON alunos_turmas(turma_id)')
        
        # Migrations for existing databases
        self._run_migrations(c)

        conn.commit()
        conn.close()

    def _run_migrations(self, cursor):
        """Run ALTER TABLE migrations for existing databases."""
        # Check existing columns in documentos table
        cursor.execute("PRAGMA table_info(documentos)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Migration: add display_name column if missing
        if "display_name" not in existing_columns:
            cursor.execute("ALTER TABLE documentos ADD COLUMN display_name TEXT DEFAULT ''")

    # ============================================================
    # UTILITÁRIOS
    # ============================================================
    
    def _generate_id(self, *args) -> str:
        """Gera ID único baseado nos argumentos + timestamp + uuid"""
        import uuid
        content = "_".join(str(a) for a in args) + str(datetime.now().timestamp()) + uuid.uuid4().hex
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_connection(self) -> sqlite3.Connection:
        """Retorna conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _sanitize_filename(self, name: str) -> str:
        """Remove caracteres inválidos de nomes de arquivo"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name

    def _backend_label(self) -> str:
        """Returns the active database backend label."""
        return "postgresql" if self.use_postgresql else "sqlite"

    def _normalize_select_columns(self, columns: Any) -> str:
        """Normalizes select columns into a SQL/Supabase-friendly clause."""
        if not columns:
            return "*"
        if isinstance(columns, str):
            return columns
        return ", ".join(str(column) for column in columns)

    def _build_sql_filter_clause(self, key: str, value: Any) -> Tuple[str, List[Any]]:
        """Builds a SQLite WHERE clause for eq/null/in filters."""
        if isinstance(value, dict):
            if "in" in value:
                value = list(value["in"])
            elif "eq" in value:
                value = value["eq"]
            elif "is" in value:
                value = None if value["is"] == "null" else value["is"]
            else:
                raise ValueError(f"Unsupported filter operator for {key}: {value}")

        if isinstance(value, (list, tuple, set)):
            values = list(value)
            if not values:
                return "0 = 1", []
            placeholders = ", ".join("?" for _ in values)
            return f"{key} IN ({placeholders})", values

        if value is None:
            return f"{key} IS NULL", []

        return f"{key} = ?", [value]

    def _select_rows(self,
                     table: str,
                     filters: Dict[str, Any] = None,
                     order_by: str = None,
                     order_desc: bool = False,
                     limit: int = None,
                     columns: Any = None) -> List[Dict[str, Any]]:
        """Returns raw rows with projection support for both backends."""
        if self.use_postgresql:
            return supabase_db.select(
                table,
                filters=filters,
                order_by=order_by,
                order_desc=order_desc,
                limit=limit,
                columns=columns,
            )

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            query = f"SELECT {self._normalize_select_columns(columns)} FROM {table}"
            params: List[Any] = []
            clauses: List[str] = []

            for key, value in (filters or {}).items():
                clause, clause_params = self._build_sql_filter_clause(key, value)
                clauses.append(clause)
                params.extend(clause_params)

            if clauses:
                query += " WHERE " + " AND ".join(clauses)

            if order_by:
                if any(token in order_by.upper() for token in (" ", ",")):
                    query += f" ORDER BY {order_by}"
                else:
                    direction = " DESC" if order_desc else ""
                    query += f" ORDER BY {order_by}{direction}"

            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _count_rows(self, table: str, filters: Dict[str, Any] = None) -> int:
        """Counts rows with filter support for both backends."""
        if self.use_postgresql:
            return supabase_db.count(table, filters=filters)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            query = f"SELECT COUNT(*) AS total FROM {table}"
            params: List[Any] = []
            clauses: List[str] = []

            for key, value in (filters or {}).items():
                clause, clause_params = self._build_sql_filter_clause(key, value)
                clauses.append(clause)
                params.extend(clause_params)

            if clauses:
                query += " WHERE " + " AND ".join(clauses)

            cursor.execute(query, params)
            row = cursor.fetchone()
            return int(row["total"]) if row else 0
        finally:
            conn.close()

    def _log_hot_endpoint_profile(self,
                                  endpoint: str,
                                  started_at: float,
                                  row_counts: Dict[str, int],
                                  payload_counts: Dict[str, int] = None) -> None:
        """Logs the duration and cardinality of a hot endpoint helper."""
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logging.info(
            "[hot-endpoint] endpoint=%s duration_ms=%.2f backend=%s rows=%s payload=%s",
            endpoint,
            duration_ms,
            self._backend_label(),
            row_counts,
            payload_counts or {},
        )
    
    # ============================================================
    # CRUD: MATÉRIAS
    # ============================================================

    def criar_materia(self, nome: str, descricao: str = None, nivel: NivelEnsino = NivelEnsino.OUTRO) -> Materia:
        """Cria uma nova matéria"""
        existing = self.listar_materias()
        for m in existing:
            if m.nome == nome:
                raise ValueError(f"Já existe uma matéria com o nome '{nome}'")

        materia = Materia(
            id=self._generate_id("materia", nome),
            nome=nome,
            descricao=descricao,
            nivel=nivel
        )

        if self.use_postgresql:
            data = {
                "id": materia.id,
                "nome": materia.nome,
                "descricao": materia.descricao,
                "nivel": materia.nivel.value,
                "criado_em": materia.criado_em.isoformat(),
                "atualizado_em": materia.atualizado_em.isoformat(),
                "metadata": materia.metadata
            }
            supabase_db.insert("materias", data)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO materias (id, nome, descricao, nivel, criado_em, atualizado_em, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                materia.id, materia.nome, materia.descricao, materia.nivel.value,
                materia.criado_em.isoformat(), materia.atualizado_em.isoformat(),
                json.dumps(materia.metadata)
            ))
            conn.commit()
            conn.close()

        # Criar diretório da matéria
        (self.arquivos_path / materia.id).mkdir(exist_ok=True)

        return materia

    def get_materia(self, materia_id: str) -> Optional[Materia]:
        """Busca matéria por ID"""
        if self.use_postgresql:
            row = supabase_db.select_one("materias", materia_id)
            if not row:
                return None
            return Materia.from_dict(row)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM materias WHERE id = ?', (materia_id,))
            row = c.fetchone()
            conn.close()

            if not row:
                return None

            return Materia.from_dict(dict(row))

    def listar_materias(self) -> List[Materia]:
        """Lista todas as matérias"""
        if self.use_postgresql:
            rows = supabase_db.select("materias", order_by="nome")
            return [Materia.from_dict(row) for row in rows]
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM materias ORDER BY nome')
            rows = c.fetchall()
            conn.close()

            return [Materia.from_dict(dict(row)) for row in rows]

    def atualizar_materia(self, materia_id: str, **kwargs) -> Optional[Materia]:
        """Atualiza campos de uma matéria"""
        materia = self.get_materia(materia_id)
        if not materia:
            return None

        campos_permitidos = ['nome', 'descricao', 'nivel', 'metadata']
        update_data = {}

        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                if campo == 'nivel' and isinstance(valor, NivelEnsino):
                    valor = valor.value
                update_data[campo] = valor

        if not update_data:
            return materia

        if self.use_postgresql:
            supabase_db.update("materias", materia_id, update_data)
        else:
            updates = []
            valores = []

            for campo, valor in update_data.items():
                if campo == 'metadata':
                    valor = json.dumps(valor)
                updates.append(f"{campo} = ?")
                valores.append(valor)

            updates.append("atualizado_em = ?")
            valores.append(datetime.now().isoformat())
            valores.append(materia_id)

            conn = self._get_connection()
            c = conn.cursor()
            c.execute(f"UPDATE materias SET {', '.join(updates)} WHERE id = ?", valores)
            conn.commit()
            conn.close()

        return self.get_materia(materia_id)

    def deletar_materia(self, materia_id: str) -> bool:
        """Deleta matéria e todos os dados relacionados"""
        if self.use_postgresql:
            success = supabase_db.delete("materias", materia_id)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('DELETE FROM materias WHERE id = ?', (materia_id,))
            success = c.rowcount > 0
            conn.commit()
            conn.close()

        # Remover diretório
        dir_path = self.arquivos_path / materia_id
        if dir_path.exists():
            shutil.rmtree(dir_path)

        return success

    def cleanup_duplicate_materias(self) -> Dict[str, int]:
        """Remove duplicate matérias (same nome), merging turmas into the survivor.

        For each group of matérias sharing the same nome:
        - Keeps the first one (by ID sort order) as the survivor
        - Reassigns turmas from duplicates to the survivor
        - Deletes the duplicate matéria records

        Returns a report dict: {"duplicates_removed": N, "turmas_reassigned": N}
        """
        materias = self.listar_materias()

        # Group matérias by nome
        by_nome: Dict[str, list] = {}
        for m in materias:
            by_nome.setdefault(m.nome, []).append(m)

        duplicates_removed = 0
        turmas_reassigned = 0

        for nome, group in by_nome.items():
            if len(group) <= 1:
                continue

            # Survivor is the first by ID (deterministic)
            group.sort(key=lambda m: m.id)
            survivor = group[0]
            duplicates = group[1:]

            for dup in duplicates:
                # Reassign turmas from duplicate to survivor
                dup_turmas = self.listar_turmas(materia_id=dup.id)
                for turma in dup_turmas:
                    if self.use_postgresql:
                        supabase_db.update("turmas", turma.id, {"materia_id": survivor.id})
                    else:
                        conn = self._get_connection()
                        c = conn.cursor()
                        c.execute(
                            'UPDATE turmas SET materia_id = ? WHERE id = ?',
                            (survivor.id, turma.id),
                        )
                        conn.commit()
                        conn.close()
                    turmas_reassigned += 1

                # Delete the duplicate matéria
                self.deletar_materia(dup.id)
                duplicates_removed += 1

        return {"duplicates_removed": duplicates_removed, "turmas_reassigned": turmas_reassigned}

    # ============================================================
    # CRUD: TURMAS
    # ============================================================

    def criar_turma(self, materia_id: str, nome: str, ano_letivo: int = None,
                    periodo: str = None, descricao: str = None) -> Optional[Turma]:
        """Cria uma nova turma dentro de uma matéria"""
        if not self.get_materia(materia_id):
            return None

        turma = Turma(
            id=self._generate_id("turma", materia_id, nome),
            materia_id=materia_id,
            nome=nome,
            ano_letivo=ano_letivo,
            periodo=periodo,
            descricao=descricao
        )

        if self.use_postgresql:
            data = {
                "id": turma.id,
                "materia_id": turma.materia_id,
                "nome": turma.nome,
                "ano_letivo": turma.ano_letivo,
                "periodo": turma.periodo,
                "descricao": turma.descricao,
                "criado_em": turma.criado_em.isoformat(),
                "atualizado_em": turma.atualizado_em.isoformat(),
                "metadata": turma.metadata
            }
            supabase_db.insert("turmas", data)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO turmas (id, materia_id, nome, ano_letivo, periodo, descricao, criado_em, atualizado_em, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                turma.id, turma.materia_id, turma.nome, turma.ano_letivo, turma.periodo,
                turma.descricao, turma.criado_em.isoformat(), turma.atualizado_em.isoformat(),
                json.dumps(turma.metadata)
            ))
            conn.commit()
            conn.close()

        # Criar diretório da turma
        (self.arquivos_path / materia_id / turma.id).mkdir(parents=True, exist_ok=True)

        return turma

    def get_turma(self, turma_id: str) -> Optional[Turma]:
        """Busca turma por ID"""
        if self.use_postgresql:
            row = supabase_db.select_one("turmas", turma_id)
            if not row:
                return None
            return Turma.from_dict(row)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM turmas WHERE id = ?', (turma_id,))
            row = c.fetchone()
            conn.close()

            if not row:
                return None

            return Turma.from_dict(dict(row))

    def listar_turmas(self, materia_id: str = None) -> List[Turma]:
        """Lista turmas, opcionalmente filtradas por matéria"""
        if self.use_postgresql:
            filters = {"materia_id": materia_id} if materia_id else None
            rows = supabase_db.select("turmas", filters=filters, order_by="nome")
            return [Turma.from_dict(row) for row in rows]
        else:
            conn = self._get_connection()
            c = conn.cursor()

            if materia_id:
                c.execute('SELECT * FROM turmas WHERE materia_id = ? ORDER BY ano_letivo DESC, nome', (materia_id,))
            else:
                c.execute('SELECT * FROM turmas ORDER BY ano_letivo DESC, nome')

            rows = c.fetchall()
            conn.close()

            return [Turma.from_dict(dict(row)) for row in rows]

    def deletar_turma(self, turma_id: str) -> bool:
        """Deleta turma e todos os dados relacionados"""
        turma = self.get_turma(turma_id)
        if not turma:
            return False

        if self.use_postgresql:
            supabase_db.delete("turmas", turma_id)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('DELETE FROM turmas WHERE id = ?', (turma_id,))
            conn.commit()
            conn.close()

        # Remover diretório
        dir_path = self.arquivos_path / turma.materia_id / turma_id
        if dir_path.exists():
            shutil.rmtree(dir_path)

        return True
    
    # ============================================================
    # CRUD: ALUNOS
    # ============================================================

    def criar_aluno(self, nome: str, email: str = None, matricula: str = None) -> Aluno:
        """Cria um novo aluno"""
        aluno = Aluno(
            id=self._generate_id("aluno", nome, matricula or ""),
            nome=nome,
            email=email,
            matricula=matricula
        )

        if self.use_postgresql:
            data = {
                "id": aluno.id,
                "nome": aluno.nome,
                "email": aluno.email,
                "matricula": aluno.matricula,
                "criado_em": aluno.criado_em.isoformat(),
                "atualizado_em": aluno.atualizado_em.isoformat(),
                "metadata": aluno.metadata
            }
            supabase_db.insert("alunos", data)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO alunos (id, nome, email, matricula, criado_em, atualizado_em, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                aluno.id, aluno.nome, aluno.email, aluno.matricula,
                aluno.criado_em.isoformat(), aluno.atualizado_em.isoformat(),
                json.dumps(aluno.metadata)
            ))
            conn.commit()
            conn.close()

        return aluno

    def get_aluno(self, aluno_id: str) -> Optional[Aluno]:
        """Busca aluno por ID"""
        if self.use_postgresql:
            row = supabase_db.select_one("alunos", aluno_id)
            if not row:
                return None
            return Aluno.from_dict(row)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM alunos WHERE id = ?', (aluno_id,))
            row = c.fetchone()
            conn.close()

            if not row:
                return None

            return Aluno.from_dict(dict(row))

    def listar_alunos(self, turma_id: str = None) -> List[Aluno]:
        """Lista alunos, opcionalmente filtrados por turma"""
        if self.use_postgresql:
            if turma_id:
                vinculos = self._select_rows(
                    "alunos_turmas",
                    filters={"turma_id": turma_id, "ativo": True},
                    columns=["aluno_id"],
                )
                aluno_ids = [v["aluno_id"] for v in vinculos]
                if not aluno_ids:
                    return []
                rows = self._select_rows("alunos", filters={"id": aluno_ids}, order_by="nome")
                return [Aluno.from_dict(row) for row in rows]

            rows = self._select_rows("alunos", order_by="nome")
            return [Aluno.from_dict(row) for row in rows]
        else:
            conn = self._get_connection()
            c = conn.cursor()

            if turma_id:
                c.execute('''
                    SELECT a.* FROM alunos a
                    JOIN alunos_turmas at ON a.id = at.aluno_id
                    WHERE at.turma_id = ? AND at.ativo = 1
                    ORDER BY a.nome
                ''', (turma_id,))
            else:
                c.execute('SELECT * FROM alunos ORDER BY nome')

            rows = c.fetchall()
            conn.close()

            return [Aluno.from_dict(dict(row)) for row in rows]

    def deletar_aluno(self, aluno_id: str) -> bool:
        """Deleta um aluno e todos os seus vínculos"""
        aluno = self.get_aluno(aluno_id)
        if not aluno:
            return False

        if self.use_postgresql:
            # CASCADE should handle related records, but be explicit
            supabase_db.delete_where("alunos_turmas", {"aluno_id": aluno_id})
            supabase_db.delete_where("documentos", {"aluno_id": aluno_id})
            supabase_db.delete_where("resultados", {"aluno_id": aluno_id})
            supabase_db.delete("alunos", aluno_id)
            return True
        else:
            conn = self._get_connection()
            c = conn.cursor()

            # Remove vínculos com turmas
            c.execute('DELETE FROM alunos_turmas WHERE aluno_id = ?', (aluno_id,))

            # Remove documentos do aluno (opcional: pode querer manter)
            c.execute('DELETE FROM documentos WHERE aluno_id = ?', (aluno_id,))

            # Remove resultados
            c.execute('DELETE FROM resultados WHERE aluno_id = ?', (aluno_id,))

            # Remove o aluno
            c.execute('DELETE FROM alunos WHERE id = ?', (aluno_id,))
            affected = c.rowcount

            conn.commit()
            conn.close()

            return affected > 0

    def atualizar_aluno(self, aluno_id: str, **kwargs) -> Optional[Aluno]:
        """Atualiza campos de um aluno"""
        aluno = self.get_aluno(aluno_id)
        if not aluno:
            return None

        campos_permitidos = ['nome', 'email', 'matricula', 'metadata']
        update_data = {}

        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                update_data[campo] = valor

        if not update_data:
            return aluno

        if self.use_postgresql:
            supabase_db.update("alunos", aluno_id, update_data)
        else:
            updates = []
            valores = []

            for campo, valor in update_data.items():
                if campo == 'metadata':
                    valor = json.dumps(valor)
                updates.append(f"{campo} = ?")
                valores.append(valor)

            updates.append("atualizado_em = ?")
            valores.append(datetime.now().isoformat())
            valores.append(aluno_id)

            conn = self._get_connection()
            c = conn.cursor()
            c.execute(f"UPDATE alunos SET {', '.join(updates)} WHERE id = ?", valores)
            conn.commit()
            conn.close()

        return self.get_aluno(aluno_id)

    def vincular_aluno_turma(self, aluno_id: str, turma_id: str, observacoes: str = None) -> Optional[AlunoTurma]:
        """Vincula um aluno a uma turma"""
        if not self.get_aluno(aluno_id) or not self.get_turma(turma_id):
            return None

        vinculo = AlunoTurma(
            id=self._generate_id("vinculo", aluno_id, turma_id),
            aluno_id=aluno_id,
            turma_id=turma_id,
            observacoes=observacoes
        )

        if self.use_postgresql:
            data = {
                "id": vinculo.id,
                "aluno_id": vinculo.aluno_id,
                "turma_id": vinculo.turma_id,
                "ativo": True,
                "data_entrada": vinculo.data_entrada.isoformat(),
                "observacoes": vinculo.observacoes
            }
            result = supabase_db.insert("alunos_turmas", data)
            if not result:
                return None  # Likely duplicate
        else:
            conn = self._get_connection()
            c = conn.cursor()

            try:
                c.execute('''
                    INSERT INTO alunos_turmas (id, aluno_id, turma_id, ativo, data_entrada, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    vinculo.id, vinculo.aluno_id, vinculo.turma_id,
                    1, vinculo.data_entrada.isoformat(), vinculo.observacoes
                ))
                conn.commit()
            except sqlite3.IntegrityError:
                # Vínculo já existe
                conn.close()
                return None

            conn.close()

        return vinculo

    def desvincular_aluno_turma(self, aluno_id: str, turma_id: str) -> bool:
        """Remove vínculo aluno-turma (soft delete)"""
        if self.use_postgresql:
            # Find the vinculo and update it
            vinculos = supabase_db.select("alunos_turmas",
                filters={"aluno_id": aluno_id, "turma_id": turma_id})
            if vinculos:
                supabase_db.update("alunos_turmas", vinculos[0]["id"], {
                    "ativo": False,
                    "data_saida": datetime.now().isoformat()
                })
                return True
            return False
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('''
                UPDATE alunos_turmas
                SET ativo = 0, data_saida = ?
                WHERE aluno_id = ? AND turma_id = ?
            ''', (datetime.now().isoformat(), aluno_id, turma_id))
            affected = c.rowcount
            conn.commit()
            conn.close()
            return affected > 0

    def get_turmas_do_aluno(self, aluno_id: str, apenas_ativas: bool = True) -> List[Dict[str, Any]]:
        """Retorna todas as turmas de um aluno, com info da matéria, sem N+1."""
        filters = {"aluno_id": aluno_id}
        if apenas_ativas:
            filters["ativo"] = True

        vinculos = self._select_rows(
            "alunos_turmas",
            filters=filters,
            columns=["turma_id", "observacoes", "data_entrada"],
        )
        turma_ids = [v["turma_id"] for v in vinculos]
        if not turma_ids:
            return []

        turmas_rows = self._select_rows("turmas", filters={"id": turma_ids})
        turmas_by_id = {turma["id"]: turma for turma in turmas_rows}
        materia_ids = list({turma["materia_id"] for turma in turmas_rows if turma.get("materia_id")})
        materias_rows = (
            self._select_rows("materias", filters={"id": materia_ids}, columns=["id", "nome"])
            if materia_ids
            else []
        )
        materias_by_id = {materia["id"]: materia["nome"] for materia in materias_rows}

        result = []
        for vinculo in vinculos:
            turma = turmas_by_id.get(vinculo["turma_id"])
            if not turma:
                continue

            turma_dict = dict(turma)
            turma_dict["materia_nome"] = materias_by_id.get(turma.get("materia_id"), "")
            turma_dict["observacoes"] = vinculo.get("observacoes")
            turma_dict["data_entrada"] = vinculo.get("data_entrada")
            result.append(turma_dict)

        result.sort(
            key=lambda turma: (
                (turma.get("materia_nome") or "").lower(),
                -(turma.get("ano_letivo") or 0),
                (turma.get("nome") or "").lower(),
            )
        )
        return result

    def get_aluno_detalhes_fast(self, aluno_id: str) -> Optional[Dict[str, Any]]:
        """Retorna o payload de /api/alunos/{id} com leituras em lote."""
        started_at = time.perf_counter()
        aluno = self.get_aluno(aluno_id)
        if not aluno:
            return None

        turmas = self.get_turmas_do_aluno(aluno_id)
        payload = {
            "aluno": aluno.to_dict(),
            "turmas": turmas,
            "total_turmas": len(turmas),
        }
        self._log_hot_endpoint_profile(
            "/api/alunos/{id}",
            started_at,
            {
                "alunos": 1,
                "turmas": len(turmas),
            },
            {"total_turmas": len(turmas)},
        )
        return payload
    
    # ============================================================
    # CRUD: ATIVIDADES
    # ============================================================

    def criar_atividade(self, turma_id: str, nome: str, tipo: str = None,
                        data_aplicacao: datetime = None, nota_maxima: float = 10.0,
                        descricao: str = None) -> Optional[Atividade]:
        """Cria uma nova atividade dentro de uma turma"""
        turma = self.get_turma(turma_id)
        if not turma:
            return None

        atividade = Atividade(
            id=self._generate_id("atividade", turma_id, nome),
            turma_id=turma_id,
            nome=nome,
            tipo=tipo,
            data_aplicacao=data_aplicacao,
            nota_maxima=nota_maxima,
            descricao=descricao
        )

        if self.use_postgresql:
            data = {
                "id": atividade.id,
                "turma_id": atividade.turma_id,
                "nome": atividade.nome,
                "tipo": atividade.tipo,
                "data_aplicacao": atividade.data_aplicacao.isoformat() if atividade.data_aplicacao else None,
                "data_entrega": atividade.data_entrega.isoformat() if atividade.data_entrega else None,
                "peso": atividade.peso,
                "nota_maxima": atividade.nota_maxima,
                "descricao": atividade.descricao,
                "criado_em": atividade.criado_em.isoformat(),
                "atualizado_em": atividade.atualizado_em.isoformat(),
                "metadata": atividade.metadata
            }
            supabase_db.insert("atividades", data)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO atividades (id, turma_id, nome, tipo, data_aplicacao, data_entrega, peso, nota_maxima, descricao, criado_em, atualizado_em, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                atividade.id, atividade.turma_id, atividade.nome, atividade.tipo,
                atividade.data_aplicacao.isoformat() if atividade.data_aplicacao else None,
                atividade.data_entrega.isoformat() if atividade.data_entrega else None,
                atividade.peso, atividade.nota_maxima, atividade.descricao,
                atividade.criado_em.isoformat(), atividade.atualizado_em.isoformat(),
                json.dumps(atividade.metadata)
            ))
            conn.commit()
            conn.close()

        # Criar diretório da atividade
        materia_id = turma.materia_id
        ativ_path = self.arquivos_path / materia_id / turma_id / atividade.id
        ativ_path.mkdir(parents=True, exist_ok=True)
        (ativ_path / "_base").mkdir(exist_ok=True)  # Pasta para documentos base

        return atividade

    def get_atividade(self, atividade_id: str) -> Optional[Atividade]:
        """Busca atividade por ID"""
        if self.use_postgresql:
            row = supabase_db.select_one("atividades", atividade_id)
            if not row:
                return None
            return Atividade.from_dict(row)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM atividades WHERE id = ?', (atividade_id,))
            row = c.fetchone()
            conn.close()

            if not row:
                return None

            return Atividade.from_dict(dict(row))

    def listar_atividades(self, turma_id: str) -> List[Atividade]:
        """Lista atividades de uma turma"""
        if self.use_postgresql:
            rows = supabase_db.select("atividades", filters={"turma_id": turma_id}, order_by="nome")
            return [Atividade.from_dict(row) for row in rows]
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM atividades WHERE turma_id = ? ORDER BY data_aplicacao DESC, nome', (turma_id,))
            rows = c.fetchall()
            conn.close()

            return [Atividade.from_dict(dict(row)) for row in rows]

    def deletar_atividade(self, atividade_id: str) -> bool:
        """Deleta atividade e todos os documentos"""
        atividade = self.get_atividade(atividade_id)
        if not atividade:
            return False

        turma = self.get_turma(atividade.turma_id)

        if self.use_postgresql:
            supabase_db.delete("atividades", atividade_id)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('DELETE FROM atividades WHERE id = ?', (atividade_id,))
            conn.commit()
            conn.close()

        # Remover diretório
        if turma:
            dir_path = self.arquivos_path / turma.materia_id / turma.id / atividade_id
            if dir_path.exists():
                shutil.rmtree(dir_path)

        return True
    
    # ============================================================
    # CRUD: DOCUMENTOS
    # ============================================================
    
    def _get_caminho_documento(self, atividade: Atividade, tipo: TipoDocumento,
                                aluno_id: str = None, nome_arquivo: str = "") -> Path:
        """Calcula o caminho onde o documento deve ser salvo"""
        turma = self.get_turma(atividade.turma_id)
        base = self.arquivos_path / turma.materia_id / turma.id / atividade.id

        # Documentos que não precisam de aluno ficam em _base/
        # Isso inclui: enunciado, gabarito, extracao_questoes, extracao_gabarito
        if tipo in TipoDocumento.documentos_sem_aluno():
            base_dir = base / "_base"
            base_dir.mkdir(parents=True, exist_ok=True)
            return base_dir / nome_arquivo
        else:
            # Documentos de aluno ficam em {aluno_id}/
            if not aluno_id:
                raise ValueError("Documentos de aluno precisam de aluno_id")
            aluno_dir = base / aluno_id
            aluno_dir.mkdir(parents=True, exist_ok=True)
            return aluno_dir / nome_arquivo
    
    def salvar_documento(self,
                         arquivo_origem: str,
                         tipo: TipoDocumento,
                         atividade_id: str,
                         aluno_id: str = None,
                         display_name: str = None,
                         ia_provider: str = None,
                         ia_modelo: str = None,
                         prompt_usado: str = None,
                         criado_por: str = "usuario",
                         versao: int = 1,
                         documento_origem_id: str = None) -> Optional[Documento]:
        """
        Salva um documento no sistema.

        Args:
            arquivo_origem: Caminho do arquivo a ser copiado
            tipo: Tipo do documento
            atividade_id: ID da atividade
            aluno_id: ID do aluno (obrigatório para docs de aluno/gerados)
            display_name: Nome de exibição (auto-gerado se não fornecido)
            ia_provider: Provider da IA (para docs gerados)
            ia_modelo: Modelo da IA (para docs gerados)
            prompt_usado: Prompt utilizado (para docs gerados)
            criado_por: Quem criou o documento
            versao: Número da versão (1 = original, 2+ = re-processado)
            documento_origem_id: ID do documento original se for versão > 1
        """
        atividade = self.get_atividade(atividade_id)
        if not atividade:
            raise ValueError(f"Atividade não encontrada: {atividade_id}")

        # Validar aluno_id para documentos que precisam
        if tipo not in TipoDocumento.documentos_sem_aluno() and not aluno_id:
            raise ValueError(f"Tipo {tipo.value} requer aluno_id")

        # Validar se aluno existe e está na turma
        aluno = None
        if aluno_id:
            aluno = self.get_aluno(aluno_id)
            if not aluno:
                raise ValueError(f"Aluno não encontrado: {aluno_id}")

        # Info do arquivo
        arquivo_path = Path(arquivo_origem)
        nome_original = arquivo_path.name
        extensao = arquivo_path.suffix
        tamanho = arquivo_path.stat().st_size if arquivo_path.exists() else 0

        # Auto-generate display_name from metadata when not provided
        if display_name is None:
            turma = self.get_turma(atividade.turma_id) if atividade.turma_id else None
            materia = self.get_materia(turma.materia_id) if turma and turma.materia_id else None
            display_name = build_display_name(
                tipo=tipo,
                aluno_nome=aluno.nome if aluno else None,
                materia_nome=materia.nome if materia else None,
                turma_nome=turma.nome if turma else None,
            )

        # Gerar nome único para o arquivo usando display_name
        nome_arquivo = build_storage_filename(display_name, extensao)

        # Calcular destino
        destino = self._get_caminho_documento(atividade, tipo, aluno_id, nome_arquivo)
        destino.parent.mkdir(parents=True, exist_ok=True)

        # Copiar arquivo
        shutil.copy2(arquivo_origem, destino)

        # Calcular caminho relativo para compatibilidade cross-platform
        caminho_relativo = destino.relative_to(self.base_path)

        # Criar registro
        documento = Documento(
            id=self._generate_id("doc", atividade_id, tipo.value, aluno_id or "base"),
            tipo=tipo,
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            display_name=display_name,
            nome_arquivo=nome_arquivo,
            caminho_arquivo=str(caminho_relativo),
            extensao=extensao,
            tamanho_bytes=tamanho,
            ia_provider=ia_provider,
            ia_modelo=ia_modelo,
            prompt_usado=prompt_usado,
            criado_por=criado_por,
            versao=versao,
            documento_origem_id=documento_origem_id
        )

        if self.use_postgresql:
            data = {
                "id": documento.id,
                "tipo": documento.tipo.value,
                "atividade_id": documento.atividade_id,
                "aluno_id": documento.aluno_id,
                "display_name": documento.display_name,
                "nome_arquivo": documento.nome_arquivo,
                "caminho_arquivo": documento.caminho_arquivo,
                "extensao": documento.extensao,
                "tamanho_bytes": documento.tamanho_bytes,
                "ia_provider": documento.ia_provider,
                "ia_modelo": documento.ia_modelo,
                "prompt_usado": documento.prompt_usado,
                "prompt_versao": documento.prompt_versao,
                "tokens_usados": documento.tokens_usados,
                "tempo_processamento_ms": documento.tempo_processamento_ms,
                "status": documento.status.value,
                "criado_em": documento.criado_em.isoformat(),
                "atualizado_em": documento.atualizado_em.isoformat(),
                "criado_por": documento.criado_por,
                "versao": documento.versao,
                "documento_origem_id": documento.documento_origem_id,
                "metadata": documento.metadata
            }
            result = supabase_db.insert("documentos", data)
            if result is None:
                import logging
                logger = logging.getLogger("storage")
                logger.error(f"[SupabaseDB] Failed to insert documento {documento.id} into Supabase. Data keys: {list(data.keys())}")
                raise RuntimeError(f"Failed to insert documento {documento.id} into Supabase DB - insert returned None")
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO documentos (
                    id, tipo, atividade_id, aluno_id, display_name,
                    nome_arquivo, caminho_arquivo, extensao,
                    tamanho_bytes, ia_provider, ia_modelo, prompt_usado, prompt_versao,
                    tokens_usados, tempo_processamento_ms, status, criado_em, atualizado_em,
                    criado_por, versao, documento_origem_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                documento.id, documento.tipo.value, documento.atividade_id, documento.aluno_id,
                documento.display_name,
                documento.nome_arquivo, documento.caminho_arquivo, documento.extensao,
                documento.tamanho_bytes, documento.ia_provider, documento.ia_modelo,
                documento.prompt_usado, documento.prompt_versao, documento.tokens_usados,
                documento.tempo_processamento_ms, documento.status.value,
                documento.criado_em.isoformat(), documento.atualizado_em.isoformat(),
                documento.criado_por, documento.versao, documento.documento_origem_id,
                json.dumps(documento.metadata)
            ))
            conn.commit()
            conn.close()

        # Upload para Supabase Storage (persistência de arquivos em cloud)
        if SUPABASE_STORAGE_AVAILABLE and supabase_storage:
            remote_path = str(caminho_relativo).replace("\\", "/")
            success, msg = supabase_storage.upload(str(destino), remote_path)
            if success:
                print(f"[Supabase] Upload OK: {remote_path}")
            else:
                print(f"[Supabase] ERRO Upload: {msg}")
                import logging
                logging.getLogger("storage").error(f"[Supabase] Storage upload failed for {remote_path}: {msg}")

        return documento

    def get_documento(self, documento_id: str) -> Optional[Documento]:
        """Busca documento por ID"""
        if self.use_postgresql:
            row = supabase_db.select_one("documentos", documento_id)
            if not row:
                return None
            return Documento.from_dict(row)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM documentos WHERE id = ?', (documento_id,))
            row = c.fetchone()
            conn.close()

            if not row:
                return None

            return Documento.from_dict(dict(row))

    def resolver_caminho_documento(self, documento: Documento, force_remote: bool = False) -> Path:
        """
        Resolve o caminho absoluto de um documento.

        Usa cache local primeiro e só baixa do Supabase quando necessário.
        """
        logger = logging.getLogger("pipeline")

        # Normalizar: converter barras invertidas para barras normais
        caminho_str = documento.caminho_arquivo.replace('\\', '/')

        # Normalizar caminho remoto (remover 'data/' se existir)
        remote_path = caminho_str
        if remote_path.startswith('data/'):
            remote_path = remote_path[5:]

        # Definir caminho local para salvar
        local_path = self.base_path / remote_path

        logger.info(f"[resolver_caminho] Doc: {documento.id} | Nome: {documento.nome_arquivo}")
        logger.info(f"[resolver_caminho] caminho_arquivo (BD): {documento.caminho_arquivo}")
        logger.info(f"[resolver_caminho] remote_path: {remote_path}")
        logger.info(f"[resolver_caminho] local_path: {local_path}")
        logger.info(f"[resolver_caminho] SUPABASE_AVAILABLE: {SUPABASE_AVAILABLE}")
        logger.info(f"[resolver_caminho] supabase_storage.enabled: {supabase_storage.enabled if supabase_storage else 'None'}")

        if local_path.exists() and not force_remote:
            logger.info(f"[resolver_caminho] Cache local hit: {local_path}")
            return local_path

        if SUPABASE_AVAILABLE and supabase_storage and supabase_storage.enabled:
            logger.info(f"[resolver_caminho] Cache miss, tentando Supabase...")

            # Criar diretório pai se não existir
            local_path.parent.mkdir(parents=True, exist_ok=True)

            success, msg = supabase_storage.download(remote_path, str(local_path))

            if success:
                logger.info(f"[resolver_caminho] Supabase OK: {local_path}")
                return local_path
            else:
                logger.warning(f"[resolver_caminho] Supabase falhou: {msg}")

                # Tentar também com prefixo 'arquivos/' se não tiver
                if not remote_path.startswith('arquivos/'):
                    alt_path = f"arquivos/{remote_path}"
                    logger.info(f"[resolver_caminho] Tentando caminho alternativo: {alt_path}")
                    success2, msg2 = supabase_storage.download(alt_path, str(local_path))
                    if success2:
                        logger.info(f"[resolver_caminho] Supabase OK (alt): {local_path}")
                        return local_path
                    else:
                        logger.warning(f"[resolver_caminho] Supabase (alt) falhou: {msg2}")
        else:
            logger.warning(f"[resolver_caminho] Supabase não disponível!")

        if local_path.exists():
            logger.info(f"[resolver_caminho] Usando cache local: {local_path}")
            return local_path

        logger.error(f"[resolver_caminho] ERRO: Arquivo não encontrado em lugar nenhum!")
        return local_path
    
    def listar_documentos(self, atividade_id: str, aluno_id: str = None,
                          tipo: TipoDocumento = None) -> List[Documento]:
        """Lista documentos com filtros"""
        if self.use_postgresql:
            filters = {"atividade_id": atividade_id}
            if tipo:
                filters["tipo"] = tipo.value

            if aluno_id is None:
                rows = self._select_rows(
                    "documentos",
                    filters=filters,
                    order_by="criado_em",
                    order_desc=True,
                )
            else:
                rows_by_id: Dict[str, Dict[str, Any]] = {}
                for query_filters in (
                    {**filters, "aluno_id": aluno_id},
                    {**filters, "aluno_id": None},
                ):
                    for row in self._select_rows(
                        "documentos",
                        filters=query_filters,
                        order_by="criado_em",
                        order_desc=True,
                    ):
                        rows_by_id[row["id"]] = row

                rows = sorted(
                    rows_by_id.values(),
                    key=lambda row: row.get("criado_em") or "",
                    reverse=True,
                )
            return [Documento.from_dict(row) for row in rows]
        else:
            conn = self._get_connection()
            c = conn.cursor()

            query = 'SELECT * FROM documentos WHERE atividade_id = ?'
            params = [atividade_id]

            if aluno_id is not None:
                query += ' AND (aluno_id = ? OR aluno_id IS NULL)'
                params.append(aluno_id)

            if tipo:
                query += ' AND tipo = ?'
                params.append(tipo.value)

            query += ' ORDER BY criado_em DESC'

            c.execute(query, params)
            rows = c.fetchall()
            conn.close()

            return [Documento.from_dict(dict(row)) for row in rows]

    def deletar_documento(self, documento_id: str) -> bool:
        """Deleta documento do banco e do sistema de arquivos (local e cloud)"""
        doc = self.get_documento(documento_id)
        if not doc:
            return False

        # Remover arquivo local
        if doc.caminho_arquivo:
            arquivo = self.resolver_caminho_documento(doc)
            if arquivo.exists():
                arquivo.unlink()

            # Remover do Supabase Storage também
            if SUPABASE_STORAGE_AVAILABLE and supabase_storage:
                remote_path = str(doc.caminho_arquivo).replace("\\", "/")
                if remote_path.startswith('data/'):
                    remote_path = remote_path[5:]
                success, msg = supabase_storage.delete(remote_path)
                if success:
                    print(f"[Supabase] Deletado: {remote_path}")

        # Remover do banco
        if self.use_postgresql:
            supabase_db.delete("documentos", documento_id)
        else:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('DELETE FROM documentos WHERE id = ?', (documento_id,))
            conn.commit()
            conn.close()

        return True

    def deletar_documentos_aluno_atividade(self, atividade_id: str, aluno_id: str) -> int:
        """Deleta todos os documentos de um aluno em uma atividade específica"""
        rows = self._select_rows(
            "documentos",
            filters={"atividade_id": atividade_id, "aluno_id": aluno_id},
            columns=["id"],
        )

        count = 0
        for row in rows:
            if self.deletar_documento(row["id"]):
                count += 1

        return count

    def excluir_documentos_ai_aluno_atividade(self, atividade_id: str, aluno_id: str) -> int:
        """Deleta apenas os documentos gerados por IA de um aluno em uma atividade específica"""
        ai_types = ['extracao_questoes', 'extracao_gabarito', 'extracao_respostas', 'correcao', 'analise_habilidades', 'relatorio_final']
        rows = self._select_rows(
            "documentos",
            filters={"atividade_id": atividade_id, "aluno_id": aluno_id},
            columns=["id", "tipo", "ia_provider"],
        )

        count = 0
        for row in rows:
            if row.get("ia_provider") or row.get("tipo") in ai_types:
                if self.deletar_documento(row["id"]):
                    count += 1

        return count

    def resetar_extracoes_questoes_aluno_atividade(self, atividade_id: str, aluno_id: str) -> int:
        """Reseta as extrações de questões de um aluno em uma atividade específica"""
        rows = self._select_rows(
            "documentos",
            filters={"atividade_id": atividade_id, "aluno_id": aluno_id, "tipo": "extracao_questoes"},
            columns=["id", "tipo"],
        )

        count = 0
        for row in rows:
            if row.get("tipo") == "extracao_questoes":
                if self.deletar_documento(row["id"]):
                    count += 1

        return count

    def renomear_documento(self, documento_id: str, novo_nome: str) -> Optional[Documento]:
        """Renomeia um documento"""
        doc = self.get_documento(documento_id)
        if not doc:
            return None
        
        # Renomear arquivo físico
        arquivo_atual = Path(doc.caminho_arquivo)
        if arquivo_atual.exists():
            novo_caminho = arquivo_atual.parent / novo_nome
            arquivo_atual.rename(novo_caminho)
            
            # Atualizar banco
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('''
                UPDATE documentos 
                SET nome_arquivo = ?, caminho_arquivo = ?, atualizado_em = ?
                WHERE id = ?
            ''', (novo_nome, str(novo_caminho), datetime.now().isoformat(), documento_id))
            conn.commit()
            conn.close()
        
        return self.get_documento(documento_id)
    
    # ============================================================
    # STATUS E VERIFICAÇÕES
    # ============================================================
    
    def get_status_atividade(self, atividade_id: str) -> Dict[str, Any]:
        """
        Retorna status completo de uma atividade.
        Inclui documentos existentes, faltantes, e status por aluno.
        """
        atividade = self.get_atividade(atividade_id)
        if not atividade:
            return {"erro": "Atividade não encontrada"}
        
        turma = self.get_turma(atividade.turma_id)
        alunos = self.listar_alunos(turma.id)
        documentos = self.listar_documentos(atividade_id)
        
        # Documentos base
        docs_base = [d for d in documentos if d.is_documento_base]
        docs_base_detalhes: Dict[str, List[Dict[str, Any]]] = {}
        for doc in docs_base:
            tipo = doc.tipo.value
            if tipo not in docs_base_detalhes:
                docs_base_detalhes[tipo] = []
            docs_base_detalhes[tipo].append({
                "id": doc.id,
                "nome_arquivo": doc.nome_arquivo,
                "criado_em": doc.criado_em.isoformat(),
                "criado_por": doc.criado_por
            })
        tipos_base_existentes = [TipoDocumento(tipo) for tipo in docs_base_detalhes.keys()]
        
        docs_base_faltando = []
        for tipo in [TipoDocumento.ENUNCIADO, TipoDocumento.GABARITO]:
            if tipo not in tipos_base_existentes:
                docs_base_faltando.append(tipo.value)
        
        # Status por aluno
        alunos_status = []
        for aluno in alunos:
            docs_aluno = [d for d in documentos if d.aluno_id == aluno.id]
            tipos_aluno = [d.tipo for d in docs_aluno]
            
            tem_prova = TipoDocumento.PROVA_RESPONDIDA in tipos_aluno
            tem_correcao = TipoDocumento.CORRECAO in tipos_aluno
            tem_relatorio = TipoDocumento.RELATORIO_FINAL in tipos_aluno
            
            alunos_status.append({
                "aluno_id": aluno.id,
                "aluno_nome": aluno.nome,
                "tem_prova": tem_prova,
                "tem_correcao": tem_correcao,
                "tem_relatorio": tem_relatorio,
                "documentos": len(docs_aluno)
            })
        
        return {
            "atividade": atividade.to_dict(),
            "documentos_base": {
                "existentes": [tipo.value for tipo in tipos_base_existentes],
                "faltando": docs_base_faltando,
                "aviso": "Falta gabarito para poder corrigir" if TipoDocumento.GABARITO.value in docs_base_faltando else None,
                "detalhes": docs_base_detalhes
            },
            "alunos": {
                "total": len(alunos),
                "com_prova": sum(1 for a in alunos_status if a["tem_prova"]),
                "corrigidos": sum(1 for a in alunos_status if a["tem_correcao"]),
                "detalhes": alunos_status
            }
        }
    
    def verificar_pode_processar(self, atividade_id: str, aluno_id: str, 
                                  tipo_alvo: TipoDocumento) -> Dict[str, Any]:
        """
        Verifica se um tipo de documento pode ser gerado.
        Retorna o que está faltando.
        """
        documentos = self.listar_documentos(atividade_id, aluno_id)
        tipos_existentes = [d.tipo for d in documentos]
        
        return verificar_dependencias(tipo_alvo, tipos_existentes)
    
    # ============================================================
    # NAVEGAÇÃO HIERÁRQUICA
    # ============================================================

    def get_estatisticas_gerais_fast(self) -> Dict[str, Any]:
        """Returns dashboard statistics with batched reads instead of N+1 loops."""
        started_at = time.perf_counter()

        total_materias = self._count_rows("materias")
        total_turmas = self._count_rows("turmas")
        total_alunos = self._count_rows("alunos")

        atividades_rows = self._select_rows("atividades", columns=["id"])
        atividade_ids = [row["id"] for row in atividades_rows]
        documentos_rows = (
            self._select_rows(
                "documentos",
                filters={"atividade_id": atividade_ids},
                columns=["atividade_id", "tipo"],
            )
            if atividade_ids
            else []
        )

        tipos_por_atividade: Dict[str, set] = defaultdict(set)
        for row in documentos_rows:
            tipos_por_atividade[row["atividade_id"]].add(row["tipo"])

        gabarito_tipo = TipoDocumento.GABARITO.value
        atividades_sem_gabarito = sum(
            1
            for atividade_id in atividade_ids
            if gabarito_tipo not in tipos_por_atividade.get(atividade_id, set())
        )

        payload = {
            "total_materias": total_materias,
            "total_turmas": total_turmas,
            "total_alunos": total_alunos,
            "total_atividades": len(atividade_ids),
            "total_documentos": len(documentos_rows),
            "alertas": {
                "atividades_sem_gabarito": atividades_sem_gabarito
            }
        }
        self._log_hot_endpoint_profile(
            "/api/estatisticas",
            started_at,
            {
                "materias": total_materias,
                "turmas": total_turmas,
                "alunos": total_alunos,
                "atividades": len(atividades_rows),
                "documentos": len(documentos_rows),
            },
            {
                "total_atividades": payload["total_atividades"],
                "total_documentos": payload["total_documentos"],
            },
        )
        return payload

    def get_arvore_navegacao_fast(self) -> Dict[str, Any]:
        """Returns the navigation tree with batched reads and merged duplicate matérias."""
        started_at = time.perf_counter()

        materias_rows = self._select_rows(
            "materias",
            order_by="nome",
            columns=["id", "nome"],
        )
        materia_ids = [row["id"] for row in materias_rows]

        turmas_rows = (
            self._select_rows(
                "turmas",
                filters={"materia_id": materia_ids},
                order_by="nome",
                columns=["id", "materia_id", "nome", "ano_letivo"],
            )
            if materia_ids
            else []
        )
        turma_ids = [row["id"] for row in turmas_rows]

        atividades_rows = (
            self._select_rows(
                "atividades",
                filters={"turma_id": turma_ids},
                order_by="nome",
                columns=["id", "turma_id", "nome", "tipo"],
            )
            if turma_ids
            else []
        )
        atividade_ids = [row["id"] for row in atividades_rows]

        documentos_rows = (
            self._select_rows(
                "documentos",
                filters={"atividade_id": atividade_ids},
                columns=["atividade_id"],
            )
            if atividade_ids
            else []
        )
        vinculos_rows = (
            self._select_rows(
                "alunos_turmas",
                filters={"turma_id": turma_ids, "ativo": True},
                columns=["turma_id", "aluno_id"],
            )
            if turma_ids
            else []
        )

        total_documentos_por_atividade: Dict[str, int] = defaultdict(int)
        for row in documentos_rows:
            total_documentos_por_atividade[row["atividade_id"]] += 1

        total_alunos_por_turma: Dict[str, set] = defaultdict(set)
        for row in vinculos_rows:
            total_alunos_por_turma[row["turma_id"]].add(row["aluno_id"])

        atividades_por_turma: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for atividade in atividades_rows:
            atividades_por_turma[atividade["turma_id"]].append({
                "id": atividade["id"],
                "nome": atividade["nome"],
                "tipo": atividade.get("tipo"),
                "total_documentos": total_documentos_por_atividade.get(atividade["id"], 0),
            })

        turmas_por_materia: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for turma in turmas_rows:
            turmas_por_materia[turma["materia_id"]].append({
                "id": turma["id"],
                "nome": turma["nome"],
                "ano_letivo": turma.get("ano_letivo"),
                "total_alunos": len(total_alunos_por_turma.get(turma["id"], set())),
                "atividades": atividades_por_turma.get(turma["id"], []),
            })

        materias_por_nome: Dict[str, Dict[str, Any]] = {}
        for materia in materias_rows:
            entry = materias_por_nome.get(materia["nome"])
            if not entry:
                entry = {
                    "id": materia["id"],
                    "nome": materia["nome"],
                    "turmas": [],
                }
                materias_por_nome[materia["nome"]] = entry
            entry["turmas"].extend(turmas_por_materia.get(materia["id"], []))

        payload = {"materias": list(materias_por_nome.values())}
        self._log_hot_endpoint_profile(
            "/api/navegacao/arvore",
            started_at,
            {
                "materias": len(materias_rows),
                "turmas": len(turmas_rows),
                "atividades": len(atividades_rows),
                "documentos": len(documentos_rows),
                "alunos_turmas": len(vinculos_rows),
            },
            {
                "materias": len(payload["materias"]),
            },
        )
        return payload

    def listar_documentos_com_contexto_fast(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Returns /api/documentos/todos using batched reads and context maps."""
        started_at = time.perf_counter()

        filters = filters or {}
        materia_ids = filters.get("materia_ids") or None
        turma_ids = filters.get("turma_ids") or None
        atividade_ids_filter = filters.get("atividade_ids") or None
        aluno_ids = filters.get("aluno_ids") or None
        tipos = filters.get("tipos") or None

        turma_scope_rows: List[Dict[str, Any]] = []
        turma_scope_ids: List[str] = []
        if materia_ids or turma_ids or not atividade_ids_filter:
            turma_filters: Dict[str, Any] = {}
            if materia_ids:
                turma_filters["materia_id"] = materia_ids
            if turma_ids:
                turma_filters["id"] = turma_ids

            turma_scope_rows = self._select_rows(
                "turmas",
                filters=turma_filters or None,
                order_by="nome",
                columns=["id", "materia_id", "nome"],
            )
            turma_scope_ids = [row["id"] for row in turma_scope_rows]

            if (materia_ids or turma_ids) and not turma_scope_ids:
                self._log_hot_endpoint_profile(
                    "/api/documentos/todos",
                    started_at,
                    {
                        "materias": 0,
                        "turmas": 0,
                        "atividades": 0,
                        "documentos": 0,
                        "alunos": 0,
                    },
                    {"documentos": 0},
                )
                return []

        atividade_filters: Dict[str, Any] = {}
        if atividade_ids_filter:
            atividade_filters["id"] = atividade_ids_filter
        if turma_scope_ids:
            atividade_filters["turma_id"] = turma_scope_ids
        elif materia_ids or turma_ids or not atividade_ids_filter:
            self._log_hot_endpoint_profile(
                "/api/documentos/todos",
                started_at,
                {
                    "materias": 0,
                    "turmas": len(turma_scope_rows),
                    "atividades": 0,
                    "documentos": 0,
                    "alunos": 0,
                },
                {"documentos": 0},
            )
            return []

        atividades_rows = self._select_rows(
            "atividades",
            filters=atividade_filters or None,
            order_by="nome",
            columns=["id", "turma_id", "nome"],
        )
        atividade_ids = [row["id"] for row in atividades_rows]
        if not atividade_ids:
            self._log_hot_endpoint_profile(
                "/api/documentos/todos",
                started_at,
                {
                    "materias": 0,
                    "turmas": len(turma_scope_rows),
                    "atividades": 0,
                    "documentos": 0,
                    "alunos": 0,
                },
                {"documentos": 0},
            )
            return []

        documentos_filters: Dict[str, Any] = {"atividade_id": atividade_ids}
        if tipos:
            documentos_filters["tipo"] = tipos
        documentos_rows = self._select_rows(
            "documentos",
            filters=documentos_filters,
            order_by="criado_em",
            order_desc=True,
            columns=["id", "nome_arquivo", "tipo", "atividade_id", "aluno_id", "criado_em"],
        )

        if aluno_ids:
            aluno_ids_set = set(aluno_ids)
            documentos_rows = [
                row for row in documentos_rows
                if row.get("aluno_id") is None or row.get("aluno_id") in aluno_ids_set
            ]

        turma_ids_relevantes = sorted({row["turma_id"] for row in atividades_rows})
        turmas_rows = turma_scope_rows
        if not turmas_rows:
            turmas_rows = self._select_rows(
                "turmas",
                filters={"id": turma_ids_relevantes},
                order_by="nome",
                columns=["id", "materia_id", "nome"],
            )
        else:
            turmas_rows = [row for row in turmas_rows if row["id"] in turma_ids_relevantes]

        materia_ids_relevantes = sorted({row["materia_id"] for row in turmas_rows})
        materias_rows = (
            self._select_rows(
                "materias",
                filters={"id": materia_ids_relevantes},
                order_by="nome",
                columns=["id", "nome"],
            )
            if materia_ids_relevantes
            else []
        )

        aluno_ids_relevantes = sorted({
            row["aluno_id"] for row in documentos_rows
            if row.get("aluno_id")
        })
        alunos_rows = (
            self._select_rows(
                "alunos",
                filters={"id": aluno_ids_relevantes},
                order_by="nome",
                columns=["id", "nome"],
            )
            if aluno_ids_relevantes
            else []
        )
        aluno_nome_por_id = {row["id"]: row["nome"] for row in alunos_rows}

        atividades_por_turma: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for atividade in atividades_rows:
            atividades_por_turma[atividade["turma_id"]].append(atividade)

        turmas_por_materia: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for turma in turmas_rows:
            turmas_por_materia[turma["materia_id"]].append(turma)

        documentos_por_atividade: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for documento in documentos_rows:
            documentos_por_atividade[documento["atividade_id"]].append(documento)

        documentos: List[Dict[str, Any]] = []
        for materia in materias_rows:
            for turma in turmas_por_materia.get(materia["id"], []):
                for atividade in atividades_por_turma.get(turma["id"], []):
                    for documento in documentos_por_atividade.get(atividade["id"], []):
                        documentos.append({
                            "id": documento["id"],
                            "nome_arquivo": documento.get("nome_arquivo"),
                            "tipo": documento["tipo"],
                            "materia_id": materia["id"],
                            "materia_nome": materia["nome"],
                            "turma_id": turma["id"],
                            "turma_nome": turma["nome"],
                            "atividade_id": atividade["id"],
                            "atividade_nome": atividade["nome"],
                            "aluno_id": documento.get("aluno_id"),
                            "aluno_nome": aluno_nome_por_id.get(documento.get("aluno_id")),
                            "criado_em": documento.get("criado_em"),
                        })

        self._log_hot_endpoint_profile(
            "/api/documentos/todos",
            started_at,
            {
                "materias": len(materias_rows),
                "turmas": len(turmas_rows),
                "atividades": len(atividades_rows),
                "documentos": len(documentos_rows),
                "alunos": len(alunos_rows),
            },
            {"documentos": len(documentos)},
        )
        return documentos

    def get_arvore_navegacao(self) -> Dict[str, Any]:
        """
        Retorna árvore completa para navegação.
        Estrutura: Matérias → Turmas → Atividades
        Deduplica matérias por nome, mesclando turmas das duplicadas.
        """
        return self.get_arvore_navegacao_fast()


# ============================================================
# INSTÂNCIA GLOBAL
# ============================================================

storage = StorageManager()

# Alias para compatibilidade (remover após atualizar todos os imports)
StorageManagerV2 = StorageManager
storage_v2 = storage
