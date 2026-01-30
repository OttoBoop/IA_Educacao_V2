"""
PROVA AI - Sistema de Armazenamento Unificado

Gerencia:
1. Banco de dados SQLite com estrutura hierárquica
2. Sistema de arquivos organizado por Matéria/Turma/Atividade
3. Metadados de documentos e processamento
4. Verificação de dependências

NOTA: Este arquivo é a unificação de storage.py e storage_v2.py
O antigo storage.py (legado) foi removido em 2026-01-30.
"""

import os
import sqlite3
import hashlib
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from models import (
    Materia, Turma, Aluno, AlunoTurma, Atividade, Documento, Prompt, ResultadoAluno,
    TipoDocumento, StatusProcessamento, NivelEnsino,
    verificar_dependencias, DEPENDENCIAS_DOCUMENTOS
)

# Import Supabase storage (para persistência em cloud)
try:
    from supabase_storage import supabase_storage
    SUPABASE_AVAILABLE = supabase_storage.enabled
except ImportError:
    supabase_storage = None
    SUPABASE_AVAILABLE = False


# Diretório base para paths absolutos (compatível com Render)
BASE_DIR = Path(__file__).parent


class StorageManager:
    """
    Gerenciador de armazenamento unificado.

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
        └── database.db                      # SQLite
    """
    
    def __init__(self, base_path: str = None):
        # Usar path absoluto baseado em __file__ para compatibilidade com Render
        if base_path is None:
            base_path = str(BASE_DIR / "data")
        self.base_path = Path(base_path)
        self.arquivos_path = self.base_path / "arquivos"
        self.db_path = self.base_path / "database.db"
        
        self._setup_directories()
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
        
        conn.commit()
        conn.close()
    
    # ============================================================
    # UTILITÁRIOS
    # ============================================================
    
    def _generate_id(self, *args) -> str:
        """Gera ID único baseado nos argumentos + timestamp"""
        content = "_".join(str(a) for a in args) + str(datetime.now().timestamp())
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
    
    # ============================================================
    # CRUD: MATÉRIAS
    # ============================================================
    
    def criar_materia(self, nome: str, descricao: str = None, nivel: NivelEnsino = NivelEnsino.OUTRO) -> Materia:
        """Cria uma nova matéria"""
        materia = Materia(
            id=self._generate_id("materia", nome),
            nome=nome,
            descricao=descricao,
            nivel=nivel
        )
        
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
        updates = []
        valores = []
        
        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                if campo == 'nivel' and isinstance(valor, NivelEnsino):
                    valor = valor.value
                elif campo == 'metadata':
                    valor = json.dumps(valor)
                updates.append(f"{campo} = ?")
                valores.append(valor)
        
        if not updates:
            return materia
        
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
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM materias WHERE id = ?', (materia_id,))
        affected = c.rowcount
        conn.commit()
        conn.close()
        
        # Remover diretório
        dir_path = self.arquivos_path / materia_id
        if dir_path.exists():
            shutil.rmtree(dir_path)
        
        return affected > 0
    
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
        updates = []
        valores = []
        
        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                if campo == 'metadata':
                    valor = json.dumps(valor)
                updates.append(f"{campo} = ?")
                valores.append(valor)
        
        if not updates:
            return aluno
        
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
        """Retorna todas as turmas de um aluno, com info da matéria"""
        conn = self._get_connection()
        c = conn.cursor()
        
        query = '''
            SELECT t.*, m.nome as materia_nome, at.observacoes, at.data_entrada
            FROM turmas t
            JOIN alunos_turmas at ON t.id = at.turma_id
            JOIN materias m ON t.materia_id = m.id
            WHERE at.aluno_id = ?
        '''
        if apenas_ativas:
            query += ' AND at.ativo = 1'
        query += ' ORDER BY m.nome, t.ano_letivo DESC'
        
        c.execute(query, (aluno_id,))
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
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
        if aluno_id:
            aluno = self.get_aluno(aluno_id)
            if not aluno:
                raise ValueError(f"Aluno não encontrado: {aluno_id}")
        
        # Info do arquivo
        arquivo_path = Path(arquivo_origem)
        nome_original = arquivo_path.name
        extensao = arquivo_path.suffix
        tamanho = arquivo_path.stat().st_size if arquivo_path.exists() else 0
        
        # Gerar nome único para o arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"{tipo.value}_{timestamp}{extensao}"
        
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
            nome_arquivo=nome_original,
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
        
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO documentos (
                id, tipo, atividade_id, aluno_id, nome_arquivo, caminho_arquivo, extensao,
                tamanho_bytes, ia_provider, ia_modelo, prompt_usado, prompt_versao,
                tokens_usados, tempo_processamento_ms, status, criado_em, atualizado_em,
                criado_por, versao, documento_origem_id, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            documento.id, documento.tipo.value, documento.atividade_id, documento.aluno_id,
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

        # Upload para Supabase (persistência em cloud)
        if SUPABASE_AVAILABLE and supabase_storage:
            remote_path = str(caminho_relativo).replace("\\", "/")
            success, msg = supabase_storage.upload(str(destino), remote_path)
            if success:
                print(f"[Supabase] Upload OK: {remote_path}")
            else:
                print(f"[Supabase] Aviso: {msg}")

        return documento
    
    def get_documento(self, documento_id: str) -> Optional[Documento]:
        """Busca documento por ID"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM documentos WHERE id = ?', (documento_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return None

        return Documento.from_dict(dict(row))

    def resolver_caminho_documento(self, documento: Documento) -> Path:
        """
        Resolve o caminho absoluto de um documento.

        SEMPRE usa Supabase como fonte primária.
        Local é apenas cache/fallback para dev.
        """
        import sys
        import logging
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

        # SEMPRE tentar Supabase primeiro
        if SUPABASE_AVAILABLE and supabase_storage and supabase_storage.enabled:
            logger.info(f"[resolver_caminho] Tentando Supabase...")

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

        # Fallback: verificar local (para dev sem Supabase)
        if local_path.exists():
            logger.info(f"[resolver_caminho] Usando cache local: {local_path}")
            return local_path

        logger.error(f"[resolver_caminho] ERRO: Arquivo não encontrado em lugar nenhum!")
        return local_path
    
    def listar_documentos(self, atividade_id: str, aluno_id: str = None, 
                          tipo: TipoDocumento = None) -> List[Documento]:
        """Lista documentos com filtros"""
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

            # Remover do Supabase também
            if SUPABASE_AVAILABLE and supabase_storage:
                remote_path = str(doc.caminho_arquivo).replace("\\", "/")
                if remote_path.startswith('data/'):
                    remote_path = remote_path[5:]
                success, msg = supabase_storage.delete(remote_path)
                if success:
                    print(f"[Supabase] Deletado: {remote_path}")

        # Remover do banco
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM documentos WHERE id = ?', (documento_id,))
        conn.commit()
        conn.close()

        return True

    def deletar_documentos_aluno_atividade(self, atividade_id: str, aluno_id: str) -> int:
        """Deleta todos os documentos de um aluno em uma atividade específica"""
        # Buscar documentos do aluno nesta atividade
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, caminho_arquivo FROM documentos
            WHERE atividade_id = ? AND aluno_id = ?
        ''', (atividade_id, aluno_id))
        rows = c.fetchall()

        count = 0
        for row in rows:
            # Remover arquivo físico
            if row['caminho_arquivo']:
                arquivo = Path(row['caminho_arquivo'])
                if arquivo.exists():
                    arquivo.unlink()
            count += 1

        # Remover do banco
        c.execute('DELETE FROM documentos WHERE atividade_id = ? AND aluno_id = ?', (atividade_id, aluno_id))
        conn.commit()
        conn.close()

        return count

    def excluir_documentos_ai_aluno_atividade(self, atividade_id: str, aluno_id: str) -> int:
        """Deleta apenas os documentos gerados por IA de um aluno em uma atividade específica"""
        ai_types = ['extracao_questoes', 'extracao_gabarito', 'extracao_respostas', 'correcao', 'analise_habilidades', 'relatorio_final']
        # Buscar documentos do aluno nesta atividade que são AI-generated
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, caminho_arquivo FROM documentos
            WHERE atividade_id = ? AND aluno_id = ? AND (ia_provider IS NOT NULL OR tipo IN ({placeholders}))
        '''.format(placeholders=','.join(['?']*len(ai_types))), (atividade_id, aluno_id) + tuple(ai_types))
        rows = c.fetchall()

        count = 0
        for row in rows:
            # Remover arquivo físico
            if row['caminho_arquivo']:
                arquivo = Path(row['caminho_arquivo'])
                if arquivo.exists():
                    arquivo.unlink()
            count += 1

        # Remover do banco
        c.execute('DELETE FROM documentos WHERE atividade_id = ? AND aluno_id = ? AND (ia_provider IS NOT NULL OR tipo IN ({placeholders}))'.format(placeholders=','.join(['?']*len(ai_types))), (atividade_id, aluno_id) + tuple(ai_types))
        conn.commit()
        conn.close()

        return count

    def resetar_extracoes_questoes_aluno_atividade(self, atividade_id: str, aluno_id: str) -> int:
        """Reseta as extrações de questões de um aluno em uma atividade específica"""
        # Buscar documentos do aluno nesta atividade que são extrações de questões
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, caminho_arquivo FROM documentos
            WHERE atividade_id = ? AND aluno_id = ? AND tipo = ?
        ''', (atividade_id, aluno_id, 'extracao_questoes'))
        rows = c.fetchall()

        count = 0
        for row in rows:
            # Remover arquivo físico
            if row['caminho_arquivo']:
                arquivo = Path(row['caminho_arquivo'])
                if arquivo.exists():
                    arquivo.unlink()
            count += 1

        # Remover do banco
        c.execute('DELETE FROM documentos WHERE atividade_id = ? AND aluno_id = ? AND tipo = ?', (atividade_id, aluno_id, 'extracao_questoes'))
        conn.commit()
        conn.close()

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
    
    def get_arvore_navegacao(self) -> Dict[str, Any]:
        """
        Retorna árvore completa para navegação.
        Estrutura: Matérias → Turmas → Atividades
        """
        arvore = []
        
        for materia in self.listar_materias():
            turmas_data = []
            
            for turma in self.listar_turmas(materia.id):
                atividades_data = []
                
                for atividade in self.listar_atividades(turma.id):
                    docs = self.listar_documentos(atividade.id)
                    atividades_data.append({
                        "id": atividade.id,
                        "nome": atividade.nome,
                        "tipo": atividade.tipo,
                        "total_documentos": len(docs)
                    })
                
                turmas_data.append({
                    "id": turma.id,
                    "nome": turma.nome,
                    "ano_letivo": turma.ano_letivo,
                    "total_alunos": len(self.listar_alunos(turma.id)),
                    "atividades": atividades_data
                })
            
            arvore.append({
                "id": materia.id,
                "nome": materia.nome,
                "turmas": turmas_data
            })
        
        return {"materias": arvore}


# ============================================================
# INSTÂNCIA GLOBAL
# ============================================================

storage = StorageManager()

# Alias para compatibilidade (remover após atualizar todos os imports)
StorageManagerV2 = StorageManager
storage_v2 = storage